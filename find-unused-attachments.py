#!/usr/bin/env python3

import os
import subprocess
import sys
from os.path import abspath, isdir, isfile, join

print_progress = not sys.stdout.isatty()


def printerr(*args, **kwargs):
    if print_progress:
        print(file=sys.stderr, *args, **kwargs)


log_file = ""
attachments_dir = ""
if len(sys.argv) == 3:
    log_file = abspath(sys.argv[1])
    attachments_dir = abspath(sys.argv[2])

if not isfile(log_file) or not isdir(attachments_dir):
    print("Usage: ./find-unused-attachments.py LOG_FILE ATTACHMENTS_DIR")
    exit(1)

attachments = os.listdir(attachments_dir)
total = len(attachments)
count = 0

for attachment in attachments:
    count += 1
    printerr("\rProcessing attachment %i of %i..." % (count, total), end="")

    attachment_path = join(attachments_dir, attachment)

    if attachment_path == log_file:
        continue

    found = subprocess.call(["grep", "-q", attachment, log_file]) == 0

    if not found:
        print(attachment)

printerr()
