import socket
import sys

# --- Configuration ---
TARGET_HOST = '127.0.0.1'  # Change this to the IP of the machine running dashboard.py if necessary
TARGET_PORT = 9001

def send_update(box_id, color, status_text):
    """
    Sends a UDP packet to update a box's color and status text.
    The message format is: <box_id>,<color>,<status_text>
    """
    message = f"{box_id},{color},{status_text}"
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    try:
        sock.sendto(message.encode('utf-8'), (TARGET_HOST, TARGET_PORT))
        print(f"Update sent successfully to {TARGET_HOST}:{TARGET_PORT}")
        print(f"Message: {message}")
    except Exception as e:
        print(f"Error sending message: {e}")
    finally:
        sock.close()

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python update_sender.py <box_id> <color> \"<status_text>\"")
        print("\nExample 1 (Success):")
        print('python update_sender.py box1 green "All systems nominal"')
        print("\nExample 2 (Warning):")
        print('python update_sender.py box3 yellow "Disk space low, check logs"')
        print("\nExample 3 (Failure):")
        print('python update_sender.py box2 red "Critical failure, service stopped"')
        sys.exit(1)
        
    box_id = sys.argv[1]
    color = sys.argv[2]
    # The status text is the third argument. Use double quotes to handle spaces.
    status_text = sys.argv[3]
    
    send_update(box_id, color, status_text)

