import yaml

with open('example.yaml', 'r') as file:
    data = yaml.safe_load(file)

print(data)

# Output:
# {'example': 'data'}

