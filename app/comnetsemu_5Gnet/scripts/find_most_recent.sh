#!/bin/bash

# Specify the directory where your files are located
directory="../data/"

# Specify the prefix you're interested in (e.g., "mystring")
prefix="trace"

# Specify the file extension (e.g., ".txt", ".log", etc.)
file_extension=".pcap"

# Find all files with the specified prefix and extension
files=$(find "$directory" -maxdepth 1 -type f -name "$prefix*$file_extension")

# Get the most recent file
most_recent_file=""
most_recent_timestamp=0
for file in $files; do
    timestamp=$(stat -c %Y "$file")
    if ((timestamp > most_recent_timestamp)); then
        most_recent_timestamp=$timestamp
        most_recent_file="$file"
    fi
done

# Store the most recent file in a variable
my_variable="$most_recent_file"

# Print the result (optional)
echo "Most recent file: $my_variable"

# Convert to csv
./pcap_to_csv.sh $my_variable
csv_filename="${my_variable%.pcap}.csv"
echo "Predicting from $csv_filename"
python3 traffic_prediction.py --training-split 0.5 --sample-period 0.1S --csv $csv_filename
