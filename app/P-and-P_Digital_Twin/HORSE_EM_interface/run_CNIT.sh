cd ../sync_and_predict/
./run_PT_to_NDT.sh
cd ../PcapNinja
./analyze_pcap_CNIT.sh
cd ..
python3 HORSE_dashboard/update_senderv2.py box3 green "Message to DTE sent"
