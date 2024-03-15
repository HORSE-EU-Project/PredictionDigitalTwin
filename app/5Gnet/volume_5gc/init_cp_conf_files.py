import sys, socket, time, shutil, json, subprocess


if __name__ == "__main__":
    
    with open( '/mnt/volume_5gc/scenario.json', 'r') as f:
        scenario = json.load(f)

    cp_config = scenario["hosts"]["cp"]

    shutil.copy2('/mnt/volume_5gc/ausf.yaml', '/open5gs/install/etc/open5gs/ausf.yaml')
    shutil.copy2('/mnt/volume_5gc/bsf.yaml', '/open5gs/install/etc/open5gs/bsf.yaml')
    shutil.copy2('/mnt/volume_5gc/nrf.yaml', '/open5gs/install/etc/open5gs/nrf.yaml')
    shutil.copy2('/mnt/volume_5gc/nssf.yaml', '/open5gs/install/etc/open5gs/nssf.yaml')
    shutil.copy2('/mnt/volume_5gc/pcf.yaml', '/open5gs/install/etc/open5gs/pcf.yaml')
    shutil.copy2('/mnt/volume_5gc/template_amf.yaml', '/open5gs/install/etc/open5gs/amf.yaml')
    shutil.copy2('/mnt/volume_5gc/template_smf.yaml', '/open5gs/install/etc/open5gs/smf.yaml')
    shutil.copy2('/mnt/volume_5gc/udm.yaml', '/open5gs/install/etc/open5gs/udm.yaml')
    shutil.copy2('/mnt/volume_5gc/udr.yaml', '/open5gs/install/etc/open5gs/udr.yaml')

    # Custom AMF config file creation
    with open( "/open5gs/install/etc/open5gs/amf.yaml", 'r') as f:
        new_file_content = ""
        for line in f:
            new_line = line.replace("<DOCKER_HOST_IP>", cp_config["ip"][0:-3])
            new_file_content += new_line

    with open( "/open5gs/install/etc/open5gs/amf.yaml", 'w') as f:
        f.write(new_file_content)

    # Custom SMF config file creation
    with open( "/open5gs/install/etc/open5gs/smf.yaml", 'r') as f:
        new_file_content = ""
        for line in f:
            if "<DOCKER_HOST_IP>" in line:
                new_line = line.replace("<DOCKER_HOST_IP>", cp_config["ip"][0:-3])
                new_file_content += new_line 
            elif "<SUB_NETS>" in line:
                for u in cp_config["upfs"]:
                    new_file_content += f"      - addr: {u['subnet']}" +"\n"
                    new_file_content += f"        dnn:  {u['dnn']}" +"\n"
            elif "<UPFS>" in line:
                for u in cp_config["upfs"]:
                    new_file_content += f"      - addr: {u['host_ip']}" +"\n"
                    new_file_content += f"        dnn:  {u['dnn']}" +"\n"
            else:
                new_file_content += line 

    with open( "/open5gs/install/etc/open5gs/smf.yaml", 'w') as f:
        f.write(new_file_content)

