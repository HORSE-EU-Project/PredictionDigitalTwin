import threading
import socket
import time
from flask import Flask, render_template_string

# --- Configuration and State ---
WEB_PORT = 9000
UDP_PORT = 9001
HOST = '0.0.0.0'

# Lock for safely updating the global state from different threads
state_lock = threading.Lock()

# Global state for the box colors and status text.
BOX_STATE = {
    'box1': {'color': 'red', 'status': 'Initial Status: Disconnected'},
    'box2': {'color': 'red', 'status': 'Initial Status: Disconnected'},
    'box3': {'color': 'red', 'status': 'Initial Status: Disconnected'},
}
VALID_COLORS = ['red', 'yellow', 'green']
VALID_BOXES = BOX_STATE.keys()

def get_tailwind_class(color_name):
    """Maps a simple color name to a Tailwind CSS background class."""
    return f'bg-{color_name}-500' if color_name in VALID_COLORS else 'bg-gray-700' # Fallback color

# --- UDP Listener Function ---

def udp_listener():
    """Listens for incoming UDP packets and updates the BOX_STATE."""
    print(f"UDP Listener starting on {HOST}:{UDP_PORT}...")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    try:
        sock.bind((HOST, UDP_PORT))
    except Exception as e:
        print(f"FATAL: Error binding UDP socket on port {UDP_PORT}. Is the port already in use? Error: {e}")
        return

    while True:
        try:
            data, addr = sock.recvfrom(1024)
            message = data.decode().strip() # Preserve case for status message
            
            print(f"\n[UDP] Received message from {addr}: '{message}'")

            # Parse the message (Expected format: <box_id>,<color>,<status_text>)
            parts = [s.strip() for s in message.split(',', 2)]
            
            if len(parts) == 3:
                box_id = parts[0].lower()
                color = parts[1].lower()
                status_text = parts[2]

                if box_id in VALID_BOXES and color in VALID_COLORS:
                    
                    # Update state safely
                    with state_lock:
                        BOX_STATE[box_id]['color'] = color
                        BOX_STATE[box_id]['status'] = status_text
                        print(f"[UDP] State updated successfully: {box_id} is now {color} with status: '{status_text}'")
                else:
                    print(f"[UDP] Invalid content. Box ID '{box_id}' or Color '{color}' is not valid.")
            else:
                print(f"[UDP] Invalid format. Expected 'boxN,color,status text'. Got {len(parts)} parts.")

        except Exception as e:
            print(f"[UDP] An error occurred in UDP listener loop: {e}")
            time.sleep(1)

# --- Flask Web Route ---

app = Flask(__name__)

@app.route('/')
def dashboard():
    """Renders the HTML dashboard using the current box colors and status."""
    
    # Safely read the current state
    with state_lock:
        current_state = BOX_STATE.copy()

    # Prepare data for rendering
    data_for_template = {}
    for box_id, state in current_state.items():
        data_for_template[box_id] = {
            'color_class': get_tailwind_class(state['color']),
            'color_name': state['color'].upper(),
            'status_text': state['status']
        }
    
    print(f"[WEB] Dashboard accessed. Current status: {current_state}")

    # Tailwind CDN for easy styling
    HTML_TEMPLATE = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Status Dashboard</title>
        <!-- Load Tailwind CSS -->
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            /* Custom styling for Inter font */
            body {{
                font-family: 'Inter', sans-serif;
            }}
        </style>
    </head>
    <!-- CHANGED background to white -->
    <body class="min-h-screen bg-white flex flex-col items-center justify-center p-4">
        
        <!-- UPDATED Image src to point to the local static path -->
        <img src="/static/horse-logo.png" onerror="this.onerror=null;this.src='https://placehold.co/150x50/333/ffffff?text=Image+Missing'" alt="Dashboard Logo" class="mb-8 rounded-lg shadow-md h-16 w-auto">

        <!-- CHANGED Heading text color for contrast with white background -->
        <h1 class="text-4xl font-extrabold text-gray-900 mb-10">System Status Monitor</h1>

        <div class="w-full max-w-4xl grid grid-cols-1 sm:grid-cols-3 gap-6">

            <!-- Box 1 -->
            <div id="box1" class="p-6 rounded-xl shadow-2xl transition-colors duration-500 { data_for_template['box1']['color_class'] }">
                <h2 class="text-2xl font-semibold text-white mb-2">Service A</h2>
                <p class="text-sm text-gray-100 mb-2">Color: { data_for_template['box1']['color_name'] }</p>
                <!-- NEW Status Text Field -->
                <p class="text-base text-white font-medium break-words">Status: { data_for_template['box1']['status_text'] }</p>
            </div>

            <!-- Box 2 -->
            <div id="box2" class="p-6 rounded-xl shadow-2xl transition-colors duration-500 { data_for_template['box2']['color_class'] }">
                <h2 class="text-2xl font-semibold text-white mb-2">Service B</h2>
                <p class="text-sm text-gray-100 mb-2">Color: { data_for_template['box2']['color_name'] }</p>
                <!-- NEW Status Text Field -->
                <p class="text-base text-white font-medium break-words">Status: { data_for_template['box2']['status_text'] }</p>
            </div>

            <!-- Box 3 -->
            <div id="box3" class="p-6 rounded-xl shadow-2xl transition-colors duration-500 { data_for_template['box3']['color_class'] }">
                <h2 class="text-2xl font-semibold text-white mb-2">Service C</h2>
                <p class="text-sm text-gray-100 mb-2">Color: { data_for_template['box3']['color_name'] }</p>
                <!-- NEW Status Text Field -->
                <p class="text-base text-white font-medium break-words">Status: { data_for_template['box3']['status_text'] }</p>
            </div>

        </div>

        <!-- CHANGED Footer text color for contrast with white background -->
        <p class="mt-8 text-gray-600 text-center text-sm">
            Dashboard is served on HTTP (Port {WEB_PORT}). Colors and Status are updated by UDP listener (Port {UDP_PORT}).
            <br>
            This page auto-refreshes every 3 seconds to show changes.
        </p>
        
        <script>
            // Auto-refresh script: The curly braces are doubled to prevent Python f-string errors.
            setTimeout(() => {{
                window.location.reload();
            }}, 3000);
        </script>
    </body>
    </html>
    """
    return render_template_string(HTML_TEMPLATE, data_for_template=data_for_template, WEB_PORT=WEB_PORT, UDP_PORT=UDP_PORT)

# --- Main Execution ---

if __name__ == '__main__':
    # 1. Start the UDP Listener in a background thread
    listener_thread = threading.Thread(target=udp_listener, daemon=True)
    listener_thread.start()
    
    # 2. Start the Flask web application
    print(f"Flask Dashboard running on http://127.0.0.1:{WEB_PORT}")
    app.run(host=HOST, port=WEB_PORT, debug=False, use_reloader=False)

