echo "Logging and initializing..."
az login
az group create --name RG-Container --location eastus
az group show --name RG-Container -o table
#az acr login --name granelli

echo "Setting up names..."
resourcegroup="RG-Container"
ContainerName="oxys-reflector"

echo "Creating container..."
az container create \
 --resource-group $resourcegroup \
 --name $ContainerName \
 --image granelli.azurecr.io/oxys-reflector:v1 \
 --dns-name-label $ContainerName \
 --ip-address Public \
 --registry-login-server granelli.azurecr.io \
 --registry-username granelli \
 --registry-password cDLtVpPMVWZLZC8/uGkcApN9M4Qdb2yU \
 --command-line "python3 webserver.py 80 &" \
 --ports 861 862 20000 20001 20002

az container show \
 --resource-group $resourcegroup \
 --name $ContainerName \
 --query "{FQDN:ipAddress.fqdn,IPAddress:ipAddress.ip,ProvisioningState:provisioningState}" \
 --out table

az container exec --resource-group $resourcegroup --name $ContainerName --exec-command "/bin/bash"
