#!/bin/bash

# Define the pcap file
PCAP_FILE="../dns.pcap"

# Run the pcapninja command and store the output
PCAP_OUTPUT=$(python3 pcapninja.py --pcap_file "${PCAP_FILE}")

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

# Initialize arrays to store attack types and IP addresses
declare -a attack_types
declare -a ip_addresses

# Process each line in the security concerns section
while IFS= read -r line; do
    # Skip the "5. Security Concerns:" header itself
    if [[ "$line" == "5. Security Concerns:" ]]; then
        continue
    fi

    # Extract potential attack types and IP addresses
    # This pattern looks for common attack-related keywords followed by an IP
    # or just an IP if it's explicitly mentioned as high traffic/targeted.
    if [[ "$line" =~ (.*[Dd]DoS.*|.*[Hh]igh traffic concentration.*|.*[Tt]raffic on unusual ports.*) ]]; then
        # Capture the entire line as the "attack type" for now,
        # as the description itself gives context.
        # We can refine this if specific keywords are needed.
        attack_types+=("$(echo "$line" | sed 's/^[[:space:]]*//')")

        # Extract IP addresses from the line
        # This regex matches standard IPv4 addresses
        if [[ "$line" =~ ([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}) ]]; then
            ip_addresses+=("${BASH_REMATCH[1]}")
        fi
    fi
done <<< "${SECURITY_CONCERNS_SECTION}"

# Print the extracted information
echo "--- Security Concerns ---"
if [ ${#attack_types[@]} -eq 0 ]; then
    echo "No specific attack types or IPs found."
else
    for i in "${!attack_types[@]}"; do
        echo "Attack Type: ${attack_types[$i]}"
        if [ -n "${ip_addresses[$i]}" ]; then
            echo "Associated IP: ${ip_addresses[$i]}"
        else
            echo "Associated IP: Not specified"
        fi
        echo "-------------------------"
    done
fi
