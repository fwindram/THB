#! /usr/bin/env python

# THB.py
# Skeletorfw
# 30/04/17
# Version 1.0.1
#
# Python 3.4.1
#
# Bot to pull askreddit threads and trend popularity over time

# import os     # Will need for log rotation if done in here.
import csv
import logging
import time
from datetime import datetime
from operator import itemgetter

# V2 Multithreaded refactor
import threading
import sched
import sqlite3
from os.path import isfile
from queue import Queue
from random import randint

import praw
from prawcore import RequestException

debugmode = False

# Set up logging
# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create logfile handler
handler = logging.FileHandler('log/THB.out')
handler.setLevel(logging.INFO)  # File logging level
if debugmode:
    handler.setLevel(logging.DEBUG)  # File logging level

# Create formatter and add to handler
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(funcName)s - %(message)s')
handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(handler)

# BOT CONFIG
reddit = praw.Reddit('bot1')
sr = reddit.subreddit("askreddit")
base_threads_to_pull = 5  # Calculated that over a 1/10m every 24h (288 runs) this should never hit 500
maxthreads = 500
threadpull_mod = 10

archiveage = 86400  # 24h = 86400s

dbpath = "data/THB_db.sqlite3"

# DB setup
if not isfile(dbpath):
    # Create db!
    logger.warning("DB not found at {}!".format(dbpath))
    logger.warning("Creating new DB file and setting up tables...")
    with open("tools/create_THB_db.sql", "r") as f:
        createscript = f.read()
    db = sqlite3.connect(dbpath)
    cursor = db.cursor()
    cursor.executescript(createscript)
    db.commit()
    logger.warning("DB successfully created.")
    db.close()

# Set up FIFO thread queue for db commits
q = Queue()

##### THB V2

s = sched.scheduler(time.time, time.sleep)


class SubmissionPoller(threading.Thread):
    def __init__(self, submission_id, run_number, q, timeout=300, daemon=True):    # Daemon is true for testing
        threading.Thread.__init__(self)
        self.name = submission_id           # Thread name (inbuilt)
        self.submission_id = submission_id  # Reddit post submission ID
        self.run_number = run_number        # Run number (1 - 143) - t0 is set when the thread is initially found
        self.q = q                          # Queue object for threads to add their submissions to.
        self.timeout = timeout              # How long before the run func gives up on polling reddit and schedules the next job anyway
        self.daemon = daemon                # Is this a daemon thread?
        self.starttime = time.time()
        self.submission_data = None

    def run(self):
        logger.debug("Checking submission {}, run {}/144".format(self.submission_id, self.run_number))
        self.checkstats()

    def checkstats(self):
        successful = False
        while True:
            try:
                # Try to retrieve data
                self.submission_data = reddit.submission(self.submission_id)
                successful = True
                break
            except RequestException:
                logger.exception("Request exception for {}".format(self.submission_id))
                if time.time() - self.starttime >= self.timeout:
                    logger.warning("Run {}/144 of submission {} timed out!"
                                   .format(self.run_number + 1, self.submission_id))
                    break
                else:
                    time.sleep(5)
        if successful:
            # commit to db
            logger.info("{} at run {}/144: Score:{}, Comments:{}".format(self.submission_id, self.run_number, self.submission_data.score, self.submission_data.num_comments))
            self.write_to_db_queue()
        # Schedule next job for starttime + 10m
        if self.run_number < 144:
            s.enterabs(self.starttime + 600, 1, launch_submissionpoller, argument=(self.submission_id,
                                                                                   self.run_number + 1,
                                                                                   self.q,
                                                                                   self.timeout,
                                                                                   self.daemon))
            logger.debug("Submitted poll {} for {}".format(self.run_number + 1, self.submission_id))
        else:
            logger.info("Completed tracking of {}".format(self.submission_id))

    def write_to_db_queue(self):
        # Check if self.submission_data is filled
        logger.debug("Writing data for {} from run {}/144 to db queue...".format(self.submission_id, self.run_number))
        self.q.put({"newentry": False,
                    "id": self.submission_id,
                    "c_name": "c_t{}".format(self.run_number),
                    "comments": self.submission_data.num_comments,
                    "s_name": "s_t{}".format(self.run_number),
                    "score": self.submission_data.score})


class SubmissionGetter(threading.Thread):
    def __init__(self, subreddit, db_queue, name="submissiongetter", daemon=True):
        threading.Thread.__init__(self)
        self.name = name                    # Thread name (inbuilt)
        self.subreddit = subreddit
        self.q = db_queue
        self.daemon = daemon                # Is this a daemon thread?

    def run(self):
        logger.info("Starting SubmissionGetter thread")
        logger.info("Tracking {}".format(self.subreddit.display_name))
        subcounter = 0
        while True:
            try:
                for submission in self.subreddit.stream.submissions(skip_existing=True):
                    print(subcounter)
                    if subcounter % threadpull_mod == 0 and len(s.queue) < maxthreads:
                        logger.info("Tracking ID: {}, Title: {}, Submitted: {}\nTracking {} threads"
                                    .format(submission.id,
                                            submission.title,
                                            datetime.utcfromtimestamp(submission.created_utc).strftime('%Y-%m-%d %H:%M:%S'),
                                            len(s.queue)))
                        self.q.put({"newentry": True,
                                    "id": submission.id,
                                    "title": submission.title,
                                    "author": submission.author.name,
                                    "ts": submission.created_utc,
                                    "comments": submission.num_comments,
                                    "score": submission.score})
                        s.enterabs(time.time() + 600, 1, launch_submissionpoller, argument=(submission.id,
                                                                                            1,
                                                                                            self.q,
                                                                                            300,
                                                                                            False))
                        logger.debug("Submitted next poll for {} in 10m, Now watching {} threads"
                                     .format(submission.id, len(s.queue) - 1))
                    else:
                        logger.debug("Skipping submission.")
                    subcounter += 1
            except RequestException:
                logger.exception("Request exception occurred when streaming posts. Restarting stream.")
            except Exception:
                logger.exception("Unhandled exception occurred when streaming posts. Restarting stream.")


class DBWriter(threading.Thread):
    def __init__(self, db_queue, db_path, delaytime=300, name="DBWriter", daemon=None):
        threading.Thread.__init__(self)
        self.q = db_queue
        self.dbpath = db_path
        self.name = name                    # Thread name (inbuilt)
        self.delaytime = delaytime          # Delay time between db runs in seconds
        self.daemon = daemon                # Is this a daemon thread?

    def run(self):
        logger.info("Starting db commit run")
        if q.qsize() > 0:
            logger.info("Committing {} elements to the db".format(q.qsize()))
            tocommit = [q.get_nowait() for x in range(q.qsize())]
            newentries = [x for x in tocommit if x["newentry"] is True]
            updateentries = [x for x in tocommit if x["newentry"] is False]
            db = sqlite3.connect(self.dbpath)
            cur = db.cursor()
            try:
                if newentries:
                    logger.debug("Writing {} new entries to db".format(len(newentries)))
                    cur.executemany(''' INSERT INTO submissions(id, title, author, date, c_t0, s_t0)
                                        VALUES(:id, :title, :author, :ts, :comments, :score)''',
                                    newentries)
                    db.commit()
                if updateentries:
                    logger.debug("Updating {} entries in db".format(len(updateentries)))
                    for update in updateentries:
                        try:
                            cur.execute(''' UPDATE submissions SET {} = :comments, {} = :score WHERE id=:id'''
                                        .format(update["c_name"], update["s_name"]),
                                        update)
                            db.commit()
                        except Exception:
                            logger.exception("Failed to update {} in db.".format(update["id"]))
                            db.rollback()

            except Exception:
                logger.exception("An unhandled exception occurred when writing to the db.")
                db.rollback()
            finally:
                db.close()
        else:
            logger.info("Nothing to commit")
        self.reschedule()

    def reschedule(self):
        # logger.debug("Time is {}, Launching next db run at {}".format(time.time(), time.time() + self.delaytime))
        s.enterabs(time.time() + self.delaytime, 1, launch_dbwriter, argument=(self.q,
                                                                               self.dbpath,
                                                                               self.delaytime,
                                                                               self.name,
                                                                               self.daemon))


def launch_submissionpoller(submission_id, run_number, queue, timeout, daemon):
    thread = SubmissionPoller(submission_id, run_number, queue, timeout, daemon)
    thread.start()


def launch_dbwriter(db_queue, db_path, delaytime, name, daemon):
    thread = DBWriter(db_queue, db_path, delaytime, name, daemon)
    thread.start()


def main():
    logger.info("Starting THBv2")
    submissiongetter = SubmissionGetter(sr, q)
    submissiongetter.start()
    dbwrite = DBWriter(q, dbpath, delaytime=60)
    dbwrite.start()

    while True:
        try:
            s.run(blocking=False)
            time.sleep(1)
        except KeyboardInterrupt:
            print("Exiting THB...")
            break


main()
