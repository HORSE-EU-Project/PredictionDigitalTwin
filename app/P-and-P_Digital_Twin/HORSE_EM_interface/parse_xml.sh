#!/bin/bash

# Controlla che il file sia stato fornito
if [ -z "$1" ]; then
    echo "❗ Usa: $0 <file.xml>"
    exit 1
fi

# Controlla che il file esista
if [ ! -f "$1" ]; then
    echo "❗ Il file '$1' non esiste."
    exit 2
fi

# Estrai i contenuti dei tag <Type> e <Attack_IPAddress>
types=$(grep -oP '(?<=<Type>).*?(?=</Type>)' "$1")
ips=$(grep -oP '(?<=<Attack_IPAddress>).*?(?=</Attack_IPAddress>)' "$1")

# Stampa i risultati
echo "📄 Risultati trovati:"
paste <(echo "$types") <(echo "$ips") | while IFS=$'\t' read -r type ip; do
    echo "🔹 Type: $type | Attack_IPAddress: $ip"
done
