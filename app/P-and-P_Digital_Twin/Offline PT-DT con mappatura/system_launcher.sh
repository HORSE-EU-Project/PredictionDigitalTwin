#!/bin/bash	
echo -e '\n'
echo "*** Svuotamento del file config.ini ***"
python3 ./svuota_config.py
echo -e '\n'
echo "*** INSERIRE NEL CONFIG.INI FILE I SEGUENTI PARAMETRI:  "
echo "1) pcap_file - cioè nome del pcap con relativo percorso situato all'interno della cartella **pcap**  "
echo "2) testbed - se umu o cnit "
echo "3) interval - numero di secondi per analizzare i flussi "
echo -e '\n'
sleep 30	
mkdir -p output_tcpdump
mkdir -p attacks
mkdir -p output_Arima
mkdir -p output_pcap
mkdir -p Ryu
mkdir -p output_DT
echo -e '\n'
echo "*** Analizza **pcap** originale del PT e i risultati salvati nella cartella **output_pcap** con i relativi CSV per ogni flusso dato dal IP_DEST e info sui flussi disponibili *** "
echo -e '\n'
python3 ./tcpdump_PT_flows.py
#echo -e '\n'
#echo "*** Execution of prediction script using *Arima or Sarima* to predict values of the next bits transmitted ***"
#echo -e '\n'
#python3 ./prediction_flows.py
#echo -e '\n'	
#echo -e '*** Check directory output_Arima to see figures and values predicted - files final_combined_traffic_flow_<id_dest>__<timestamp>.csv needed for COMPARISON***'
echo -e '\n'	
echo -e "*** Conversione IP da indirizzi del PT a indirizzi del 5G (in questo esempio si mappano indirizzi appartenenti a una LAN di Mininet) ***"
python3 ./traduzione_csv_IP_testbed.py
sudo mn -c
sleep 5	
echo -e '\n'	
echo -e '*** Avvio del DIGITAL TWIN e i file pcap del DT salvati nella cartella **pcap/<timestamp>/....***'
echo -e '\n'	
sudo /usr/bin/python3 ./launcher_DT_flows_no_seg.py 
echo -e '\n'	
echo -e "*** Analizza **pcap** del DT e salva i CSV in **output_tcpdump/DT/... con nome flusso e timestamp *** \n"
python3 ./tcpdump_DT_flows.py
echo -e '\n'	
echo -e '*** Conversione IP da 5G a PT ***'
python3 ./traduzione_csv_IP_to_original.py
echo -e '\n'	
python3 ./compare_PT_DT_flows_new.py	
echo -e '*** Confronta CSV di ogni flusso con i valori del PT prima della conversione e i valori del DT dopo la conversione in IP originali. ***\n'
echo -e '*** Risultati grafici nella cartella **output_DT/confroto_traffico_<ts>** \n'