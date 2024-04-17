import os, sys, json, base64
import time
import requests
import streamlit as st
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

#    if st.button('Run sFlow'):
#        cmdline("./run_sFlow.sh")
#        st.markdown(f'''
#            `sFlow is running. You can access the GUI here:`
#            [**http://{API_HOST}:8008**](http://{API_HOST}:8008)
#                ''')
#        if st.button('Stop sFlow'):
#            st.write(cmdline("pkill java"))

    # RUN 5G/6G SPECIFIC SCENARIO
    st.write("Commands to run the 5G Network Digital Twin interactively:")
    st.code("ryu-manager ryu.app.simple_switch_stp_13", language="python")
    st.code("sudo python3 DT_v0.5.py", language="python")

    st.markdown(f'''
         `Once the DT is running, you can access the REST APIs here:`
         [**http://{API_HOST}:8000/docs**](http://{API_HOST}:8000/docs)
         ''')

    st.divider()

    # RUN Digital Twin commands
    st.write("Commands to run specific scenarios on the NDT:")

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

    # st.code("sudo mn --custom ../sflow-rt/extras/sflow.py --link tc,bw=10 --topo tree,depth=2,fanout=2", language="python")

    st.divider() 

    # Interacting with Mininet REST API
    if not state.API_CHECKED:
        st.write('To check the Digital Twin REST API, click the button below.')
        if st.button('🚀 Verify API'):
            requests.get(f'http://{API_HOST}:8000')
            state.API_CHECKED = True

    if state.API_CHECKED:
        message = {}
        c1, c2, _, c4 = st.columns([1,1,1,1])
        with c1:
            if st.button('👋 Hello'):
                resp = requests.get(f'http://{API_HOST}:8000')
                message = json.loads(resp.content)
        with c2:
            st.json(message)
        with c4:
            if st.button('🔥 Shutdown DT'): 
                state.API_CHECKED = False

    if st.button('🔥 sFlow charts'):
        st.components.v1.iframe("http://192.168.56.2:8008/app/mininet-dashboard/html/index.html#charts", height=400, scrolling=True)

    if st.button('🔥 Digital Twin APIs'):
        st.components.v1.iframe("http://192.168.56.2:8000/docs", height=400, scrolling=True)

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
