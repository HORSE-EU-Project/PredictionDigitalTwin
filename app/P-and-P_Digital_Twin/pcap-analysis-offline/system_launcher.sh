#!/bin/bash	
echo -e '\n'
echo "*** Svuotamento del file config.ini ***"
python3 ./svuota_config.py
echo -e '\n'
echo "*** INSERIRE NEL CONFIG.INI FILE I SEGUENTI PARAMETRI:  "
echo "1) testbed - se umu o cnit "
echo "2) interval - numero di secondi per analizzare i flussi "	
mkdir -p output_tcpdump
mkdir -p attacks
mkdir -p output_Arima
mkdir -p output_pcap
echo -e '\n'
echo "*** Analizza **pcap** originale del PT e il risultato è un CSV unico che contiente tutti i dati dei flussi nella cartella output_pcap*** "
echo -e '\n'
python3 ./tcpdump_PT_flows_NEW.py
read -p "Do you want to make prediction also? Y or N: " answer
if [ "$answer" = "Y" ] || [ "$answer" = "y" ]; then
    echo "Running prediction..."
	#echo "*** Execution of prediction script using *Arima or Sarima* to predict values of the next bits transmitted ***"
	#echo -e '\n'
	python3 ./prediction_flows_NEW.py
else
    echo "Skipping prediction, continuing translating IP of testbed"
fi
echo -e '\n'	
echo -e "Conversione IP da indirizzi del PT a indirizzi del 5G"
python3 ./traduzione_csv_IP_testbed_NEW.py
echo -e "."
