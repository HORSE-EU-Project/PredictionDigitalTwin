import subprocess
import time
import os

def run_external_script_non_blocking(script_path):
    """
    Runs an external bash script in a non-blocking way.
    The main Python program will continue its execution immediately.
    """
    if not os.path.exists(script_path):
        print(f"Error: Script '{script_path}' not found.")
        return

    # Make the script executable if it isn't already
    # This is important for security and permissions, ensure you trust the script.
    # In a real-world scenario, you might pre-set permissions or handle this differently.
    os.chmod(script_path, 0o755)

    try:
        # Use subprocess.Popen to run the script.
        # This starts the script in a new process and returns immediately.
        # shell=True is convenient for simple scripts but can be a security risk
        # if user input is part of the command string.
        # For this simple case, it's acceptable.
        # For more control and security, pass a list of arguments directly:
        # Popen(['/bin/bash', script_path], ...)
        process = subprocess.Popen(['/bin/bash', script_path])
        print(f"Started external script '{script_path}' with PID: {process.pid}")
        return process
    except Exception as e:
        print(f"An error occurred while trying to run the script: {e}")
        return None

if __name__ == "__main__":
    script_to_run = "run.sh"

    print("Main program: Starting background script...")
    # Run the script non-blocking
    script_process = run_external_script_non_blocking(script_to_run)

    if script_process:
        print("Main program: Continuing its own tasks...")
        # Simulate some work in the main program
        for i in range(3):
            print(f"Main program: Doing task {i+1}...")
            time.sleep(2)

        print("Main program: Done with its immediate tasks.")
        print(f"Main program: Script '{script_to_run}' is likely still running in the background.")

        # You can optionally wait for the script to finish later if needed,
        # or just let it run independently.
        # For example, to wait and get the exit code:
        # print("Main program: Waiting for the background script to complete...")
        # exit_code = script_process.wait()
        # print(f"Main program: Background script finished with exit code {exit_code}")
    else:
        print("Main program: Could not start the background script.")

    print("Main program: Exiting.")
