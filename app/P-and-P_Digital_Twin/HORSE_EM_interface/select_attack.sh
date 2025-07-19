#!/bin/bash

# Esegui run.sh e salva la prima riga di output
output=$(./parse_xml.sh last.xml | head -n 2)

# Estrai i dati
TYPE=$(echo "$output" | grep -oP 'Type: \K[^|]+')
IP=$(echo "$output" | grep -oP 'Attack_IPAddress: \K[\d\.]+')

# Rimuovi eventuali spazi
TYPE=$(echo "$TYPE" | xargs)
IP=$(echo "$IP" | xargs)

# Verifica e stampa messaggi in base al tipo di attacco
case "$TYPE" in
    "Network Denial of Service")
        echo "🛡️ Attacco DoS rilevato! IP sorgente: $IP"
        ;;
    "SQL Injection")
        echo "🧬 Attacco SQL rilevato da $IP"
        ;;
    "Phishing")
        echo "🎣 Rilevato phishing da $IP"
        ;;
    *)
        echo "⚠️ Tipo di attacco sconosciuto: '$TYPE' proveniente da $IP"
        ;;
esac
