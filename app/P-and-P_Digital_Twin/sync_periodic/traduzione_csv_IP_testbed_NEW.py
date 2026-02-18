import os
import configparser
import csv
import json
import time

def map_ip(ip, mapping):
    """Restituisce l'IP mappato o l'IP originale se non trovato."""
    return mapping.get(ip, ip)

def log_error(message):
    """Scrive un messaggio di errore nel file di log."""
    output_dir = "csv_translated"
    os.makedirs(output_dir, exist_ok=True)
    with open("csv_translated/translation_errors.log", "w") as log_file:
        log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

def translate_csv(input_file, output_file, ip_map):
    """Traduci gli IP sorgente e destinazione in un file CSV."""
    try:
        with open(input_file, 'r') as infile, open(output_file, 'w', newline='') as outfile:
            reader = csv.DictReader(infile)
            fieldnames = reader.fieldnames + ['ipsrc_original', 'ipdst_original']

            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()

            for row in reader:
                row['ipsrc_original'] = row['ipsrc']
                row['ipdst_original'] = row['ipdst']
                row['ipsrc'] = map_ip(row['ipsrc'], ip_map)
                row['ipdst'] = map_ip(row['ipdst'], ip_map)
                writer.writerow(row)
        return True
    except Exception as e:
        log_error(f"Errore durante la traduzione del file {input_file}: {e}")
        return False

def translate_and_update_config(config_path):
    config = configparser.ConfigParser()

    try:
        config.read(config_path)

        if 'PCAP' not in config or 'testbed' not in config['PCAP']:
            log_error("Errore: Sezione [PCAP] o chiave 'testbed' non trovata in config.ini.")
            return

        if 'CSV_FLOWS' not in config or 'detailed_file' not in config['CSV_FLOWS']:
            log_error("Errore: Sezione [CSV_FLOWS] o chiave 'detailed_file' mancante in config.ini.")
            return

        testbed = config['PCAP']['testbed'].strip().lower()

        with open("ip_mapping.json", "r") as file:
            mappings = json.load(file)

        if testbed not in mappings:
            log_error(f"Errore: Testbed '{testbed}' non valido o non presente in ip_mapping.json.")
            return

        ip_map = mappings[testbed]

        input_file = config['CSV_FLOWS']['detailed_file']
        base_name = os.path.basename(input_file)
        translated_name = base_name.replace(".csv", "_translated.csv")

        output_dir = "csv_translated"
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, translated_name)

        success = translate_csv(input_file, output_file, ip_map)

        if success:
            if 'CSV_FLOWS_TRANSLATED' not in config:
                config.add_section('CSV_FLOWS_TRANSLATED')
            config['CSV_FLOWS_TRANSLATED']['detailed_file'] = output_file

            with open(config_path, 'w', encoding='utf-8') as configfile:
                config.write(configfile)
            print(f"Traduzione completata: {input_file} -> {output_file}")
        else:
            print("ERRORE: traduzione fallita")

    except Exception as e:
        log_error(f"Errore durante la traduzione: {e}")


if __name__ == "__main__":
    config_path = "config.ini"
    translate_and_update_config(config_path)
    print("Tutte le traduzioni completate.")