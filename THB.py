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
from pprint import pprint

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
archiveage = 86400


def readfiles():
    """Read the current watching file and return as a dict"""
    logger.debug("Reading watchlist.")
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


def get_threads(watchedthreads, threads=2):
    logger.debug("Getting newest {0} submissions to /r/AskReddit".format(threads))
    for submission in subreddit.new(limit=threads):
        logger.debug("Found thread ID {0}".format(submission.id))
        # print("Title: {0}".format(submission.title))
        # print("Score: {0}".format(submission.score))
        # print("Comments: {0}".format(submission.num_comments))


def archive_threads(watchedthreads, stale_age=86400):
    """Archive threads over 24h old."""
    # We archive threads before polling to decrease the number of requests made to the reddit API.
    # And so we can implement archiving without pulling new threads as an alternate execution mode.
    logger.debug("Archiving stale threads.")
    stalethreads = []

    for threadid in watchedthreads:
        threadvalues = watchedthreads[threadid]
        age = time.time() - threadvalues[0]     # Calculate age from current time and created_utc
        agemins, agesecs = divmod(age, 60)      # Cannot use strftime as time could be over 24h, which causes problems.
        agehrs, agemins = divmod(agemins, 60)
        logger.debug("Thread {0} is {1}h {2}m {3}s old.".format(threadid, int(agehrs), int(agemins), int(agesecs)))
        if age > stale_age:     # Stale age is 24h by default
            logger.debug("Thread {0} is stale.".format(threadid))
            # Build archive row for entry
            archiverow = [threadid, threadvalues[0]]
            for timesegment in threadvalues[1]:
                archiverow.append(timesegment)
            stalethreads.append(archiverow)
        
    with open("data/archive.csv", "a", newline='') as archivefile:      # Automatically creates file if not found
        # newline behaviour will have to be checked on UNIX.
        archivewriter = csv.writer(archivefile)
        archivewriter.writerows(stalethreads)
        logger.info("Archived {0} stale threads.".format(len(stalethreads)))
    for thread in stalethreads:
        del watchedthreads[thread[0]]    # Remove archived threads from watchedthreads
    logger.debug("Deleted {0} stale threads from watchlist.".format(len(stalethreads)))

    return watchedthreads


def main():
    starttime = time.perf_counter()
    logger.info("-----------------------------------------")
    logger.info("Started execution at {0}".format(time.strftime("%H:%M:%S, %d/%m/%Y", time.localtime())))
    logger.info("-----------------------------------------")
    watched = readfiles()
    watched = archive_threads(watched, archiveage)
    endtime = time.perf_counter()
    runtime = time.strftime("%H:%M:%S", time.gmtime(endtime - starttime))
    logger.info("-----------------------------------------")
    logger.info("Ended execution at {0}".format(time.strftime("%H:%M:%S, %d/%m/%Y", time.localtime())))
    logger.info("Executed in {0}.".format(runtime))
    logger.info("-----------------------------------------")
main()
