import yaml
import ipaddress
import sys

input_filename = sys.argv[1]

with open(input_filename, 'r') as file:
    data = yaml.safe_load(file)

    host_num=0
    switch_num=0
    startIP=ipaddress.IPv4Address('192.168.0.100')

    original_stdout = sys.stdout # Save a reference to the original standard output

    with open('output.py', 'w') as f:
        sys.stdout = f

        with open('header.py','r') as firstfile:
        # read content from first portion of the template file 
            for line in firstfile: 
                # append content to the main file 
                f.write(line)

        print("\n    info(\"*** Adding switches and hosts\")")
        for node in data['nodes']:
        #print(node['name'], node['vendor'], node['config']['image'], node['interfaces'])
            if node['vendor']=="CISCO":
                print("    %s=net.addSwitch('%s')" % (node['name'], node['name']))
                switch_num+=1
            else:
                if ("server" in node['name']):
                    print("    %s=net.addDockerHost('%s', dimage=\"dev_test\", ip=\"%s\", docker_args={\"hostname\": \"%s\"})" % (node['name'], node['name'], str(startIP+host_num), node['name']))
                    host_num+=1
                else:
                    print("    # %s will be a mobile host configured within EURANSIM" % node['name'])
                    host_num+=1

        print("\n    info(\"*** Adding links\")")

        for link in data['links']:
            print("    net.addLink(%s, %s, bw=100, delay=\"10ms\", intfName1=\"%s-%s\", intfName2=\"%s-%s\")" % (link['a_node'], link['z_node'], link['a_node'], link['a_int'], link['z_node'], link['z_int']))

        with open('footer.py','r') as firstfile: 
        # read content from last portion of the template file 
            for line in firstfile: 
                # append content to the main file 
                f.write(line)

sys.stdout = original_stdout
