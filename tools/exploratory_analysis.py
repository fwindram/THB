# exploratory_analysis.py
# Skeletorfw
# 14/06/17
#
# Python 3.4.1
#
# Processes binned THB archives and perform some basic exploaratory analysis

# TODO: Generate basic statistics:
#   - Sample size
#   - Total data points
#   - Final score range
#   - Median final score/comments
#   - Mean & SD of same
# TODO: Identify top posts
# TODO: Identify super-top posts (score or comments >= 10,000)
# TODO: Split archive into logarithmic bins by score or comments (x<10, 100>x>=10, 1,000>x>=100, x>=1,000)
# TODO: Sample randomly from bins or whole post to give sample for exploratory data analysis
# TODO: Graph if possible
#   - Simple frequency distribution of final scores of all data.
#   - 2D freq dist involving comments & score
#   - See http://matplotlib.org/api/pyplot_api.html#matplotlib.pyplot.hist
#   - See http://docs.astropy.org/en/stable/visualization/histogram.html
#   - Maybe see https://plot.ly/python/line-charts/

from pprint import pprint
import csv
import math
import statistics
from collections import namedtuple


def read_archive():
    """Read the current archive file and return as a dict"""
    print("Reading archive.")

    archivethreads = {}
    try:
        with open("../data/archive_binned.csv") as archivefile:
            archivereader = csv.reader(archivefile)
            for submission in archivereader:
                # Split submission into 'id':('created_utc', ['offset|score1|posts1', 'offset|score2|posts2'...]
                archivethreads[submission[0]] = (float(submission[1]), submission[2:len(submission) + 1])
    except FileNotFoundError:
        print("No binned archive file present. Using empty archive.")

    print("Pulled {0} threads from archive.".format(len(archivethreads)))

    return archivethreads


def find_percentage_marks(seq_len, period=10, index_from=0):
    """Find indices closest to percentage steps of a sequence.
    
    Usually used to create marker points for creating accurate progress markers.
    When a counter is set up in an iteration loop, you can check against the dict and log/print a progress message.

    :param seq_len: The integer length of the sequence you want step locations for.
    :param period: The % steps to divide the sequence into. Choose from 1,2,5,10,25,50 (for now)
    :param index_from: Where to index from. If not 0, add this to all values before returning
    :type seq_len: int
    :type period: int
    :type index_from: int
    :returns: A dict in the form {index1: percentage_mark1, index2: percentage_mark2...}
    :raises ArgumentError: If arguments are not ints or are invalid."""

    # Check args
    class ArgumentError(Exception):
        """Raised if arguments are not ints or are invalid."""

    try:
        # Make sure all args are numbers.
        seq_len = int(seq_len)
        period = int(period)
        index_from = int(index_from)
        if period not in [1, 2, 5, 10, 25, 50]:
            raise ArgumentError
    except ValueError:
        raise ArgumentError

    target_numbers = {}
    target_counter = 0
    while True:
        target_counter += period  # Increment counter by period
        if target_counter > 100:    # Break if over 100% of seq length
            break

        # Get target_counter% of seq_len, correct for indexing.
        step_idx = int((seq_len / 100 * target_counter)) + (-1 + index_from)

        target_numbers[step_idx] = target_counter

    return target_numbers


def find_final_entry(archive):
    """Returns all the final scores from an archive in the THB format.
    
    Using one (fairly obtuse) dictionary comprehension, this finds the final recorded score of each ID.
    
    :param archive: Archive of entries in the standard THB format.
    :type archive: dict
    :returns: namedtuple containing (full list of IDs and associated data, Hi->Lo sorted scores, Hi->Lo sorted comments)
    """
    # Find the final entry in the entries list for each ID, split on |, and get comments & score
    full = [[x, int(archive[x][1][-1].split('|')[1]), int(archive[x][1][-1].split('|')[2])] for x in archive]
    scores = [x[1] for x in full]
    comments = [x[2] for x in full]
    scores.sort(reverse=True)
    comments.sort(reverse=True)
    out_tuple = namedtuple("final", "full, score, comments")    # We use a named tuple to allow access by name.
    output = out_tuple(full, scores, comments)
    return output


def basic_statistics(sorted_arc):

    sample_size = (len(sorted_arc))
    sample_max = sorted_arc[0]
    sample_min = sorted_arc[-1]
    sample_median = statistics.median(sorted_arc)
    sample_mean = statistics.mean(sorted_arc)
    sample_sd = statistics.stdev(sorted_arc, sample_mean)   # Pass mean to save recalculation

    print("{0:>18} = {1}".format("Sample Size", sample_size))
    print("{0:>18} = {1}".format("Max", sample_max))
    print("{0:>18} = {1}".format("Min", sample_min))
    print("{0:>18} = {1}".format("Median", sample_median))
    print("{0:>18} = {1}".format("Mean", sample_mean))
    print("{0:>18} = {1}".format("Standard Deviation", sample_sd))


main_archive = read_archive()
final = find_final_entry(main_archive)
print("\nScore")
basic_statistics(final.score)
print("\nComments")
basic_statistics(final.comments)
print("Done")
