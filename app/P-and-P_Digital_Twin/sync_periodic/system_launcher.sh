#!/bin/bash	
echo -e '\n'
echo -e '\n'
echo "*** INSERIRE NEL CONFIG.INI FILE I SEGUENTI PARAMETRI:  "
echo "1) testbed - se umu o cnit "
echo "2) interval - numero di secondi per analizzare i flussi "	
echo "3) do_prediction - se yes or no "

mkdir -p output_tcpdump
mkdir -p attacks
mkdir -p output_Arima
mkdir -p output_pcap
echo -e '\n'
echo "*** Analizza **pcap** originale del PT e il risultato è un CSV unico che contiente tutti i dati dei flussi nella cartella output_pcap*** "
echo -e '\n'
python3 ./tcpdump_PT_flows_NEW_dic.py

do_prediction=$(python3 -c "import configparser; c=configparser.ConfigParser(); c.read('config.ini'); print(c.get('ARIMA', 'do_prediction', fallback='no'))")

if [ \"$do_prediction\" = \"yes\" ]; then
    echo "Running prediction..."
    python3 ./arima_sarima.py
else
    echo "Skipping prediction, continuing translating IP of testbed"
fi

echo -e '\n'	
echo -e "Conversione IP da indirizzi del PT a indirizzi del 5G"
python3 ./traduzione_csv_IP_testbed_NEW.py
echo -e "."
