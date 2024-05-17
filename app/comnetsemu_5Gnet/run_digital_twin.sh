echo "[\e[1;32m sFlow \e[0m] *** Running sFlow"
./sflow-rt/start.sh &
sleep 5
echo "[\e[1;32m RYU \e[0m] *** Running RYU controller"
./scripts/run_ryu.sh &
sleep 5
echo "[\e[1;32m NDT \e[0m] *** Running Digital Twin Engine (Comnetsemu)"
sudo python3 DT_v0.8.py
