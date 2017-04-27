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
import csv
import pprint

# Set up logging
# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create logfile handler
handler = logging.FileHandler('log/THB.out')
handler.setLevel(logging.DEBUG)     # File logging level

# Create formatter and add to handler
formatter = logging.Formatter('%(asctime)s - %(levelname)8s - %(funcName)s - %(message)s')
handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(handler)

reddit = praw.Reddit('bot1')
subreddit = reddit.subreddit("AskReddit")
threads_to_pull = 20        # Could define dynamically


def readfiles():
    """
    Read the current working file and return as a dict
    """
    watchedthreads = {}
    try:
        with open("data/watched.csv") as watchedfile:
            watchedreader = csv.reader(watchedfile)
            for submission in watchedreader:
                # Split submission into 'id':('created_utc', ['score1|posts1', 'score2|posts2'...]
                watchedthreads[submission[0]] = (float(submission[1]), submission[2:len(submission)+1])
                logger.debug("Loaded {0}".format(submission[0]))
            # pprint.pprint(watchedthreads)
    except FileNotFoundError:
        logger.warning("No watchlist file present. Using empty watchlist.")
    logger.info("Watching {0} threads.".format(len(watchedthreads)))
    return watchedthreads


def get_newthreads(watchedthreads, threads=2):
    logger.debug("Getting newest {0} submissions to /r/AskReddit".format(threads))
    for submission in subreddit.new(limit=threads):
        logger.debug("Found thread ID {0}".format(submission.id))
        # print("Title: {0}".format(submission.title))
        # print("Score: {0}".format(submission.score))
        # print("Comments: {0}".format(submission.num_comments))


def main():
    starttime = time.perf_counter()
    logger.info("-----------------------------------------")
    logger.info("Started execution at {0}".format(time.strftime("%H:%M:%S, %d/%m/%Y", time.localtime())))
    logger.info("-----------------------------------------")
    watched = readfiles()
    endtime = time.perf_counter()
    mins, secs = divmod(endtime - starttime, 60)    # Easiest way to quickly split into mm:ss
    logger.info("-----------------------------------------")
    logger.info("Ended execution at {0}".format(time.strftime("%H:%M:%S, %d/%m/%Y", time.localtime())))
    logger.info("Executed in {0}m, {1}s.".format(int(mins), secs))
    logger.info("-----------------------------------------")
main()
