#!/usr/bin/env python3
# ---
# Project Name: Motivosity Driver
# Date Created: 06/19/2023
# Author: Hagen E Fritz
# Description: Engage with Motivosity
# Last Edited: 06/25/2023
# ---

import os
import argparse
import pathlib
from datetime import datetime
from time import sleep

import pandas as pd
from bs4 import BeautifulSoup
from dotenv import load_dotenv
load_dotenv()

from utils import logger
from automate import webpage

PATH_TO_TOP = f"{pathlib.Path(__file__).resolve().parent.parent}"
LOG = logger.setup("log", level="debug", stream=True)

def main(like_posts):
    """
    Scrape and drive Motivosity

    Parameters
    ----------
    like_posts : boolean
        whether to like all available posts
    """
    LOG.info(f"Started at {datetime.now()}")
    # Navigate to Motivosity
    nav = webpage.Interact()
    nav.navigate_to_webpage("https://ro.motivosity.com/mv/index.html#/home")
    # Login
    LOG.debug("entering username")
    nav.enter_text(f"{os.getenv('USERNAME')}@r-o.com","input","name","loginfmt") # username
    nav.simple_click_button("input","type","submit")
    LOG.debug("entering password")
    nav.enter_text(os.getenv("PASSWORD"),"input","name","passwd") # password
    nav.simple_click_button("input","type","submit")
    nav.simple_click_button("input","type","submit") # stay signed in dialog
    
    # Scrape
    # ------
    sleep(3) # explicit wait for page to load
    soup = BeautifulSoup(nav.driver.page_source, 'html.parser')
    # Find all updates, loop through, and save data
    update_cards = soup.find_all('div', class_='feed')
    update_data = {
        "Update": [],
        "People": [],
        "Description": []
    }
    for i, update_card in enumerate(update_cards):
        LOG.info(f"Card {i+1}")
        update_data["Update"].append(i+1)
        # names
        names = [a.text.strip() for a in update_card.find_all('a', class_='mv-body-default-medium feedInfo__subject feedInfo__link ng-star-inserted')]
        if len(names) == 0:
            names = [update_card.find('a', class_="mv-body-default-bold feedInfo__subject feedInfo__link ng-star-inserted").text.strip()]

        LOG.info(f"{len(names)} people recognized: {names}")
        update_data["People"].append(names)
        # description
        desc = update_card.find("p").text.strip()
        LOG.info(f"Description: {desc}")
        update_data["Description"].append(desc)
        if like_posts:
            # Find like button
            like_button = update_card.find("button", attrs={"containerclass":"likeTypeList"})
            # Class comes as list of str so combine into single str 
            like_button_class = ' '.join(like_button["class"])
            # like icon (of any type) will be present if user has already liked a post
            like_icon = like_button.find("img", alt="Like button icon")
            
            if like_icon is None:
                # element is None because it doesn't exist
                LOG.warning("You have NOT liked the post")
                nav.java_click_button("button", "class", like_button_class)
                LOG.info("Successfully liked the post")
            else:
                # element exists so user liked (of any type) already
                LOG.warning("You have already liked this post")
                
            sleep(1) # explicit wait so page can acknowledge like action

    # Save latest scrape
    pd.DataFrame(data=update_data).to_csv(f"{PATH_TO_TOP}/data/raw/top_updates-{datetime.now().strftime('%Y_%m_%d-%H_%M_%S')}.csv")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", help="integer argument to pass", default=0, type=int)
    parser.add_argument("-like", help="boolean argument to pass", action="store_true")
    args = parser.parse_args()

    main(like_posts=args.like)