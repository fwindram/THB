# TopHotBot.py
TopHotBot (THB) is a reddit bot written in Python 3 using PRAW.
It is designed to poll for new threads to AskReddit every 10 minutes and then track them for a full 24 hours.

### Output
THB has two major outputs, of which one is never modified, only appended to.
These are located in the /data directory.

* *watched.csv* contains the currently watched threads that THB is tracking.
* *archive.csv* contains threads over 24h old (by default). These are no longer added to and are there as a record

The data in both files is in the following format:
```
threadid,created,age1|score1|comments1,age2|score2|comments2...
```
* threadid = Reddit submission ID
* created = time created in seconds since epoch
* agex = difference between time logged and time created
* scorex = score (upvotes - downvotes) at time logged
* commentsx = number of comments at time logged

### Setup
To use THB for your own nefarious data-collecting purposes, there are a few things you need to set up:

* You must set up a praw.ini file in the main dir (see the [praw documentation](http://praw.readthedocs.io/en/latest/getting_started/configuration/prawini.html) for details).
    * This will need to include *your own* client_id, client_secret & user_agent settings.
    * Provided is a dummy.ini file you can edit and rename to praw.ini to make things easier.
* To automate this script, you will need to find a way to schedule runs every 10 minutes. I personally will be using a raspberry pi running it as a cron job.
* If you wish to poll a different subreddit, this is configured at the top of the THB.py file in the CONFIG section.

### Notes
* Currently THB is limited to tracking 500 threads at a time.
    * This is to allow a good amount of headroom when processing at max capacity.
* Sometimes the first logged timestamp won't match up. This is because negative ages due to weird timezones are set to 0.
    * I can probably fix this, but really a few seconds of error here or there should be negligable.
* Play with the config settings at your peril.
    * The defaults are there for good reason and you may hit unexpected behaviour if you fiddle too much.
    * You can play with the *subreddit* option however. That's pretty safe.

### The Future
In the future, I am planning on adding the following features to THB:
* A debug flag to enable debug logging
* A log rotation option to allow automated log flushing
* Options for automatically cleaning out the archive and watched lists
* Possibly splitting out the config to a separate YAML conf file.

### Issues
If you experience an issue using THB, please do raise an issue at [https://github.com/skeletorfw/THB/issues](https://github.com/skeletorfw/THB/issues) and I'll see what I can do to help.