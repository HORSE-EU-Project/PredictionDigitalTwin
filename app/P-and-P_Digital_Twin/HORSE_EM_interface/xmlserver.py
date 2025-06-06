from flask import Flask, request
import xml.etree.ElementTree as ET

app = Flask(__name__)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "Nessun file allegato", 400

    file = request.files['file']
    
    try:
        xml_content = file.read().decode('utf-8')
        root = ET.fromstring(xml_content)

        parsed_data = {}
        for elem in root.iter():
            parsed_data[elem.tag] = elem.text

        return f"Dati XML:\n{parsed_data}", 200

    except ET.ParseError:
        return "Errore nel parsing del file XML", 400

if __name__ == '__main__':
    app.run(debug=True)

