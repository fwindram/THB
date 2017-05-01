# THB.py
# Skeletorfw
# 30/04/17
# Version 1.0
#
# Python 3.4.1
#
# Bot to pull askreddit threads and trend popularity over time

import praw
import logging
import time
# import os     # Will need for log rotation if done in here.
import csv
from operator import itemgetter

# Set up logging
# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create logfile handler
handler = logging.FileHandler('log/THB.out')
handler.setLevel(logging.INFO)  # File logging level

# Create formatter and add to handler
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(funcName)s - %(message)s')
handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(handler)

# CONFIG
reddit = praw.Reddit('bot1')
subreddit = reddit.subreddit("AskReddit")
base_threads_to_pull = 5  # Calculated that over a 1/10m every 24h (288 runs) this should never hit 500
maxthreads = 500
archiveage = 86400  # 24h = 86400s


def readfiles():
    """Read the current watching file and return as a dict"""
    logger.debug("Reading watchlist.")

    watchedthreads = {}
    try:
        with open("data/watched.csv") as watchedfile:
            watchedreader = csv.reader(watchedfile)
            for submission in watchedreader:
                # Split submission into 'id':('created_utc', ['offset|score1|posts1', 'offset|score2|posts2'...]
                watchedthreads[submission[0]] = (float(submission[1]), submission[2:len(submission) + 1])
                logger.debug("Loaded {0}.".format(submission[0]))
    except FileNotFoundError:
        logger.warning("No watchlist file present. Using empty watchlist.")

    logger.info("Pulled {0} threads from watchlist.".format(len(watchedthreads)))

    return watchedthreads


def get_threads(watchedthreads, threads=1):
    """Get new threads from reddit and add to watchlist"""
    logger.debug("Getting newest {0} submissions to /r/AskReddit.".format(threads))

    added = 0
    for submission in subreddit.new(limit=threads):
        logger.debug("Found {0}.".format(submission.id))
        if submission.id not in watchedthreads:
            watchedthreads[submission.id] = (int(submission.created_utc),
                                             ["{0}|{1}|{2}".format(max(int(time.time() - submission.created_utc), 0),
                                                                   submission.score,
                                                                   submission.num_comments)
                                              ]
                                             )
            logger.debug("Added {0} to watchlist.".format(submission.id))
            added += 1
        else:
            logger.debug("{0} already in watchlist.".format(submission.id))
    logger.info("Added {0}/{1} new threads to watchlist.".format(added, threads))

    return watchedthreads


def archive_threads(watchedthreads, stale_age=86400):
    """Archive threads over stale_age old (usually 24h)."""
    # We archive threads before polling to decrease the number of requests made to the reddit API.
    # And so we can implement archiving without pulling new threads as an alternate execution mode.
    logger.debug("Archiving stale threads.")

    stalethreads = []
    for threadid in watchedthreads:
        threadvalues = watchedthreads[threadid]
        age = time.time() - threadvalues[0]  # Calculate age from current time and created_utc
        agemins, agesecs = divmod(age, 60)  # Cannot use strftime as time could be over 24h, which causes problems.
        agehrs, agemins = divmod(agemins, 60)
        logger.debug("Thread {0} is {1}h {2}m {3}s old.".format(threadid, int(agehrs), int(agemins), int(agesecs)))
        if age > stale_age:  # Stale age is 24h by default
            logger.debug("Thread {0} is stale.".format(threadid))
            # Build archive row for entry
            archiverow = [threadid, threadvalues[0]]
            for timesegment in threadvalues[1]:
                archiverow.append(timesegment)
            stalethreads.append(archiverow)

    with open("data/archive.csv", "a", newline='') as archivefile:  # Automatically creates file if not found
        # newline behaviour will have to be checked on UNIX.
        archivewriter = csv.writer(archivefile)
        archivewriter.writerows(stalethreads)
        logger.info("Archived {0} stale threads.".format(len(stalethreads)))
    for thread in stalethreads:
        del watchedthreads[thread[0]]  # Remove archived threads from watchedthreads
    logger.debug("Deleted {0} stale threads from watchlist.".format(len(stalethreads)))

    return watchedthreads


def update_threads(watchedthreads):
    """Updates watched threads with current score & comments count."""
    logger.debug("Updating threads.")

    for threadid in watchedthreads:
        # NEED to handle invalid IDs here. Can't find the right exception at present!
        # For some reason praw.exceptions.PRAWException is not valid.
        # For now, we can assume all IDs are valid, as they should only ever be pulled from reddit in the fist place.
        submission = reddit.submission(threadid)
        watchedthreads[threadid][1].append("{0}|{1}|{2}".format(int(time.time() - submission.created_utc),
                                                                submission.score,
                                                                submission.num_comments))
        logger.debug("Updated {0}. Score = {1}. Comments = {2}.".format(threadid,
                                                                        submission.score,
                                                                        submission.num_comments))
    logger.info("Updated {0} threads.".format(len(watchedthreads)))

    return watchedthreads


def write_watchedfile(watchedthreads):
    """Write watchfile out to csv for next time"""
    logger.debug("Writing watchfile to disk.")

    threads = []
    for threadid in watchedthreads:
        logger.debug("Processing {0} for final write.".format(threadid))
        workthread = watchedthreads[threadid]
        watchedrow = [threadid, workthread[0]]
        for timesegment in workthread[1]:
            watchedrow.append(timesegment)
        threads.append(watchedrow)    # Append string to final output holder
    threads = sorted(threads, key=itemgetter(1))    # Sort by time created.

    with open("data/watched.csv", "w", newline='') as watchedfile:
        watchedwriter = csv.writer(watchedfile)
        watchedwriter.writerows(threads)
    logger.info("Wrote {0} threads to disk watchlist.".format(len(threads)))


def main():
    starttime = time.perf_counter()
    logger.info("-----------------------------------------")
    logger.info("Started execution at {0}".format(time.strftime("%H:%M:%S, %d/%m/%Y", time.localtime())))
    logger.info("-----------------------------------------")
    watched = readfiles()
    watched = archive_threads(watched, archiveage)
    watched = update_threads(watched)
    # Calculate threads to pull as a proportion of maxthreads, but always look to pull 1.
    threads_to_pull = max(int((maxthreads - len(watched)) / maxthreads * base_threads_to_pull), 1)
    if len(watched) + threads_to_pull <= maxthreads:  # Don't bother getting new threads if already at max.
        watched = get_threads(watched, threads_to_pull)
    write_watchedfile(watched)
    endtime = time.perf_counter()
    runtime = time.strftime("%H:%M:%S", time.gmtime(endtime - starttime))
    logger.info("-----------------------------------------")
    logger.info("Ended execution at {0}".format(time.strftime("%H:%M:%S, %d/%m/%Y", time.localtime())))
    logger.info("Executed in {0}.".format(runtime))
    logger.info("-----------------------------------------")


main()
