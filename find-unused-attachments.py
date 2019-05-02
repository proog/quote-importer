#!/usr/bin/env python3

import os
import subprocess
import sys
from os.path import abspath, isdir, isfile, join

log_file = abspath(sys.argv[1])
attachments_dir = abspath(sys.argv[2])

if not isfile(log_file) or not isdir(attachments_dir):
    exit(1)

attachments = os.listdir(attachments_dir)

for attachment in attachments:
    attachment_path = join(attachments_dir, attachment)

    if attachment_path == log_file:
        continue

    found = subprocess.call(["grep", "-q", attachment, log_file]) == 0

    if not found:
        print(attachment)
