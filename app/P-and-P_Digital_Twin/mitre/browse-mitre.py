import requests
import json

# Inserisci qui il nome (o parte del nome) dell'attacco da ricercare.
ATTACK_NAME = "Denial of service"  # Puoi modificare il valore o sostituirlo con un input dinamico

# URL del file JSON del MITRE ATT&CK (Enterprise ATT&CK) in formato STIX
MITRE_URL = "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json"

def fetch_mitre_data(url):
    """Recupera i dati MITRE ATT&CK dal repository online."""
    try:
        print("Recupero dei dati MITRE ATT&CK in corso...")
        response = requests.get(url)
        response.raise_for_status()
        print("Dati recuperati con successo.\n")
        return response.json()
    except Exception as e:
        print("Errore nel recupero dei dati: ", e)
        return None

def search_attack(data, attack_name):
    """
    Cerca all'interno dei dati MITRE ATT&CK tutti gli attack-pattern che
    contengono 'attack_name' nel campo 'name' (ricerca case-insensitive).
    """
    matches = []
    for obj in data.get("objects", []):
        if obj.get("type") == "attack-pattern":
            name = obj.get("name", "")
            if attack_name.lower() in name.lower():
                matches.append(obj)
    return matches

def print_attack_info(attacks):
    """Stampa informazioni chiave sugli attacchi trovati."""
    if not attacks:
        print(f"Nessun attack-pattern trovato che corrisponda a '{ATTACK_NAME}'.")
        return

    print(f"Trovati {len(attacks)} attack-pattern che corrispondono a '{ATTACK_NAME}':\n")
    for attack in attacks:
        print("-" * 80)
        print("Nome:", attack.get("name"))
        # Estrae l'External ID (es. il T-number) dall'elenco delle referenze esterne, se presente.
        external_id = "N/A"
        if "external_references" in attack:
            for ref in attack["external_references"]:
                if "attack.mitre.org" in ref.get("url", ""):
                    external_id = ref.get("external_id", external_id)
                    break
        print("External ID:", external_id)
        print("Descrizione:", attack.get("description", "Nessuna descrizione disponibile"))
    print("-" * 80)

def main():
    data = fetch_mitre_data(MITRE_URL)
    if not data:
        return

    matching_attacks = search_attack(data, ATTACK_NAME)
    print_attack_info(matching_attacks)

if __name__ == "__main__":
    main()

