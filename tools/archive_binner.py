# archive_binner.py
# Skeletorfw
# 08/05/17
# Version 0.1
#
# Python 3.4.1
#
# Processes THB archives, binning into 10m intervals and interpolating scores where necessary.

import csv
import logging
import time
from operator import itemgetter


# Set up logging
# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create logfile handler
handler = logging.FileHandler('../log/bin_log.out')
handler.setLevel(logging.INFO)  # File logging level

# Create formatter and add to handler
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(funcName)s - %(message)s')
handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(handler)


def read_archive():
    """Read the current archive file and return as a dict"""
    logger.debug("Reading archive.")

    archivethreads = {}
    try:
        with open("../data/archive.csv") as archivefile:
            archivereader = csv.reader(archivefile)
            for submission in archivereader:
                # Split submission into 'id':('created_utc', ['offset|score1|posts1', 'offset|score2|posts2'...]
                archivethreads[submission[0]] = (float(submission[1]), submission[2:len(submission) + 1])
                logger.debug("Loaded {0}.".format(submission[0]))
    except FileNotFoundError:
        logger.warning("No archive file present. Using empty archive.")

    logger.info("Pulled {0} threads from archive.".format(len(archivethreads)))

    return archivethreads


def bin_archive(archive):
    logger.debug("Binning archive to 10m intervals.")

    total_ts = 0
    for archiveid in archive:
        archiveentry = archive[archiveid]
        location = 0
        for ts in archiveentry[1]:
            ts_list = ts.split('|')
            # Clamp age to lowest age in bin
            ts_age_binned = int(ts_list[0]) // 600 * 600
            ts_list[0] = ts_age_binned
            total_ts += 1
            archiveentry[1][location] = "{0}|{1}|{2}".format(ts_list[0], ts_list[1], ts_list[2])
            location += 1
    logger.info("Binned {0} entries in {1} threads.".format(total_ts, len(archive)))

    return archive


def interpolate_and_deduplicate(archive):
    logger.debug("Interpolating missing values.")

    interpolated_ids = 0
    interpolated_count = 0
    removed_ids = 0
    removed_count = 0
    for archiveid in archive:
        archiveentry = archive[archiveid]

        # Split timestamp strings for easy parsing
        archiveentry_listed = []
        for ts in archiveentry[1]:
            ts_list = ts.split('|')
            archiveentry_listed.append(ts_list)

        notmatched = []
        # Match timestamps in reverse and note any which are not present.
        for i in reversed(range(0, 143)):
            test_timestamp = i * 600
            ts_index = 0
            for ts in archiveentry_listed:
                if int(ts[0]) == test_timestamp:
                    break
                elif int(ts[0]) > test_timestamp:     # If timestamp is greater than test, we've gone past
                    notmatched.append([test_timestamp, ts_index])   # Add missing timestamp and index of next timestamp
                    break
                ts_index += 1
        logger.debug("{0} timestamps missing from {1}.".format(len(notmatched), archiveid))

        # Interpolate missing values and insert at correct time.
        for ts in notmatched:
            score = (int(archiveentry_listed[ts[1]][1]) + int(archiveentry_listed[ts[1] - 1][1])) // 2
            comments = (int(archiveentry_listed[ts[1]][2]) + int(archiveentry_listed[ts[1] - 1][2])) // 2
            new_ts = [str(ts[0]), str(score), str(comments)]
            archiveentry_listed.insert(ts[1], new_ts)
        logger.debug("Interpolated {0} timestamps for {1} from surrounding timestamps.".format(len(notmatched), archiveid))

        if notmatched:
            interpolated_ids += 1
            interpolated_count += len(notmatched)

        # Following list comprehension is as follows:
        # If x[0] not in seen = True, seen.add(x[0]) runs, which always returns None
        # Thus not seen.add(x[0]) is True and so seen.add is run.
        # If x[0] not in seen = False, not seen.add(x[0]) is not run as Python breaks the condition there.
        # See http://stackoverflow.com/questions/24295578/

        seen = set()
        archiveentry_listed_dd = [x for x in archiveentry_listed if x[0] not in seen and not seen.add(x[0])]
        removed_ts = len(archiveentry_listed) - len(archiveentry_listed_dd)
        archiveentry_listed = archiveentry_listed_dd
        logger.debug("Removed {0} duplicates from {1}.".format(removed_ts, archiveid))

        if removed_ts:
            removed_ids += 1
            removed_count += removed_ts

        output_list = []
        for ts in archiveentry_listed:
            output_list.append("{0}|{1}|{2}".format(ts[0], ts[1], ts[2]))

        archive[archiveid] = (archive[archiveid][0], output_list)   # Write ts including interpolated ones to archive.

    logger.info("Interpolated {0} missing values in {1} threads.".format(interpolated_count, interpolated_ids))
    logger.info("Deleted {0} duplicate values in {1} threads.".format(removed_count, removed_ids))

    return archive


def write_archive(archive):
    """Write watchfile out to csv for next time"""
    logger.debug("Writing archive to disk.")

    threads = []
    for threadid in archive:
        logger.debug("Processing {0} for final write.".format(threadid))
        workthread = archive[threadid]
        archiverow = [threadid, workthread[0]]
        for timesegment in workthread[1]:
            archiverow.append(timesegment)
        threads.append(archiverow)    # Append string to final output holder
    threads = sorted(threads, key=itemgetter(1))  # Sort by time created.
    with open("../data/archive_binned.csv", "w", newline='') as archivefile:
        archivewriter = csv.writer(archivefile)
        archivewriter.writerows(threads)
    logger.info("Wrote {0} threads to disk archive.".format(len(threads)))


def main():
    starttime = time.perf_counter()
    logger.info("-----------------------------------------")
    logger.info("Started execution at {0}".format(time.strftime("%H:%M:%S, %d/%m/%Y", time.localtime())))
    logger.info("-----------------------------------------")
    archive = read_archive()
    archive = bin_archive(archive)
    interpolate_and_deduplicate(archive)
    write_archive(archive)
    endtime = time.perf_counter()
    runtime = time.strftime("%H:%M:%S", time.gmtime(endtime - starttime))
    logger.info("-----------------------------------------")
    logger.info("Ended execution at {0}".format(time.strftime("%H:%M:%S, %d/%m/%Y", time.localtime())))
    logger.info("Executed in {0}.".format(runtime))
    logger.info("-----------------------------------------")
main()
