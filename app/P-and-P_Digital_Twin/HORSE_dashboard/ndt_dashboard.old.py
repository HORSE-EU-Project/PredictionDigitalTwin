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

# Global state for the box colors. Stores simple color names, not CSS classes.
BOX_COLORS = {
    'box1': 'red',
    'box2': 'red',
    'box3': 'red',
}
VALID_COLORS = ['red', 'yellow', 'green']
VALID_BOXES = BOX_COLORS.keys()

def get_tailwind_class(color_name):
    """Maps a simple color name to a Tailwind CSS background class."""
    return f'bg-{color_name}-500' if color_name in VALID_COLORS else 'bg-gray-700' # Fallback color

# --- UDP Listener Function ---

def udp_listener():
    """Listens for incoming UDP packets and updates the BOX_COLORS state."""
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
            message = data.decode().strip().lower()
            
            print(f"\n[UDP] Received message from {addr}: '{message}'")

            # Parse the message (Expected format: <box_id>,<color>)
            if ',' in message:
                box_id, color = [s.strip() for s in message.split(',', 1)]

                if box_id in VALID_BOXES and color in VALID_COLORS:
                    
                    # Update state safely
                    with state_lock:
                        BOX_COLORS[box_id] = color
                        print(f"[UDP] State updated successfully: {box_id} is now {color}")
                else:
                    print(f"[UDP] Invalid content. Box ID '{box_id}' or Color '{color}' is not valid.")
            else:
                print(f"[UDP] Invalid format. Expected 'boxN,color'. Got: {message}")

        except Exception as e:
            print(f"[UDP] An error occurred in UDP listener loop: {e}")
            time.sleep(1)

# --- Flask Web Route ---

app = Flask(__name__)

@app.route('/')
def dashboard():
    """Renders the HTML dashboard using the current box colors."""
    
    # Safely read the current state
    with state_lock:
        current_color_names = BOX_COLORS.copy()

    # Convert color names to Tailwind CSS classes for rendering
    current_classes = {
        key: get_tailwind_class(name) 
        for key, name in current_color_names.items()
    }
    
    print(f"[WEB] Dashboard accessed. Current status: {current_color_names}")

    # Tailwind CDN for easy styling
    HTML_TEMPLATE = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>HORSE NDT Status Dashboard</title>
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
        
        <!-- ADDED Image at the top (using a placeholder) -->
       <img src="/static/horse-logo.png" onerror="this.onerror=null;this.src='https://placehold.co/150x50/333/ffffff?text=Image+Missing'" alt="Dashboard Logo" class="mb-8 rounded-lg shadow-md h-16 w-auto">

        <!-- CHANGED Heading text color for contrast with white background -->
        <h1 class="text-4xl font-extrabold text-gray-900 mb-10">P&P Network Digital Twin Status Monitor</h1>

        <div class="w-full max-w-4xl grid grid-cols-1 sm:grid-cols-3 gap-6">

            <!-- Box 1 -->
            <div id="box1" class="p-6 rounded-xl shadow-2xl transition-colors duration-500 { current_classes['box1'] }">
                <h2 class="text-2xl font-semibold text-white mb-2">Service A</h2>
                <p class="text-sm text-gray-100">Box 1 status: { current_color_names['box1'].upper() }</p>
            </div>

            <!-- Box 2 -->
            <div id="box2" class="p-6 rounded-xl shadow-2xl transition-colors duration-500 { current_classes['box2'] }">
                <h2 class="text-2xl font-semibold text-white mb-2">Service B</h2>
                <p class="text-sm text-gray-100">Box 2 status: { current_color_names['box2'].upper() }</p>
            </div>

            <!-- Box 3 -->
            <div id="box3" class="p-6 rounded-xl shadow-2xl transition-colors duration-500 { current_classes['box3'] }">
                <h2 class="text-2xl font-semibold text-white mb-2">Service C</h2>
                <p class="text-sm text-gray-100">Box 3 status: { current_color_names['box3'].upper() }</p>
            </div>

        </div>

        <!-- CHANGED Footer text color for contrast with white background -->
        <p class="mt-8 text-gray-600 text-center text-sm">
            Dashboard is served on HTTP (Port {WEB_PORT}). Colors are updated by a separate UDP listener (Port {UDP_PORT}).
            <br>
            This page auto-refreshes every 3 seconds to show color changes.
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
    return render_template_string(HTML_TEMPLATE, current_classes=current_classes, current_color_names=current_color_names, WEB_PORT=WEB_PORT, UDP_PORT=UDP_PORT)

# --- Main Execution ---

if __name__ == '__main__':
    # 1. Start the UDP Listener in a background thread
    listener_thread = threading.Thread(target=udp_listener, daemon=True)
    listener_thread.start()
    
    # 2. Start the Flask web application
    print(f"Flask Dashboard running on http://127.0.0.1:{WEB_PORT}")
    app.run(host=HOST, port=WEB_PORT, debug=False, use_reloader=False)

