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
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = logging.FileHandler('THB.out')
handler.setLevel(logging.DEBUG)



reddit = praw.Reddit('bot1')
subreddit = reddit.subreddit("AskReddit")
threads_to_pull = 20


def get_newthreads(threads=20):
    for submission in subreddit.new(limit=threads):
        print("Title: {0}".format(submission.title))
        print("Score: {0}".format(submission.score))
        print("Comments: {0}".format(submission.num_comments))
        print()