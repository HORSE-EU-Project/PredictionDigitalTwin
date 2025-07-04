import dpkt
import socket
from datetime import datetime, timedelta
import csv
import os
from collections import defaultdict
import configparser
import pandas as pd

# Carica il file di configurazione
config = configparser.ConfigParser()
try:
    config.read('config.ini')
except Exception as error:
    print("\n Couldn't open config.ini: ", error)

# Crea la sezione [FLOWS_DT_TRANSLATED] se non esiste
if 'FLOWS_DT_TRANSLATED' not in config.sections():
    config.add_section('FLOWS_DT_TRANSLATED')

# Crea la sezione [FLOWS_DT_ALL] se non esiste
if 'FLOWS_DT_ALL' not in config.sections():
    config.add_section('FLOWS_DT_ALL')
    
tt = datetime.now().strftime('%H_%M_%S')

# Ottieni il parametro 'interval' e altre configurazioni dal file
interval = int(config['FLOW'].get('interval', 1))  # Default 1 secondo
#   interval = 1
if interval <= 0:
    print("Errore: l'intervallo deve essere maggiore di zero.")
    exit(1)

pcap_dir_dt = config['PCAP']['pcap_dir_dt']
pcap_files = [config['PCAP_DT'][key] for key in config['PCAP_DT']]

# Crea directory di output se non esiste
output_dir = f"output_tcpdump/DT"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
    print(f"Creata la directory: {output_dir}")

# Funzione per arrotondare il timestamp all'inizio dell'intervallo
def round_timestamp_to_interval(timestamp, interval):
    return timestamp - timedelta(seconds=timestamp.second % interval, microseconds=timestamp.microsecond)

# Funzione per aggiornare i flussi per ogni intervallo, ipsrc e ipdst
def update_flow(aggregated_data, timestamp, ipsrc, ipdst, bits):
    # Arrotonda il timestamp all'inizio dell'intervallo
    interval_start = round_timestamp_to_interval(timestamp, interval)
    key = (interval_start, ipsrc, ipdst)  # Usa timestamp arrotondato, ipsrc e ipdst come chiave
    if key not in aggregated_data:
        aggregated_data[key] = {
            'total_bits': 0,
            'packet_count': 0
        }
    #else:
        #print(f"[DEBUG] Aggiunto {bits} bits per {ipsrc} -> {ipdst} all'intervallo {interval_start}")

    # Somma i bit totali e conta i pacchetti in questo intervallo
    aggregated_data[key]['total_bits'] += bits
    aggregated_data[key]['packet_count'] += 1

# Dizionario per tenere traccia dei file CSV per ciascun IP di destinazione
csv_files_per_ip = {}
writers_per_ip = {}

# Analizza i pacchetti di ciascun file PCAP
for pcap_file in pcap_files:
    # Usa il nome del file direttamente come percorso completo
    pcap_path = pcap_file.strip()
    
    print(f"Analizzando il file PCAP: {pcap_path}")
    
    # Verifica se il file esiste
    if not os.path.exists(pcap_path):
        print(f"Errore: Il file PCAP {pcap_path} non è stato trovato.")
        continue

    try:
        with open(pcap_path, 'rb') as f:
            pcap = dpkt.pcap.Reader(f)
            
            # Estrai l'IP di destinazione dal nome del file
            '''
            file_parts = pcap_file.rsplit('/', 1)[-1].rsplit('.', 1)[0]  # Prendi solo il nome del file
            id_parts = file_parts.split('_')
            ip_dst = '.'.join(id_parts[3:7])  # IP di destinazione
            '''
            # Estrai l'IP corretto dal nome del file e formatta con '_'
            file_name = os.path.basename(pcap_file)  # Prende solo il nome del file senza il path
            if "server_" in file_name:
                ip_dst = file_name.replace("server_", "").replace(".pcap", "")  # Rimuove 'server_' e '.pcap'
                ip_dst_formatted = ip_dst  # Mantiene gli underscore
                ip_dst = ip_dst_formatted.replace("_",".")
                
            else:
                print(f"[ERRORE] Nome file non conforme: {file_name}")
                continue  # Salta il file se il nome non è corretto

            #print(f"[DEBUG] IP destinazione estratto: {ip_dst_formatted}")  # Verifica che sia corretto


            # Se l'IP di destinazione non ha ancora un file CSV, creane uno
            if ip_dst not in csv_files_per_ip:
                t = datetime.now().strftime('%H_%M_%S')
                csv_filename = f"{output_dir}/flow_{ip_dst_formatted}_DT_{t}.csv"
                
                csv_file = open(csv_filename, 'w', newline='')
                writer = csv.writer(csv_file)
                writer.writerow(["ds", "ipsrc", "ipdst", "y"])

                # Aggiungi il file CSV alla sezione [FLOWS_DT_TRANSLATED] nel config
                file_index = len(csv_files_per_ip)
                config['FLOWS_DT_TRANSLATED'][f'file_{file_index}'] = csv_filename

                # Salva il file CSV e il writer per l'IP di destinazione
                csv_files_per_ip[ip_dst] = csv_file
                writers_per_ip[ip_dst] = writer

            # Per ogni file, memorizza i flussi separatamente
            aggregated_data = defaultdict(lambda: {
                'total_bits': 0,
                'packet_count': 0,
            })

            # Analizza ogni pacchetto nel file PCAP
            for timestamp, buf in pcap:
                try:
                    eth = dpkt.ethernet.Ethernet(buf)

                    # Controlla se è un pacchetto IPv4
                    if isinstance(eth.data, dpkt.ip.IP):
                        ip = eth.data
                        ipsrc = socket.inet_ntoa(ip.src)
                        ipdst = socket.inet_ntoa(ip.dst)
                        timestamp_dt = datetime.utcfromtimestamp(timestamp)

                        payload_length = ip.len - (ip.hl * 4) - (ip.data.off * 4 if hasattr(ip.data, 'off') else 0)
                        bits = payload_length * 8
                        
                        if payload_length < 0:
                            print(f"[DEBUG] ATTENZIONE! Lunghezza payload negativa per pacchetto {ipsrc} -> {ipdst}")

                        #print(f"[DEBUG] Pacchetto: {ipsrc} -> {ipdst}, dimensione: {bits} bits, timestamp: {timestamp_dt}")

                        # Filtra solo i pacchetti in cui l'IP di destinazione è uguale a 'ip_dst'
                        if ipdst == ip_dst:
                            # Aggiorna il flusso con i dati aggregati
                            update_flow(aggregated_data, timestamp_dt, ipsrc, ipdst, bits)

                except Exception as e:
                    print(f"Errore nell'analisi del pacchetto: {e}")
            
            # Scrivi i dati aggregati nel file CSV corrente per l'IP di destinazione
            writer = writers_per_ip[ip_dst]
            for (interval_start, ipsrc, ipdst), data in sorted(aggregated_data.items()):
                if data['packet_count'] > 0:
                    avg_bits_per_second = data['total_bits'] / int(interval)  # Calcola bit al secondo per la durata totale
                    #print(f"[DEBUG] Scrivendo: {interval_start}, {ipsrc}, {ipdst}, {round(avg_bits_per_second)}")
                    writer.writerow([interval_start.strftime("%Y-%m-%d %H:%M:%S"), ipsrc, ipdst, round(avg_bits_per_second)])
                    csv_file.flush()
                #else:
                    #print(f"[DEBUG] Nessun pacchetto per {ipdst} all'intervallo {interval_start}")
    except FileNotFoundError:
        print(f"Errore: Il file PCAP {pcap_path} non è stato trovato. Si continua con il prossimo file.")
        continue

# Chiudi tutti i file CSV aperti
for csv_file in csv_files_per_ip.values():
    csv_file.close()
# Chiudi i file CSV al termine dell'analisi
for ipdst, csv_file in csv_files_per_ip.items():
    print(f"[DEBUG] Chiudendo file CSV per {ipdst}")
    csv_file.close()

# Crea un CSV completo unendo tutti i CSV generati
csv_files = list(csv_files_per_ip.values())
combined_data = []

# Leggi tutti i CSV generati e aggiungi i dati a combined_data
for file in config['FLOWS_DT_TRANSLATED'].values():
    df = pd.read_csv(file)
    combined_data.append(df)

# Unisci tutti i DataFrame in uno solo
combined_df = pd.concat(combined_data)

# Ordina i dati in base al timestamp 'ds'
combined_df['ds'] = pd.to_datetime(combined_df['ds'])
combined_df.sort_values(by='ds', inplace=True)

# Salva il CSV completo ordinato cronologicamente
complete_csv_filename = f"{output_dir}/combined_flow_DT_{tt}.csv"
combined_df.to_csv(complete_csv_filename, index=False)
print(f"CSV completo creato: {complete_csv_filename}")

# Aggiungi il CSV completo alla sezione [FLOWS_DT_ALL] nel config
config['FLOWS_DT_ALL']['file_0'] = complete_csv_filename

# Salva le modifiche nel file di configurazione
try:
    with open('config.ini', 'w') as configfile:
        config.write(configfile)
    print("Configurazione aggiornata con il file CSV completo.")
except Exception as e:
    print(f"Errore nel salvataggio della configurazione: {e}")
