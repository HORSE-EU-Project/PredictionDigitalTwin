echo "Setting up names..."
resourcegroup="RG-Container"
ContainerName="democontainer"

echo "Stopping container..."
az container stop \
 --resource-group $resourcegroup \
 --name $ContainerName

echo "...DONE"
az container show \
 --resource-group $resourcegroup \
 --name $ContainerName \
 --out table

echo "Deleting container..."
az container delete \
 --resource-group $resourcegroup \
 --name $ContainerName
