#echo "[ NTFY ] *** Running NTFY"
#./customization/run_ntfy.sh
echo "[ sFlow ] *** Running sFlow"
./sflow-rt/start.sh &
sleep 5
echo "[ RYU ] *** Running RYU controller"
./scripts/run_ryu.sh &
sleep 5
# echo "[ DETECT ] *** Running detection script"
# python3 ./scripts/detect_elephants.py &
echo "[ EM ] *** Running input interface with Early Modeling"
python3 ./scripts/EM-interface.py &
echo "[ NDT ] *** Running Digital Twin Engine (Comnetsemu)"
sudo python3 DT_v0.9.py
