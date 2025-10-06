import configparser

# Percorso del file config.ini
config_file = 'config.ini'

# Carica il file di configurazione
config = configparser.ConfigParser()
config.read(config_file)

# Svuota i parametri specificati
if 'PCAP' in config:
    config['PCAP']['pcap_dir_dt'] = ''

if 'FLOW' in config:
    config['FLOW']['flows'] = ''

# Svuota tutte le sezioni specificate
sections_to_clear = [
    'FLOWS', 'PCAP_DT', 'OUTPUT_TCPDUMP_ANALYZER',
    'OUTPUT_ARIMA', 'OUTPUT_ARIMA_ALL',
    'OUTPUT_DT', 'FLOWS_DT', 'FLOWS_DT_ALL', 'FLOWS_TRANSLATED', 'FLOWS_DT_TRANSLATED', 'FLOWS_DT_IP_ORIGINAL', 'CSV_FLOWS', 'CSV_FLOWS_TRANSLATED'
]

for section in sections_to_clear:
    if section in config:
        config[section].clear()

# Salva le modifiche nel file di configurazione
with open(config_file, 'w') as configfile:
    config.write(configfile)

print("Config.ini aggiornato con parametri svuotati.")
