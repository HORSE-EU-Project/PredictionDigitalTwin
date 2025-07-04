import os
import configparser
import csv
import json
import time

# Leggi la mappatura degli IP da un file JSON
with open("ip_mapping_reverse.json", "r") as file:
    mappings = json.load(file)

def map_ip(ip, mapping):
    """Restituisce l'IP mappato o l'IP originale se non trovato."""
    return mapping.get(ip, ip)

def translate_csv(input_file, output_file, ip_map):
    """Traduci gli IP sorgente e destinazione in un file CSV."""
    try:
        with open(input_file, 'r') as infile, open(output_file, 'w', newline='') as outfile:
            reader = csv.DictReader(infile)
            fieldnames = reader.fieldnames

            # Scrivi l'intestazione nel file di output
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()

            for row in reader:
                # Traduci gli IP sorgente e destinazione
                row['ipsrc'] = map_ip(row['ipsrc'], ip_map)
                row['ipdst'] = map_ip(row['ipdst'], ip_map)
                writer.writerow(row)
        return True  # Indica che la traduzione è andata a buon fine     
    except Exception as e:
        log_error(f"Errore durante la traduzione del file {input_file}: {e}")
        return False 

def generate_translated_filename(input_file, ip_map):
    """Genera il nome del file tradotto e restituisce il percorso."""
    base_name = os.path.basename(input_file)
    parts = base_name.split("_DT_")
    
    '''
    ip_section = parts[0].split("_")[-1]
    new_ip = map_ip(ip_section.replace("_", "."), ip_map).replace(".", "_")
    parts[0] = parts[0].replace(ip_section, new_ip)
    translated_name = "___".join(parts)
    output_dir = "csv_translated_reverse"
    os.makedirs(output_dir, exist_ok=True)
    return os.path.join("csv_translated_reverse", translated_name)
    '''
    try:
        # **Legge il primo valore di 'ipdst' dal file CSV**
        with open(input_file, 'r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            first_row = next(reader, None)  # Legge solo la prima riga

            if not first_row or 'ipdst' not in first_row:
                log_error(f"❌ Errore: impossibile determinare l'IP di destinazione in {input_file}")
                return None

            translated_ip_dst = first_row['ipdst']
            original_ip_dst = map_ip(translated_ip_dst, ip_map).replace(".", "_")

        # **Divide il nome in segmenti per individuare la posizione dell'IP**
        name_parts = parts[0].split("_")  
        
        # **Trova la posizione esatta dell'IP (Ultimi 4 segmenti)**
        ip_start_index = max(0, len(name_parts) - 4)  
        
        # **Sostituisce SOLO l'IP di destinazione, mantenendo il resto del nome invariato**
        old_ip = "_".join(name_parts[ip_start_index:])

        name_parts[ip_start_index:] = original_ip_dst.split("_")
        
        # **Costruisce il nome corretto eliminando numeri extra prima di `_DT_`**
        standardized_name = "_".join(name_parts[:5]) + "_" + "_".join(name_parts[5:])  

        # **Mantiene `_DT_<timestamp>.csv` invariato**
        translated_name = standardized_name + "DT_" + parts[1]

        # **Crea la cartella di output se non esiste**
        output_dir = "csv_translated_reverse"
        os.makedirs(output_dir, exist_ok=True)
        
        return os.path.join(output_dir, translated_name)

    except Exception as e:
        log_error(f"Errore durante la generazione del nome file per {input_file}: {e}")
        return None
        
def log_error(message):
    """Scrivi un messaggio di errore nel file di log."""
    output_dir = "csv_translated"
    os.makedirs(output_dir, exist_ok=True)
    with open("csv_translated/translation_errors.log", "a") as log_file:
        log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

def translate_and_update_config(config_path):
    """Gestisce la traduzione del CSV e aggiorna il file di configurazione."""
    config = configparser.ConfigParser()
    
    try:
        config.read(config_path)
        if 'PCAP' not in config or 'testbed' not in config['PCAP']:
            log_error("Errore: Sezione [PCAP] o chiave 'testbed' non trovata in config.ini.")
            return

        testbed = config['PCAP']['testbed'].strip().lower()

        if testbed not in mappings:
            log_error(f"Errore: Testbed '{testbed}' non valido o non presente in ip_mapping.json.")
            return
        if 'FLOWS_DT_IP_ORIGINAL' not in config:
            config.add_section('FLOWS_DT_IP_ORIGINAL')
       
        ip_map = mappings[testbed]

        # Processa tutti i file elencati in [FLOWS]
        for key in sorted(config['FLOWS_DT_TRANSLATED'].keys()):
            if not key.startswith("file_"):
                continue  # Ignora chiavi non conformi

            input_file = config['FLOWS_DT_TRANSLATED'][key]

            if not ip_map:
                log_error(f"Errore: Nessuna mappatura trovata per {testbed}")
                continue

            output_file = generate_translated_filename(input_file, ip_map)
            if not output_file:
                continue

            success = translate_csv(input_file, output_file, ip_map)
            
            if success:
                config['FLOWS_DT_IP_ORIGINAL'][key] = output_file
                print(f"Traduzione completata: {input_file} -> {output_file}")

        # Scrive le modifiche nel file di configurazione
        with open(config_path, 'w', encoding='utf-8') as configfile:
            config.write(configfile)

    except KeyError as e:
        log_error(f"Chiave mancante nel file di configurazione: {e}")
    except Exception as e:
        log_error(f"Errore durante la traduzione: {e}")

if __name__ == "__main__":
    config_path = "config.ini"
    translate_and_update_config(config_path)
    print("Tutte le traduzioni completate.")