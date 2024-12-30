import xml.etree.ElementTree as ET
import glob
import os

# Specify the folder path and the desired prefix
folder_path = './uploads/'
prefix = 'uploaded'  # Replace with your actual prefix

# Get a list of files matching the prefix
file_list = glob.glob(os.path.join(folder_path, f"{prefix}*"))

# Find the latest (most recent) file
latest_file = max(file_list, key=os.path.getctime)

# Now you can open or process the latest file as needed
print(f"Latest file: {latest_file}")

# Read the XML file (replace 'your_file.xml' with the actual file path)
file_path = latest_file
tree = ET.parse(file_path)
root = tree.getroot()

# Iterate through the elements and print their fields
#def print_fields(element, indent=0):
#    print("  " * indent + f"Element: {element.tag}")
#    for sub_element in element:
#        print_fields(sub_element, indent + 1)
#
#print_fields(root)

# Iterate through the elements and print field names and values
for element in root.iter():
    if element.text:
        print(f"{element.tag}: {element.text}")

# Define the tags you want to extract
tags_to_extract = ["timestamp", "Type", "Asset_Type", "Asset_IPAddress"]

# Initialize variables to store the extracted values
timestamp = None
type_value = None
asset_type_value = None
asset_ip_value = None
#tree = ET.parse(file_path)
#root = tree.getroot()

# Iterate through the elements and extract values for specified tags
print("\nVariables of interest:\n")
for element in root.iter():
    if element.tag in tags_to_extract and element.text:
        if element.tag == "Type":
            type_value = element.text
        elif element.tag == "Asset_Type":
            asset_type_value = element.text
        elif element.tag == "Asset_IPAddress":
            asset_ip_value = element.text
        elif element.tag == "timestamp":
            timestamp = element.text

# Print the extracted values (you can use these variables as needed)
print(f"Timestamp: {timestamp}")
print(f"Type: {type_value}")
print(f"Asset_Type: {asset_type_value}")
print(f"Asset_IPAddress: {asset_ip_value}")
