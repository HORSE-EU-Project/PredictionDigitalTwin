import pandas as pd
import os
import time
from mininet.net import Mininet
from mininet.node import RemoteController, CPULimitedHost
from mininet.link import TCLink
from mininet.util import customClass
from mininet.topo import Topo
import subprocess
import configparser
from threading import Thread, Lock
import glob
from datetime import datetime

# Lettura del file di configurazione
config = configparser.ConfigParser()
config.read('config.ini')

# Inizializza l'indice dei file PCAP
indice_pcap = 0

# Legge il valore 'interval' dalla sezione [FLOW]
interval = int(config['FLOW']['interval'])
tt = datetime.now().strftime('%H_%M_%S')

# Inizializza la directory per i pcap
config['PCAP']['pcap_dir_DT'] = tt
if 'PCAP_DT' not in config:
    config.add_section('PCAP_DT')

with open('config.ini', 'w') as configfile:
    config.write(configfile)

pcap_dir = f"pcap/{tt}"
os.makedirs(pcap_dir, exist_ok=True)

# Lettura e unione dei file CSV elencati in [FLOWS_TRANSLATED] dopo essere mappati
def read_csv_PT_files(config):
    all_data = []
    for key, file_path in config['FLOWS_TRANSLATED'].items():
        if key.startswith('file_') and os.path.exists(file_path):
            df = pd.read_csv(file_path)
            df['ipsrc'] = df['ipsrc'].astype(str).fillna('')
            df['ipdst'] = df['ipdst'].astype(str).fillna('')
            df['y'] = pd.to_numeric(df['y'], errors='coerce')
            df = df[df['ipsrc'].str.match(r'^\d+\.\d+\.\d+\.\d+$')]
            df = df[df['ipdst'].str.match(r'^\d+\.\d+\.\d+\.\d+$')]
            all_data.append(df)
    return all_data

# Inizializza la topologia Mininet
'''
class CSVTopo(Topo):
    def build(self, ip_list):
        hosts = {ip: self.addHost(f"h{idx+1}", ip=ip) for idx, ip in enumerate(ip_list)}
        switch = self.addSwitch('s1')
        for host in hosts.values():
            self.addLink(host, switch)
'''
# Correzione della topologia di Mininet
class CorrectedTopo(Topo):
    def build(self, ip_list):
        switch = self.addSwitch('s1')  # Uno switch centrale
        hosts = {}

        for i, ip in enumerate(ip_list):
            host_name = f"h{i+1}"
            hosts[ip] = self.addHost(host_name, ip=ip)
            self.addLink(hosts[ip], switch, bw=50, delay='5ms', jitter='1ms')  # Connette ogni host allo switch -- AGGIUNTO BW=20 E DELAY , bw=20, delay='5ms'
            
            


# Avvio Mininet con la nuova topologia
def setup_mininet(ip_list):
    #setLogLevel('info')
    topo = CorrectedTopo(ip_list)
    link = customClass({'tc': TCLink}, 'tc')
    net = Mininet(topo=topo, link=TCLink, controller=RemoteController, host=CPULimitedHost, autoSetMacs=True)

    print("\nAvvio della rete Mininet...")
    net.start()

    # Dump degli host con nome e IP
    print("\nDump degli host in Mininet:")
    for host in net.hosts:
        print(f"{host.name} --> IP: {host.IP()}")

    # Test della connettività con pingall
    print("\nTEST DI CONNETTIVITÀ: Pingall tra tutti gli host...\n")
    result = net.pingAll()
    if result > 0:
        print("ERRORE: Alcuni host non sono raggiungibili! Controlla la topologia o la configurazione IP.")
    else:
        print("Tutti gli host sono connessi correttamente!")

    return net
    
    
def start_servers_and_tcpdump(flows, net):
    global indice_pcap
    server_ports = {}
    port_start = 10000  # Porta iniziale per i server
    max_port = 11000  # Porta massima per i server
    assigned_ports = set()  # Mantiene traccia delle porte già assegnate

    for ipdst in flows['ipdst'].unique():
        dst_host = next((h for h in net.hosts if h.IP() == ipdst), None)
        if ipdst.startswith("224.") or ipdst == "255.255.255.255":
            print(f"Ignorato server su IP non valido {ipdst}")
            continue

        if dst_host:
            ports = []
            num_clients = len(flows[flows['ipdst'] == ipdst]['ipsrc'].unique())

            for _ in range(num_clients):
                # Trova una porta libera
                while port_start in assigned_ports and port_start <= max_port:
                    port_start += 1

                if port_start > max_port:
                    print(f"Nessuna porta disponibile per il server {ipdst}.")
                    continue

                assigned_ports.add(port_start)
                log_file = f"/var/tmp/iperf3_server_{port_start}.log"
                server_cmd = f"nohup iperf3 -s -p {port_start} -B {ipdst} > {log_file} 2>&1 &"
                dst_host.cmdPrint(server_cmd)

                # Controlla se il server è effettivamente in ascolto
                time.sleep(2)
                check_cmd = f"netstat -tulnp | grep {port_start}"
                result = dst_host.cmd(check_cmd)
                if not result:
                    print(f"ERRORE: Il server iperf3 su {ipdst}:{port_start} non è stato avviato correttamente!")
                else:
                    print(f"Server iperf3 attivo su {ipdst}, porta {port_start}")

                ports.append(port_start)

            # Avvia tcpdump
            pcap_file = f"{pcap_dir}/server_{ipdst.replace('.', '_')}.pcap"
            tcpdump_cmd = f"sudo tcpdump -i {dst_host.defaultIntf()} -w {pcap_file} & echo $!"
            pid = dst_host.cmd(tcpdump_cmd).strip()
            tcpdump_pids[ipdst] = pid
            print(f"Tcpdump avviato su {ipdst}, file pcap: {pcap_file}, PID: {pid}")

            # Salva il file pcap nella configurazione
            config['PCAP_DT'][f'file_{indice_pcap}'] = pcap_file
            with open('config.ini', 'w') as configfile:
                config.write(configfile)

            print(f"File pcap registrato in config.ini: {pcap_file}")
            indice_pcap += 1

            server_ports[ipdst] = ports

    return server_ports


# Avvio parallelo dei client iperf3
def start_clients_parallel(flows, net, server_ports, interval):
    threads = []
    lock = Lock()
    max_port = 11000  # Definisci un range massimo per le porte
    assigned_ports = set()  # Tiene traccia delle porte già assegnate

    for _, flow in flows.iterrows():
        src_ip, dst_ip, bit_rate = flow['ipsrc'], flow['ipdst'], flow['y']
        src_host = next((h for h in net.hosts if h.IP() == src_ip), None)

        if not src_host:
            print(f"Errore: Host sorgente {src_ip} non trovato in Mininet!")
            continue

        # Se non ci sono porte disponibili, ne assegniamo una nuova
        if dst_ip not in server_ports or not server_ports[dst_ip]:
            port = 10000
            while port in assigned_ports and port <= max_port:
                port += 1

            if port > max_port:
                print(f"Errore critico: Nessuna porta disponibile per {dst_ip}!")
                continue

            print(f"Assegno nuova porta {port} per {dst_ip}.")
            server_ports.setdefault(dst_ip, []).append(port)
            assigned_ports.add(port)

        # Prendi la prima porta disponibile
        port = server_ports[dst_ip].pop(0)
        
        t = Thread(target=start_client, args=(src_host, dst_ip, port, bit_rate, interval, lock))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()


# Avvio di un singolo client iperf3
def start_client(src_host, dst_ip, port, bit_rate, interval, lock):
    with lock:
        cmd = f"iperf3 -u -c {dst_ip} -p {port} -b {round(bit_rate)} -t {interval} &"
        src_host.cmdPrint(cmd)
        print(f"cmd client {src_host.IP()} --> {cmd}")

# Arresto di tcpdump e iperf3
def stop_tcpdump():
    for ip, pid in tcpdump_pids.items():
        host = next((h for h in net.hosts if h.IP() == ip), None)
        if host:
            host.cmd(f"kill {pid}")
            print(f"Tcpdump terminato su {ip}, PID: {pid}")

def stop_iperf_servers(net):
    for host in net.hosts:
        print(f"Arresto iperf3 su {host.name} ({host.IP()})...")
        host.cmd("pkill -f 'iperf3 -s'")
        
def start_ryu():
    subprocess.run("pkill -f ryu-manager", shell=True)
    time.sleep(2)
    subprocess.Popen("ryu-manager ryu.app.simple_switch_13 &", shell=True)
    time.sleep(5)
    print("Ryu controller restarted.")
    
# Avvio dei server iperf3 e tcpdump
tcpdump_pids = {}


# Codice principale
if __name__ == "__main__":
    all_data = read_csv_PT_files(config)
    if not all_data:
        print("Nessun file CSV trovato! Interruzione del programma.")
        exit(1)

    combined_df = pd.concat(all_data).sort_values(by='ds')
    ip_list = list(set(combined_df['ipsrc']).union(set(combined_df['ipdst'])))
    start_ryu()
    
    '''
    topology = CSVTopo(ip_list)
    link = customClass({'tc': TCLink}, 'tc')

    net = Mininet(topo=topology, link=link, controller=RemoteController, host=CPULimitedHost, autoSetMacs=True)
    net.start()

    # Debug degli host Mininet
    print("\nDump degli host in Mininet:")
    for host in net.hosts:
        print(f"{host.name} --> IP: {host.IP()}")
    
    print("\nTEST DI CONNETTIVITÀ: Pingall tra tutti gli host...\n")
    result = net.pingAll()
    if result > 0:
        print("ERRORE: Alcuni host non sono raggiungibili! Verifica la configurazione di Mininet.")
    else:
        print("Tutti gli host sono connessi correttamente!")
    '''
    
     
    net = setup_mininet(ip_list)
    
    
    server_ports = start_servers_and_tcpdump(combined_df, net)
    start_clients_parallel(combined_df, net, server_ports, interval)

    time.sleep(interval + 5)  # Attendi la fine del test
    stop_tcpdump()
    stop_iperf_servers(net)
    
    net.stop()
    print("Test completato!")
