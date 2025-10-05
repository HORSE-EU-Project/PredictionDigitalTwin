import socket
import sys

# Configuration must match dashboard.py
TARGET_HOST = '127.0.0.1' # Use '127.0.0.1' if running locally, or the IP of the dashboard server
TARGET_PORT = 9001

def send_update(box_id, color):
    """Sends a UDP packet to the dashboard listener."""
    
    # Validate input
    VALID_COLORS = ['red', 'yellow', 'green']
    VALID_BOXES = ['box1', 'box2', 'box3']

    if box_id not in VALID_BOXES or color not in VALID_COLORS:
        print("Invalid Box ID or Color.")
        print("Usage: python update_sender.py <box1|box2|box3> <red|yellow|green>")
        return

    message = f"{box_id},{color}"
    
    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    try:
        # Send the message
        print(f"Sending UDP message: '{message}' to {TARGET_HOST}:{TARGET_PORT}")
        sock.sendto(message.encode(), (TARGET_HOST, TARGET_PORT))
        print("Message sent successfully.")
    except Exception as e:
        print(f"Error sending UDP packet: {e}")
    finally:
        sock.close()

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python update_sender.py <box_id> <color>")
        print("Example: python update_sender.py box2 green")
    else:
        send_update(sys.argv[1], sys.argv[2])

