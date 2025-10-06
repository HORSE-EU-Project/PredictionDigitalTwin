import os

# Get the value of 'HOME' or default to '/tmp' if it's not set
home_directory = os.environ.get('TESTBED', 'UMU')
print(f"The TESTBED is: {home_directory}")

# Get the value of 'CUSTOM_VAR' or default to None
custom_value = os.environ.get('CUSTOM_VAR')
print(f"The CUSTOM_VAR value is: {custom_value}")
