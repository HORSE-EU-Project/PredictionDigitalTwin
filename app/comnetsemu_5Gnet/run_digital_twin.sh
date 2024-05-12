echo "*** Running RYU controller"
./scripts/run_ryu.sh &
echo "*** Running Digital Twin Engine (Comnetsemu)"
sudo python3 DT_v0.7.py
