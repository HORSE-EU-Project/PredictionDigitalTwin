from flask import Flask, request
import xml.etree.ElementTree as ET
import subprocess
import time
import os
import textwrap

app = Flask(__name__)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "Nessun file allegato", 400

    file = request.files['file']
    
    try:
        xml_content = file.read().decode('utf-8')
        root = ET.fromstring(xml_content)

        # Cerca il tipo di attacco
        attack_type = root.find(".//Type")

        # Cerca il campo Attack_IPAddress nel file XML
        #attack_ip = root.find(".//Attack_IPAddress")

        cyber_attack = root.find(".//CyberAttack")

        if attack_type is not None:
            with open("last.xml", 'w') as file:
                file.write(xml_content)
            print(xml_content)
            #script_path = "run_CNIT.sh"
            #process = subprocess.Popen(['/bin/bash', script_path])
            #print("[HORSE SAN] Input received by EM module, proceeding with Prediction and Prevention")
            print("--- CyberAttack Section Content ---")
            cyber_attack_xml_string = ET.tostring(cyber_attack, encoding='unicode')
            print(textwrap.dedent(cyber_attack_xml_string))
            #print("-----------------------------------")
            # print(f"[HORSE SAN] Started external script '{script_path}' with PID: {process.pid}")
            return f"Attack Type: {attack_type.text}", 200
            # return f"Attack_IPAddress: {attack_ip.text}, Type: {attack_type.text}", 200
        else:
            return "Campo Attack_Type non trovato", 400

    except ET.ParseError:
        return "Errore nel parsing del file XML", 400

if __name__ == '__main__':
     app.run(host='0.0.0.0')
#    app.run(host='10.19.2.22',debug=True)

