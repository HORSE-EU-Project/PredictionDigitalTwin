#!/usr/bin/env python3

#
# HTTP python frontend of the OXYS reflector
# Usage: ./server.py [<port>]
#   

from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
import datetime
import subprocess

class MyServer(BaseHTTPRequestHandler):
    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    # HTTP GET
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', 'https://pewu.github.io')
            self.end_headers()
            content = open('mywebpage.html', 'rb').read()
            self.wfile.write(content)
        elif self.path == "/twamp":
            logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
            now = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            wrapper = """<html>
            <head>
            <title>%s output - %s</title>
            </head>
            <body><p>Output @ %s:</p><p> %s</p></body>
            </html>"""
            proc = subprocess.run(
                ["python3","./twamp.py","sender","172.17.0.3:861"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            output=proc.stdout
            whole = wrapper % ("TWAMP", now, now, output)
            self._set_response()
            self.wfile.write(whole.encode('utf-8'))
            csv_out = open("/home/data/twamp "+now+".csv","wt")
            n = csv_out.write(output)
            csv_out.close()
        elif self.path == "/iperf":
            logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
            now = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            wrapper = """<html>
            <head>
            <title>%s output - %s</title>
            </head>
            <body><p>Output @ %s:</p><p> %s</p></body>
            </html>"""
            proc = subprocess.run(
                ["python3","./iperf-client.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            output=proc.stdout
            whole = wrapper % ("IPERF", now, now, output)
            self._set_response()
            self.wfile.write(whole.encode('utf-8'))
            csv_out = open("/home/data/iperf "+now+".csv","wt")
            n = csv_out.write(output)
            csv_out.close()

# HTTP POST
    def do_POST(self):
        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data = self.rfile.read(content_length) # <--- Gets the data itself
        logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
                str(self.path), str(self.headers), post_data.decode('utf-8'))

        self._set_response()
        self.wfile.write("POST request for {}".format(self.path).encode('utf-8'))

# HTTP server activation and de-activation
def run(server_class=HTTPServer, handler_class=MyServer, port=8080):
    logging.basicConfig(level=logging.INFO)
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    # logging.info('Starting httpd...\n')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    # logging.info('Stopping httpd...\n')

if __name__ == '__main__':
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    elif len(argv) == 3:
        run(port=int(argv[1]))
        print("Server mode")
    else:
        run()
