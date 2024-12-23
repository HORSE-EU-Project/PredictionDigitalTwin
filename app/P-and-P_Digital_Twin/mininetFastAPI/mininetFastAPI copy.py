from fastapi import FastAPI
from pydantic import BaseModel
from configparser import ConfigParser
import uvicorn
import time

class MNCmd(BaseModel):
    command: str

class MininetRest():

    def __init__(self, net):
        super(MininetRest, self).__init__()
        self.net = net
        self.app = FastAPI()

        @self.app.get("/")
        async def read_root():
            return {"Digital Twin": "Ready"}

        @self.app.get("/nodes")
        async def get_nodes():
            return {'nodes': [n for n in self.net]} 

        @self.app.get("/links")
        async def get_links():
            return {'links': [dict(name=l.intf1.node.name + '-' + l.intf2.node.name,
                node1=l.intf1.node.name, node2=l.intf2.node.name,
                intf1=l.intf1.name, intf2=l.intf2.name) for l in self.net.links]}

        @self.app.get("/switches")
        async def get_switches():
            return {'switches': [s.name for s in self.net.switches]}

        @self.app.get("/hosts")
        async def get_hosts():
            return {'hosts': [h.name for h in self.net.hosts]}

        @self.app.get("/nodes/{node_name}")
        async def get_node(node_name: str):
            node = self.net[node_name]
            return {'intfs': [i.name for i in node.intfList()], 'params': node.params}

        @self.app.get("/nodes/{node_name}/{intf_name}")
        async def get_intf(node_name:str, intf_name: str):
            node = self.net[node_name]
            intf = node.nameToIntf[intf_name]
            return {'name': intf.name, 'status': 'up' if intf.name in intf.cmd('ifconfig') else 'down',
                "params": intf.params}

        @self.app.post("/nodes/{node_name}/cmd")
        async def run_cmd(node_name: str, cmd: MNCmd):
            node = self.net[node_name]
            args = cmd.command
            rest = args.split(' ')
            # Substitute IP addresses for node names in command
            # If updateIP() returns None, then use node name
            rest = [self.net[arg].defaultIntf().updateIP() or arg
                if arg in self.net else arg
                for arg in rest]
            rest = ' '.join(rest)
            node.sendCmd(rest)
            output = ''
            init_time = time.time()
            while node.waiting:
                exec_time = time.time() - init_time
                if exec_time > 5:
                    break
                data = node.monitor(timeoutms=1000)
                output += data
            if node.waiting:
                node.sendInt()
                time.sleep(0.5)
                data.monitor(timeoutms=1000)
                output += data
                node.waiting = False
            return output

    def run(self):
        # Read the config.ini file
        config_object = ConfigParser()
        config_object.read("config.ini")
        mininet_config = config_object["MININET_SERVER"]
        uvicorn.run(self.app, host=mininet_config["ipaddr"], port=int(mininet_config["port"])) 
        # reload=True which nedd to pass app in pattern "module:app"
        # uvicorn.run("main:server.app", host="0.0.0.0", port=8000, reload=True, use_colors=False) 
                 # self.app ->  server.app

#server = MininetRest(net) ### edit here
#if __name__ == "__main__":
#    server.run()
