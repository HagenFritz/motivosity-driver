# Motivosity Driver
_Scrape data from and drive the Motivosity platform_

The code in this repository allows for:
* Scrape data from recognitions
* Systematically "Like" 👍 posts

# How to Use this Repository
Regardless of your use case, the setup is similar:
1. Create virtual environment and install the requirements:
```bash
pip install -r requirements.txt
```
2. Create a `.env` ⚙️ file and include the following variables:
```env
USERNAME=<azure username without domain>
PASSWORD=<azure password>
```

## Scrape Recognition Data
By default, the program will _always_ scrape the latest updates and save them. To pull Motivosity updates, simply run the `main.py` script from the command line without arguments:
```python
python main.py
```
Data will be saved to the `/data/raw/` directory with the timestamp (at completion of the scrape) in the filename.

## Like Most Recent Posts
To like the most recent posts, simple include the `-like` flag when running the main script:
```python
python main.py -like
```
The script will attempt to like all posts and skip over posts that have already been liked. By default, the logging information will be streamed but you can find the log file in `/src/utils/`
