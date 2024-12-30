#!/bin/bash

# Check if the correct number of arguments is given
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <input.pcap>"
    exit 1
fi

input_pcap="$1"
output_csv="${input_pcap%.pcap}.csv"

# Check if tshark is installed
if ! command -v tshark &> /dev/null; then
    echo "tshark could not be found, please install it."
    exit 1
fi

# Extract timestamp and packet length from the pcap file and write to csv
tshark -r "$input_pcap" -T fields -e frame.time_epoch -e frame.len -E header=y -E separator=, -E quote=n -E occurrence=f > "$output_csv"

echo "Output CSV generated: $output_csv"
