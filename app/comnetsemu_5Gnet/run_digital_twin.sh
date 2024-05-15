echo "[\e[1;32m RYU \e[0m] *** Running RYU controller"
./scripts/run_ryu.sh &
echo "[\e[1;32m NDT \e[0m] *** Running Digital Twin Engine (Comnetsemu)"
sudo python3 DT_v0.7.py
