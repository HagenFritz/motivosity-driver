import pywinauto
from pywinauto.findwindows import ElementNotFoundError, ElementAmbiguousError

import time

def upload_photo(path_and_file):
    """
    Uses pywinauto to find and upload the photo
    
    Parameters
    ----------
    path_and_file : str
        name of full-path file to upload
    """
    time.sleep(1)
    windowHandle = pywinauto.findwindows.find_windows(title=u'Open', class_name='#32770')[0]
    app = pywinauto.application.Application(backend="win32").connect(handle=windowHandle)
    window = app.window(title=u"Open")
    window.FileNameEdit.set_edit_text(f"{path_and_file}")
    for _ in range(2):
        try:
            window.child_window(title="&Open", class_name="Button").click()
            time.sleep(0.5)
        except ElementNotFoundError:
            # window closed
            break

    time.sleep(1)

def close_file_explorer_dialog():
    """
    Closes the currently open file explorer dialog
    """
    windowHandle = pywinauto.findwindows.find_windows(title=u'Open', class_name='#32770')[0]
    app = pywinauto.application.Application(backend="win32").connect(handle=windowHandle)

    try:
        error_window = app.window(title=u"Open", found_index=0)
        error_window.child_window(title="OK", class_name="Button").click()
    except Exception as e:
        pass

    time.sleep(1)

    try:
        original_window = app.window(title=u"Open", found_index=0)
        original_window.child_window(title="Cancel", class_name="Button").click()
    except Exception as e:
        pass

    time.sleep(2)
