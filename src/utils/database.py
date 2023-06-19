import pyodbc
import json
import pandas as pd
import os

import firebase_admin
from firebase_admin import credentials, firestore, storage
from dotenv import load_dotenv

class Warehouse:

    def __init__(self, trusted=True) -> None:
        self.trusted = trusted
        self.server = "azr-warehouse-1"

    def query_all_from_table(self, database, table):
        """
        Queries all variables from the given database and table

        Parameters
        ----------
        database : str
            name of the database as it appears in the Azure data warehouse
        table : str
            name of the table within the given database

        Returns
        -------
        data : DataFrame
            all available data from table
        """

        # set up connection
        driver = '{SQL Server}'
        cnxn = pyodbc.connect('DRIVER=' + driver + ';SERVER=' + self.server + ';DATABASE=' + database + ';Trusted_Connection=yes;')

        # execute SQL query and save data to DataFrame
        query = f"SELECT * FROM {table}"
        data = pd.read_sql(query, cnxn)

        # close connection
        cnxn.close()

        return data
    
    def get_all_tables(self, database, schema=None):
        """
        Finds all tables in the given database and schema

        Parameters
        ----------
        database : str
            Name of the database as it appears in the Azure data warehouse
        schema : str, optional
            Name of the schema within the given database, defaults to None (all schemas)

        Returns
        -------
        tables : list
            List of table names found in the specified database and schema
        """

        # set up connection
        driver = '{SQL Server}'
        cnxn = pyodbc.connect('DRIVER=' + driver + ';SERVER=' + self.server + ';DATABASE=' + database + ';Trusted_Connection=yes;')

        # prepare the query to retrieve table names
        query = """
            SELECT TABLE_SCHEMA, TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_TYPE = 'BASE TABLE'
        """

        # add schema condition if provided
        if schema:
            query += f"AND TABLE_SCHEMA = '{schema}'"

        # execute SQL query and retrieve table names
        cursor = cnxn.cursor()
        cursor.execute(query)
        tables = [(row.TABLE_SCHEMA, row.TABLE_NAME) for row in cursor.fetchall()]

        # close connection
        cnxn.close()

        return tables
    
class FireBase:

    def __init__(self, project_id) -> None:
        # load credentials
        load_dotenv()
        cred = credentials.Certificate(json.loads(os.getenv("FIREBASE_CREDS")))
        # initialize app
        app = firebase_admin.initialize_app(cred, 
            {
            "databaseURL": f"https://{project_id}.firebaseio.com/",
            "storageBucket": f"{project_id}.appspot.com",
        })
        # create firebase instances
        self.database = firestore.client(app=app)
        self.bucket = storage.bucket(app=app)

    def add_data(self, data, collection):
        """
        Adds data as a document to the Firebase collection
        Some help from here: https://code.luasoftware.com/tutorials/pandas/firestore-to-pandas-dataframe/

        Parameters
        ----------
        data : list of dict or DataFrame
            from the get_data method
        collection : str
            name of Firestore collection to add to
        
        Returns
        -------
        <exit_code> : int
            0 for success, 1 for error
        <add_status> : str
            status message regarding the upload to Firebase
        """
        if isinstance(data, list):
            pass # correct form of data
        elif isinstance(data, pd.DataFrame):
            # convert to list of dict since firestore wants this
            data = data.to_dict(orient="records")
        
        try:
            list(map(lambda x: self.database.collection(collection).add(x), data))
            return 0, f"Successfully added {len(data)} entries"
        except Exception as e:
            return 1, e
        
    def delete_collection(self, collection):
        """
        Deletes all documents within the class collection

        Parameters
        ----------
        collection : str
            name of Firestore collection to add to
        
        Returns
        -------
        <exit_code> : int
            0 for success, 1 for error
        <message> : str
            success or failure message
        """
        # pull all documents from firebase
        docs = self.database.collection(collection).stream()

        docs_deleted = 0
        sub_docs_deleted = 0
        for doc in docs:
            # Delete the subcollections within the document (if any)
            subcollections = doc.reference.collections()
            for subcollection in subcollections:
                for sub_doc in subcollection.stream():
                    # Delete all documents in the subcollection
                    sub_doc.reference.delete()
                    sub_docs_deleted += 1

                # Delete the subcollection itself
                subcollection_ref = doc.reference.collection(subcollection.id)
                if subcollection_ref.get():
                    subcollection_ref.delete()

            # Delete the main document
            doc.reference.delete()
            docs_deleted += 1

        return 0, f"Successfully deleted {docs_deleted} documents and {sub_docs_deleted} subcollection documents"
    
    def get_data(self, collection):
        """
        Gets data from Firestore and formats as DataFrame

        Parameters
        ----------
        collection : str
            name of Firestore collection to add to

        Returns
        -------
        <data> : DataFrame
            available data from Firestore
        """
        docs = self.database.collection(collection).stream()
        firestore_projects = list(map(lambda x: {**x.to_dict(), 'id': x.id}, docs))
        
        return pd.DataFrame.from_records(firestore_projects)
    
    def update_values(self, collection, doc_id, new_data):
        """
        Updates a given document

        Parameters
        ----------
        collection : str
            name of Firestore collection to add to
        doc_id : str
            unique document identifier
        new_data : dict
            keys are variables and values are the updates
        """
        doc_ref = self.database.document(f"{collection}/{doc_id}")
        try:
            doc_ref.update(new_data)
        except ValueError as e:
            print(e)
