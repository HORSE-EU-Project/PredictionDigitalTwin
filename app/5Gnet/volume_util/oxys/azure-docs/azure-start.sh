echo "Logging and initializing..."
az login
az group create --name RG-Container --location eastus
az group show --name RG-Container -o table

echo "Setting up names..."
resourcegroup="RG-Container"
ContainerName="democontainer"

echo "Creating container..."
az container create \
 --resource-group $resourcegroup \
 --name $ContainerName \
 --image nginx \
 --dns-name-label $ContainerName \
 --port 80

az container show \
 --resource-group $resourcegroup \
 --name $ContainerName \
 --query "{FQDN:ipAddress.fqdn,IPAddress:ipAddress.ip,ProvisioningState:provisioningState}" \
 --out table

#az container exec --resource-group $resourcegroup --name $ContainerName 
--exec-command "/bin/bash"
