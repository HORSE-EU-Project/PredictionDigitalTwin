import os, sys, json, base64
import time
import requests
from pathlib import Path
import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
from subprocess import PIPE, Popen
from configparser import ConfigParser

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
    st.title('HORSE Digital Twin Graphical Testing Interface')

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
    st.image("../HORSE_data/HORSE-DDoS-DNS-simp.png",width=800)
    
    st.divider()

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
    # RUN 5G/6G SPECIFIC SCENARIO
    st.write("To run the 5G/6G Network Digital Twin:")
    st.code("./run_digitaltwin.sh", language="python")
    st.write("To run the 5G/6G Network Digital Twin interactively:")
    st.code("ryu-manager ryu.app.simple_switch_stp_13", language="python")
    st.code("sudo python3 DT_v0.7.py", language="python")

    st.markdown(f'''
         `Once the DT is running, you can access the REST APIs here:`
         [**http://{API_HOST}:8000/docs**](http://{API_HOST}:8000/docs)
         ''')

    # Information
    st.markdown(f'''
        #### Notes
        - `To terminate the DT, please use the CLI and close sFlow.`
        - `To invoke the / endpoint of the REST API (check for API availability), click the Hello button above.`
    ''')

def sidebar():
    # ABOUT
    st.sidebar.image("HORSE_logo.jpg",width=300)
    st.sidebar.header('About')
    st.sidebar.info('FastAPI Wrapper to run and stop the HORSE Digital Twin (DT)!\n\n' + \
        'Check out HORSE project (horse-6g.eu) for more information.')
    st.sidebar.markdown('---')


if __name__ == '__main__':
    main()
    sidebar()
