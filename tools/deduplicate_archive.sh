#!/bin/bash
# THB archive deduplicator.
THB='/home/thb/bot/'    # Replace with bot home dir (which contains THB.py).
cd $THB
cd data
awk '!a[$0]++' archive.csv > archive_dedup.csv
mv archive.csv archive.csv_old && mv archive_dedup.csv archive.csv