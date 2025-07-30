#!/bin/bash

# Define the pcap file
PCAP_FILE="../dns.pcap"

# Define the output file name
OUTPUT_FILE="output.json"

# Run the pcapninja command and store the output
PCAP_OUTPUT=$(python3 -W ignore pcapninja.py --pcap_file "${PCAP_FILE}")

# Extract the "Security concerns" section
SECURITY_CONCERNS_SECTION=$(echo "${PCAP_OUTPUT}" | awk '/^5\. Security Concerns:/,/^6\. Key Recommendations:/ {
    if ($0 ~ /^5\. Security Concerns:/) {
        found_start=1
    } else if ($0 ~ /^6\. Key Recommendations:/) {
        found_end=1
    }
    if (found_start && !found_end) {
        print
    }
}')

# Initialize arrays to store short attack names and IP addresses
declare -a short_attack_names
declare -a ip_addresses

# Process each line in the security concerns section
while IFS= read -r line; do
    # Skip the "5. Security Concerns:" header itself
    if [[ "$line" == "5. Security Concerns:" ]]; then
        continue
    fi

    # Initialize variables for current line
    current_attack_name=""
    current_ip=""

    # Try to extract the short attack name
    if [[ "$line" =~ [Dd][Dd][Oo][Ss] ]]; then
        # for DEMO 3
        # current_attack_name="DDoS"
        # for DEMO 2
        current_attack_name="DNS Amplification"
    elif [[ "$line" =~ [Uu]nusual\ ports ]]; then
        current_attack_name="Unusual Port Traffic"
    elif [[ "$line" =~ [Hh]igh\ traffic\ concentration ]]; then
        current_attack_name="High Traffic Concentration"
    fi

    # Extract IP addresses from the line if any
    if [[ "$line" =~ ([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}) ]]; then
        current_ip="${BASH_REMATCH[1]}"
    fi

    # Only add to arrays if we found a recognized attack type or an IP address
    if [[ -n "$current_attack_name" || -n "$current_ip" ]]; then
        short_attack_names+=("$current_attack_name")
        ip_addresses+=("$current_ip")
    fi

done <<< "${SECURITY_CONCERNS_SECTION}"

# Print the extracted information
echo "--- P\&P NDT Security Concerns ---"
if [ ${#short_attack_names[@]} -eq 0 ] && [ ${#ip_addresses[@]} -eq 0 ]; then
    echo "No specific attack types or IPs found."
else
    for i in "${!short_attack_names[@]}"; do
        echo "Attack Type (short): ${short_attack_names[$i]:-N/A}" # Use N/A if attack type is empty
        echo "Associated IP: ${ip_addresses[$i]:-N/A}"            # Use N/A if IP is empty
        echo "-------------------------"
    done
fi

# Initialize array for JSON objects
declare -a ALL_JSON_OBJECTS

# Iterate through the array
if [ ${#short_attack_names[@]} -eq 0 ] && [ ${#ip_addresses[@]} -eq 0 ]; then
    echo "No JSON output to generate."
else
    for i in "${!short_attack_names[@]}"; do
        if [[ "${short_attack_names[$i]}" != "N/A" && -n "${short_attack_names[$i]}" ]]; then
            ATTACK_NAME="${short_attack_names[$i]}"
            # Generate a single JSON object (without the surrounding array brackets)
            SINGLE_JSON_OBJECT="{\"prediction\": \"$ATTACK_NAME\", \"confidence\": 0.6}"
            
            # Add the single JSON object to our array
            ALL_JSON_OBJECTS+=("$SINGLE_JSON_OBJECT")
        fi
    done

    # Join all JSON objects with a comma and wrap them in a single JSON array
    # This ensures the output.json file contains a valid JSON array of objects
    FINAL_JSON_OUTPUT="[$(IFS=,; echo "${ALL_JSON_OBJECTS[*]}")]"
    
    # Print the final JSON output to the screen
    echo "$FINAL_JSON_OUTPUT"
    
    # Store the final JSON output to the file
    echo "$FINAL_JSON_OUTPUT" > "$OUTPUT_FILE"
    
    echo "---"
    echo "JSON output also saved to $OUTPUT_FILE"
    
    echo "[HORSE SAN] Sending JSON file to DTE module"
    
    # Send the actual JSON content from the file to avoid variable expansion issues
    curl -X 'POST' \
      'http://10.208.11.73:9898/receive-data/' \
      -H 'accept: application/json' \
      -H 'Content-Type: application/json' \
      -d @"$OUTPUT_FILE"
    
    echo
    echo "[HORSE SAN] DTE notification complete, waiting for another message from EM module"
    echo
fi
