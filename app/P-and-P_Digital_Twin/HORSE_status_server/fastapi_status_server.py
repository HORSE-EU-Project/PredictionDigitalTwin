import uvicorn
from fastapi import FastAPI
import os

# --- Configuration and Variable Setup ---

# The core status message required in the response.
BASE_STATUS_PREFIX = "HORSE P&P NDT status:"

# This is the string variable that will be appended to the status prefix.
# In a real application, this would likely be fetched from a database, sensor,
# or another service, but here it's hardcoded for demonstration.
NDT_STATUS_DETAIL = "READY (Data pipeline active)"

# Define the port the server will run on. Default to 8000, but can be
# overridden by the environment variable PORT for easy deployment.
SERVER_PORT = int(os.environ.get("PORT", 10000))

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
    """
    # Combine the required prefix with the current status variable
    full_status_message = f"{BASE_STATUS_PREFIX} {NDT_STATUS_DETAIL}"

    # FastAPI automatically handles converting the returned string into a
    # successful (200 OK) plain text or JSON response.
    return full_status_message


# --- Server Startup ---

if __name__ == "__main__":
    # To run this server, you must first install the required libraries:
    # pip install fastapi uvicorn
    print(f"Starting server on http://127.0.0.1:{SERVER_PORT}")
    print(f"Access the status at: http://127.0.0.1:{SERVER_PORT}/status")

    # Start the Uvicorn server instance
    uvicorn.run(
        app,
        host="0.0.0.0",  # Listen on all interfaces
        port=SERVER_PORT
    )
