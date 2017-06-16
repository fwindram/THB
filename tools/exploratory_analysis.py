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
#   - Range
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
test = [x + 1 for x in range(3565)]

marks = find_percentage_marks(3565)
pprint(marks)
for i in range(3565):
    if i in marks:
        print("{0}% at {1}".format(marks[i], test[i]))

# for mark in marks:
#     print("{0}% at {1}".format(marks[mark], test[mark]))
