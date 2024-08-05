import os, sys, json, base64, glob
import time
import requests
from pathlib import Path
import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
from subprocess import PIPE, Popen
from configparser import ConfigParser
import xml.etree.ElementTree as ET
# --------------------------------------------------------------------------------

# Some definitions
def cmdline(command):
    process = Popen(
        args=command,
        stdout=PIPE,
        shell=True
    )
    return

# Session State variables:
state = st.session_state
if 'API_APP' not in state:
    state.API_APP = None
if 'API_CHECKED' not in state:
    state.API_CHECKED=False
if 'SFLOW_ON' not in state:
    state.SFLOW_ON=True
if 'PREDICTION_ON' not in state:
    state.PREDICTION_ON=False

# --------------------------------------------------------------------------------

# NOTE: Design point... only main() is allowed to mutate state. All supporting functions should not mutate state.
def main():
    st.title('HORSE Digital Twin - First Demo')

    config_object = ConfigParser()
    config_object.read("config.ini")
    mininet_config = config_object["MININET_SERVER"]
    API_HOST=mininet_config["ipaddr"]
    API_PORT=int(mininet_config["port"])
    API_BASE_URL=f'http://{API_HOST}:{API_PORT}'

    topology_file = st.file_uploader("Upload YAML Topology File",type=['yaml'])
    if topology_file is not None:
        file_details = {"FileName":topology_file.name,"FileType":topology_file.type}
        st.write(file_details)
        #with open(os.path.join("tempDir",topology_file.name),"wb") as f: 
        with open(os.path.join("tempDir","input.yaml"),"wb") as f:
            f.write(topology_file.getbuffer())         
        st.success("File Saved")
        cmdline("cd ../yaml-parser/ ; python3 parse_yaml.py ../GUI/tempDir/input.yaml ; mv output.py ../GUI/tempDir/output.py ; cd ../GUI")
        st.success("Topology converted from YAML")

    st.divider() 

    st.header("Digital Twin Topology")
    st.image("../HORSE_data/HORSE-DDoS-DNS-simp.png",width=600)
    
    st.divider()

    # Print input and output files
    a1, a2 = st.columns([1,1])

    with a1:
        if st.button('Input interface:'):
            folder_path = '../scripts/uploads'
            prefix = 'EM'
            file_list = glob.glob(os.path.join(folder_path, f"{prefix}*"))
            latest_file = max(file_list, key=os.path.getctime)
            #print(f"Latest file: {latest_file}")
            with open(latest_file, 'r') as file:
                data = file.read()
                st.code(data, language='python')
    with a2:
        if st.button('Received EM command:'):
            folder_path = '../scripts/uploads'
            prefix = 'uploaded'
            file_list = glob.glob(os.path.join(folder_path, f"{prefix}*"))
            latest_file = max(file_list, key=os.path.getctime)
            tree = ET.parse(latest_file)
            root = tree.getroot()
            # Define the tags you want to extract
            tags_to_extract = ["timestamp", "Type", "Asset_Type", "Asset_IPAddress"]
            # Initialize variables to store the extracted values
            timestamp = None
            type_value = None
            asset_type_value = None
            asset_ip_value = None
            # Iterate through the elements and extract values for specified tags
            for element in root.iter():
                if element.tag in tags_to_extract and element.text:
                    if element.tag == "Type":
                        type_value = element.text
                    elif element.tag == "Asset_Type":
                        asset_type_value = element.text
                    elif element.tag == "Asset_IPAddress":
                        asset_ip_value = element.text
                    elif element.tag == "timestamp":
                        timestamp = element.text
            # Print the extracted values (you can use these variables as needed)
            st.write("Timestamp:", timestamp)
            st.write("Type:", type_value)
            st.write("Asset_Type:", asset_type_value)
            st.write("Asset_IPAddress:", asset_ip_value)

    # RUN Digital Twin commands
    st.header("Digital Twin Commands")

    col1, col2 = st.columns([1,1])

    with col1:
        if st.button('Run hping'):
            cmdline('cd ../scenarios ; ./run_hping.sh ; cd ../GUI')
        if st.button('Flooding attack'):
            cmdline('cd ../scenarios ; ./flood.sh ; cd ../GUI')
        if st.button('Dump traffic'):
            cmdline('cd ../scenarios ; ./dump_traffic.sh ; cd ../GUI')

    with col2:
        if st.button('Run iperf server (Internet)'):
            cmdline('cd ../scenarios ; ./run_iperf_server.sh ; cd ../GUI')
        if st.button('Run iperf client (UE)'):
            cmdline('cd ../scenarios ; ./run_iperf_client.sh ; cd ../GUI')
        if st.button('Run prediction scenario'):
            cmdline('cd ../scenarios ; ./scenario1.sh ; cd ../GUI')

    st.divider()

    # Interacting with Mininet REST API
    st.header('Digital Twin Dashboard')
    
    if not state.API_CHECKED:
        st.write('To check the Digital Twin REST API, click the button below.')
        if st.button('🚀 Verify API'):
            requests.get(f'http://{API_HOST}:8000')
            state.API_CHECKED = True

    if state.API_CHECKED:
        message = {}
        c1, c2, c3, _ = st.columns([1,1,1,1])
        with c1:
            if st.button('👋 Hello'):
                resp = requests.get(f'http://{API_HOST}:8000')
                message = json.loads(resp.content)
        with c2:
            st.json(message)
        with c3:
            if st.button('🔥 Close API'): 
                state.API_CHECKED = False

    d1, d2, _ = st.columns([1,1,1])

    with d1:
       if st.button('🔥 sFlow charts'):
           state.SFLOW_ON = True
    with d2:
       if st.button('🔥 hide charts'):
           state.SFLOW_ON = False

    if state.SFLOW_ON:
       st.components.v1.iframe(f'http://{API_HOST}:8008/app/mininet-dashboard/html/index.html#charts', height=400, scrolling=True)

    # Visualize docker containers status

    # Specify the directory path and the file prefix
    DIRECTORY_PATH = Path('../data/')
    FILE_PREFIX = 'container_stats_'
    FILE_EXTENSION = '.csv'  # Change this to the desired file extension

    # Get a list of files matching the prefix and extension
    matching_files = DIRECTORY_PATH.glob(f"{FILE_PREFIX}*{FILE_EXTENSION}")

    if any(file.name.startswith(FILE_PREFIX) for file in DIRECTORY_PATH.iterdir() if file.is_file()):
        # Find the most recent file based on creation time
        latest_file = max(matching_files, key=lambda f: f.stat().st_ctime)
        df = pd.read_csv(latest_file)
        st.write("Containers status:")
        st.write(df) # visualize the csv table

    e1, e2, _ = st.columns([1,1,1])

    with e1:
        if st.button('Collect data'):
            st.write(cmdline('cd ../scripts ; ./container_stats_csv.sh ; cd ../GUI'))
    with e2:
        if st.button('Refresh Page'):
            st.rerun()

    # if st.button('Check health'):
    #     st.write(cmdline('cd ../scripts ; ./containers_overloaded_csv.sh ; cd ../GUI'))

    if st.button('🔥 Digital Twin APIs'):
        st.components.v1.iframe(f'http://{API_HOST}:8000/docs', height=400, scrolling=True)

    st.divider()

    # Display Prediction
    f1, f2, _ = st.columns([1,1,1])

    with f1:
       if st.button('🔥 Display Prediction'):
           state.PREDICTION_ON = True
    with f2:
       if st.button('🔥 Hide Prediction'):
           state.PREDICTION_ON = False

    if state.PREDICTION_ON:
        st.image("../data/output.png", width=800)

    st.divider()

def sidebar():
    # ABOUT
    st.sidebar.image("HORSE_logo.jpg",width=300)
    st.sidebar.header('About')
    st.sidebar.info('First integrated demo of the HORSE Digital Twin (DT)!\n\n' + \
        'Check out HORSE project (horse-6g.eu) for more information.')
    st.sidebar.markdown('---')


if __name__ == '__main__':
    main()
    sidebar()
