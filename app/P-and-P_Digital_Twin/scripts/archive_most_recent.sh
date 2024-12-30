#!/bin/bash

# Specify the directory to search (replace '/path/to/your/directory' with your actual directory)
DIRECTORY="./comnetsemu_5Gnet/"

# Specify the number of days (N) for modification time
N_DAYS=10

# Find files modified within the last N days
find "$DIRECTORY" -type f -mtime -$N_DAYS -print0 | xargs -0 tar czvf archive.tgz
