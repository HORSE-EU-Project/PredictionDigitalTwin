echo "[5G UERANSIM And Open5GS] Installing docker containers"
cd build
./dockerhub_pull.sh
echo "[HORSE] Customization for HORSE project"
cd ../customization
./install_java.sh
./build.sh
cd ..

