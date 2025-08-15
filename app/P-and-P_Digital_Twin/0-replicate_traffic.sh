echo "[HORSE SAN] Transferring pcap file"
docker cp dns.pcap upf_cld:/open5gs
./cmd_container.sh upf_cld "timeout 1m tcpdump -i ogstun -w capture.pcap &"
./cmd_container.sh upf_cld "capture_pid=$!"
./cmd_container.sh upf_cld "tcpreplay --intf1=ogstun dns.pcap"
echo "[HORSE SAN] Playback completed, waiting for acquisition to finish"
./cmd_container.sh upf_cld "wait $capture_pid"
