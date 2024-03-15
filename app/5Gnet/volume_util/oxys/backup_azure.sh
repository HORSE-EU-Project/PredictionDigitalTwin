#az acr create --resource-group $resourcegroup --name granelli --sku Basic
#az acr login --name granelli
docker tag oxys-reflector granelli.azurecr.io/oxys-reflector:v1
docker push granelli.azurecr.io/oxys-reflector:v1

#credentials
#username: granelli
#password: cDLtVpPMVWZLZC8/uGkcApN9M4Qdb2yU
# https://portal.azure.com/#@unitrento365.onmicrosoft.com/resource/subscriptions/9ee4471b-26eb-4fb7-9d18-64b11600d332/resourceGroups/RG-Container/providers/Microsoft.ContainerRegistry/registries/granelli/accessKey
