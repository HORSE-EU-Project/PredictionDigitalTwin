# To send an xml file:
# curl --header "Content-Type: text/xml" --data @note.xml 192.168.130.9:65123


import http.server
import socketserver
import urllib.parse
import os
import datetime

PORT = 65123
UPLOAD_DIR = "uploads"
PREFIX = "uploaded_file_"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        file_path = parsed_path.path.lstrip('/')

        if file_path:
            try:
                with open(file_path, 'rb') as file:
                    self.send_response(200)
                    self.send_header("Content-type", "application/octet-stream")
                    self.end_headers()
                    self.wfile.write(file.read())
            except Exception as e:
                self.send_response(404)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(f"<html><body><h1>File Not Found</h1><p>{str(e)}</p></body></html>".encode('utf-8'))
        else:
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Bad Request</h1></body></html>")

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{PREFIX}_{timestamp}.txt"

        # filename = self.headers.get('Filename', 'uploaded_file')
        file_path = os.path.join(UPLOAD_DIR, filename)

        try:
            with open(file_path, 'wb') as file:
                file.write(post_data)

            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(f"<html><body><h1>File Saved</h1><p>Saved as {filename}</p></body></html>".encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(f"<html><body><h1>Error</h1><p>{str(e)}</p></body></html>".encode('utf-8'))

with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
    print(f"Serving on port {PORT}")
    httpd.serve_forever()
