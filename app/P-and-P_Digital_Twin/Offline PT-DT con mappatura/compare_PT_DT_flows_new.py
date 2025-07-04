import pandas as pd
import matplotlib.pyplot as plt
import configparser
import os
import re
from datetime import datetime

# Carica il file di configurazione
config = configparser.ConfigParser()
config.read('config.ini')

# Recupera i file di traffico PT e DT
flows_pt = {key: value for key, value in config['FLOWS'].items()} #prima della traduzione nella cartella *output_pcap*, quelli tradotti stanno in FLOWS_TRANSLATED
flows_dt = {key: value for key, value in config['FLOWS_DT_IP_ORIGINAL'].items()} #flows dopo la traduzione (prima della traduzione è flows_dt_translated), quelli che stanno nella cartella *csv_translated_reverse*

# Crea una cartella per salvare i grafici di confronto
timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
output_directory = os.path.join('output_DT', f"confronto_traffico_{timestamp}")

# Crea la directory di output se non esiste
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

# Funzione per estrarre l'ipdest dal nome del file
def extract_ipdest_from_filename(file_path):
    match = re.search(r'flow_(\d+_\d+_\d+_\d+)_DT', file_path) or re.search(r'traffic_flow_(\d+_\d+_\d+_\d+)', file_path)
    if match:
        return match.group(1)
    return None

# Associa i file PT e DT in base all'ipdest estratto dal nome del file
pt_by_ipdest = {extract_ipdest_from_filename(v): v for k, v in flows_pt.items() if extract_ipdest_from_filename(v)}
dt_by_ipdest = {extract_ipdest_from_filename(v): v for k, v in flows_dt.items() if extract_ipdest_from_filename(v)}

print(f"[DEBUG] Associazione PT per ipdest: {pt_by_ipdest}")
print(f"[DEBUG] Associazione DT per ipdest: {dt_by_ipdest}")

# Funzione per caricare e sincronizzare i file
def load_and_sync_files(file_pt, file_dt):
    print(f"[DEBUG] Caricamento file PT: {file_pt}")
    print(f"[DEBUG] Caricamento file DT: {file_dt}")

    # Carica i file CSV
    df_pt = pd.read_csv(file_pt)
    df_dt = pd.read_csv(file_dt)

    # Rimuove righe con valori NaN
    df_pt.dropna(inplace=True)
    df_dt.dropna(inplace=True)

    # Verifica se i dataframe sono vuoti
    if df_pt.empty or df_dt.empty:
        print(f"[DEBUG] Uno dei file è vuoto: PT ({len(df_pt)} righe), DT ({len(df_dt)} righe).")
        return None, None

    # Converte 'ds' in datetime
    df_pt['ds'] = pd.to_datetime(df_pt['ds'])
    df_dt['ds'] = pd.to_datetime(df_dt['ds'])

    # **Allinea il DT al timestamp del PT**
    min_len = min(len(df_pt), len(df_dt))  # Trova il numero di righe minore
    df_pt = df_pt.iloc[:min_len].copy()  # Taglia il PT se necessario
    df_dt = df_dt.iloc[:min_len].copy()  # Taglia il DT alla lunghezza del PT
    df_dt['ds'] = df_pt['ds'].values  # **Forza il timestamp del PT nel DT** --- come timestamp usare secondi invece dell'orario completo

    # Ordina i dati in ordine cronologico
    df_pt.sort_values(by='ds', inplace=True)
    df_dt.sort_values(by='ds', inplace=True)

    # Imposta 'ds' come indice per entrambi i dataframe
    df_pt.set_index('ds', inplace=True)
    df_dt.set_index('ds', inplace=True)

    return df_pt, df_dt

# Confronta i file e crea grafici per ciascun IP di destinazione corrispondente
for ipdest in pt_by_ipdest.keys():
    if ipdest in dt_by_ipdest:
        file_pt = pt_by_ipdest[ipdest]
        file_dt = dt_by_ipdest[ipdest]

        # Controllo se i file esistono
        if not os.path.exists(file_pt) or not os.path.exists(file_dt):
            print(f"[DEBUG] File non trovato: {file_pt} o {file_dt}")
            continue

        # Carica, pulisci e sincronizza i file
        df_pt, df_dt = load_and_sync_files(file_pt, file_dt)

        # Verifica se i dataframe sono validi
        if df_pt is None or df_dt is None:
            print(f"[DEBUG] Salto il confronto per ipdest {ipdest} poiché uno dei file è vuoto o senza timestamp comuni.")
            continue

        # Crea il grafico sovrapposto
        plt.figure(figsize=(15, 6))

        # Linea PT (blu)
        plt.plot(df_pt.index, df_pt['y'], label=f'Traffico PT {ipdest}', color='blue')

        # Linea DT (rosso tratteggiato)
        plt.plot(df_dt.index, df_dt['y'], label=f'Traffico DT {ipdest}', color='red', linestyle='--')

        # Titolo e assi
        plt.xlabel('Timestamp', fontsize=12)
        plt.ylabel('Bitrate (bps)', fontsize=12)
        plt.title(f'Confronto Traffico PT vs DT per {ipdest}', fontsize=14)
        plt.legend()
        plt.grid()

        # Salva il grafico
        output_file = os.path.join(output_directory, f"confronto_{ipdest}.png")
        plt.savefig(output_file)

        print(f"[DEBUG] Grafico di confronto salvato: {output_file}")

        # Chiudi il grafico per liberare memoria
        plt.clf()
        plt.close()

print(f"[DEBUG] Grafici salvati nella cartella: {output_directory}")