#!/bin/bash	
#echo "*** Clearing file config.ini ***"
# python3 ./svuota_config.py
# echo -e '\n'
# echo "*** INSERT THE FOLLOWING PARAMETERS IN THE CONFIG.INI FILE:  "
# echo "1) testbed - umu, upc or cnit "
# echo "2) interval - pcap analysis window "
# echo "3) pcap_file - pcap filename"	
mkdir -p output_tcpdump
mkdir -p attacks
mkdir -p output_Arima
mkdir -p output_pcap
echo -e '\n'
echo "[HORSE P&P NDT] *** Analysis of the original **pcap** file from PT and output to a CSV file containing flows data in folder output_pcap*** "
python3 -W ignore ./tcpdump_PT_flows_NEW.py
echo
echo "[HORSE P&P NDT] Running prediction..."
echo "[HORSE P&P NDT] *** Execution of prediction script using *Arima or Sarima* to predict values of the next bits transmitted ***"
python3 -W ignore ./prediction_flows_NEW.py
echo
echo -e "[HORSE P&P NDT] Converting IP addresses from PT to NDT"
python3 -W ignore ./traduzione_csv_IP_testbed_NEW.py
echo -e "."
