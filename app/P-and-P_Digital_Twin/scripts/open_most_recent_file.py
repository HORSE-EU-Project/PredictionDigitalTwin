import glob
import os

# Specify the folder path and the desired prefix
folder_path = '../log/input'
prefix = 'input'  # Replace with your actual prefix

# Get a list of files matching the prefix
file_list = glob.glob(os.path.join(folder_path, f"{prefix}*"))

# Find the latest (most recent) file
latest_file = max(file_list, key=os.path.getctime)

# Now you can open or process the latest file as needed
print(f"Latest file: {latest_file}")
