import uvicorn
from fastapi import FastAPI
import os

# --- Configuration and Variable Setup ---

# The core status message required in the response.
BASE_STATUS_PREFIX = "HORSE P&P NDT status:"

# Define the path to the file containing the current NDT status detail.
STATUS_FILE_PATH = "status_detail.txt"

# Define the port the server will run on. Default to 8000, but can be
# overridden by the environment variable PORT for easy deployment.
SERVER_PORT = int(os.environ.get("PORT", 10001))

# Initialize the FastAPI application
app = FastAPI(
    title="NDT Status API",
    description="Simple server to report the status of the HORSE P&P system."
)


# --- Endpoint Definition ---

@app.get("/status", tags=["Status"])
def get_nd_status():
    """
    Handles a GET request on /status and returns the combined status string.
    The status detail is read from a file on every request.
    """
    # Default/Fallback status in case of an issue
    ndt_status_detail = "UNKNOWN (Error reading status file)"

    try:
        # Read the status detail from the file. The 'strip()' removes leading/trailing whitespace and newlines.
        with open(STATUS_FILE_PATH, 'r') as f:
            # We only expect a single line of status text
            ndt_status_detail = f.read().strip()
    except FileNotFoundError:
        # If the status file doesn't exist, log an error and use the fallback status.
        print(f"ERROR: Status file not found at '{STATUS_FILE_PATH}'. Please create this file.")
        # ndt_status_detail remains "UNKNOWN (Error reading status file)"
    except Exception as e:
        # Handle other potential errors (e.g., permission issues)
        print(f"An unexpected error occurred while reading the status file: {e}")
        ndt_status_detail = "UNKNOWN (Internal Server Error)"


    # Combine the required prefix with the current status variable
    full_status_message = f"{BASE_STATUS_PREFIX} {ndt_status_detail}"

    # FastAPI automatically handles converting the returned string into a
    # successful (200 OK) plain text or JSON response.
    return full_status_message


# --- Server Startup ---

if __name__ == "__main__":
    # To run this server, you must first install the required libraries:
    # pip install fastapi uvicorn
    print(f"Starting server on http://127.0.0.1:{SERVER_PORT}")
    print(f"Access the status at: http://127.0.0.1:{SERVER_PORT}/status")
    print(f"NOTE: The status will be read from the file: '{STATUS_FILE_PATH}'")

    # Start the Uvicorn server instance
    uvicorn.run(
        app,
        host="0.0.0.0",  # Listen on all interfaces
        port=SERVER_PORT
    )
