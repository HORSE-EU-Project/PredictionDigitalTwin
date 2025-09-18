clear
figlet "HORSE P&P NDT"
figlet -f ./scripts/smkeyboard.flf "DEMO#4"
echo
# echo "[HORSE SAN] Checking data consistency"
sleep 5
cd data_consistency
./check_hash_UMU.sh input.pcap
