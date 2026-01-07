export demo=1
cd sync_and_predict/
./run_PT_to_NDT_v3.sh
cd ..
cd PcapNinja/
./analyze_pcap_CNIT.sh
cd ..

