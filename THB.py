# THB.py
# Skeletorfw
# 23/04/17
# Version 0.1
#
# Python 3.4.1
#
# Bot to pull askreddit threads and trend popularity over time
import praw
import logging
import time
import os

# Set up logging
# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create logfile handler
handler = logging.FileHandler('THB.out')
handler.setLevel(logging.DEBUG)

# Create formatter and add to handler
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(handler)

reddit = praw.Reddit('bot1')
subreddit = reddit.subreddit("AskReddit")
threads_to_pull = 20


def get_newthreads(threads=20):
    logger.debug("Getting newest {0} submissions to /r/AskReddit".format(threads))
    for submission in subreddit.new(limit=threads):
        logger.debug("Found thread ID {0}".format(submission.id))
        # print("Title: {0}".format(submission.title))
        # print("Score: {0}".format(submission.score))
        # print("Comments: {0}".format(submission.num_comments))



def logtest():
    logger.debug("DEBUG TEST")
    logger.info("INFO TEST")
    logger.warning("WARNING TEST")
    logger.error("ERROR TEST")
    logger.critical("CRITICAL TEST")
    logger.fatal("FATAL TEST")
