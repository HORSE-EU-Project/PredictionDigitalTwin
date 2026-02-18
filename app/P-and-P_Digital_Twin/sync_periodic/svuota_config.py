import configparser

# Percorso del file config.ini
config_file = 'config.ini'

# Carica il file di configurazione
config = configparser.ConfigParser()
config.read(config_file)

# Svuota i parametri specificati

if 'FLOW' in config:
    config['FLOW']['flows'] = ''

# Svuota tutte le sezioni specificate
sections_to_clear = [
    'OUTPUT_TCPDUMP_ANALYZER',
    'OUTPUT_ARIMA', 'CSV_FLOWS', 'CSV_FLOWS_TRANSLATED'
]

for section in sections_to_clear:
    if section in config:
        config[section].clear()

# Salva le modifiche nel file di configurazione
with open(config_file, 'w') as configfile:
    config.write(configfile)

print("Config.ini aggiornato con parametri svuotati.")
