#!/bin/bash

# Example usage:
# Declare an associative array (Bash 4.0+)
declare -A short_attack_names
short_attack_names[0]="Data Poisoning"
short_attack_names[1]="N/A"
short_attack_names[2]="Model Inversion"
short_attack_names[3]="Evasion Attack"

# Define the output file name
OUTPUT_FILE="output.json"

# Clear the output file if it exists, or create it
> "$OUTPUT_FILE"

# Initialize an empty array to hold all JSON objects
ALL_JSON_OBJECTS=()

# Iterate through the array
for i in "${!short_attack_names[@]}"; do
    if [[ "${short_attack_names[$i]}" != "N/A" ]]; then
        ATTACK_NAME="${short_attack_names[$i]}"
        # Generate a single JSON object (without the surrounding array brackets)
        SINGLE_JSON_OBJECT="{\"prediction\": \"$ATTACK_NAME\", \"confidence\": 0.6}"
        
        # Add the single JSON object to our array
        ALL_JSON_OBJECTS+=("$SINGLE_JSON_OBJECT")
    fi
done

# Join all JSON objects with a comma and wrap them in a single JSON array
# This ensures the output.json file contains a valid JSON array of objects
FINAL_JSON_OUTPUT="[$(IFS=,; echo "${ALL_JSON_OBJECTS[*]}") ]"

# Print the final JSON output to the screen
echo "$FINAL_JSON_OUTPUT"

# Store the final JSON output to the file
echo "$FINAL_JSON_OUTPUT" > "$OUTPUT_FILE"

echo "---"
echo "JSON output also saved to $OUTPUT_FILE"
