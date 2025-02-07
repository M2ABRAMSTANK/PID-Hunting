#!/usr/bin/env python3
import serial
import time
import logging
import argparse

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] %(message)s')

class OBDScanner:
    """
    A simple wrapper for communicating with an OBD-II adapter
    using a serial (USB) connection.
    """
    def __init__(self, port, baudrate=38400, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        try:
            self.ser = serial.Serial(port, baudrate=baudrate, timeout=timeout)
            logging.info("Connected to OBD-II adapter on %s", port)
        except serial.SerialException as e:
            logging.error("Error opening serial port %s: %s", port, e)
            raise

    def send_command(self, cmd, delay=0.2):
        """
        Send an AT command to the adapter (appends a carriage return),
        waits a short period, and then reads the response.
        """
        # Prepare the command by ensuring proper termination
        command = cmd.strip() + "\r"
        logging.debug("Sending: %s", command)
        self.ser.write(command.encode('utf-8'))
        time.sleep(delay)
        response = self.read_response()
        logging.debug("Received: %s", response)
        return response

    def read_response(self):
        """
        Read all available data from the serial port.
        """
        response = self.ser.read_all().decode('utf-8', errors='replace').strip()
        return response

    def close(self):
        if self.ser:
            self.ser.close()

def is_valid_response(response):
    """
    Checks whether the response from the OBD-II adapter appears to contain valid data.
    This is a placeholder function—you may need to refine it to match your adapter's error messages.
    """
    if not response:
        return False
    # Some common error responses from many OBD-II adapters:
    invalid_responses = ['?', 'NO DATA', 'UNABLE TO CONNECT']
    for invalid in invalid_responses:
        if invalid in response.upper():
            return False
    return True

def scan_pid_for_ecu(scanner, ecu, pid, use_extended=False):
    """
    Sends a sequence of configuration and query commands to scan a given ECU with a PID.
    
    The sequence below is based on your sample:
    
        ATST96
        ATSH6F1              (or ATFCSH6F1 if extended)
        ATCEA01
        ATCRA601
        ATFCSD01300000
        ATFCSM1
        224002

    In this sample, the ECU address (e.g. "6F1") is set first, and then
    a target ECU “slot” (here shown as "01") is used in later commands. Adjust as needed.
    """
    # Set the timeout (or other global settings)
    scanner.send_command("ATST96")

    # Set the header. If extended addressing is required, use a different command.
    if not use_extended:
        header_cmd = "ATSH" + ecu
    else:
        header_cmd = "ATFCSH" + ecu
    scanner.send_command(header_cmd)
    
    # In our sample the next commands appear to set a “target ECU” address.
    # For demonstration we use a fixed target address ("01"). In a real
    # application you might compute or look up this value.
    target_addr = "01"
    cmds = [
        "ATCEA" + target_addr,
        "ATCRA6" + target_addr,
        # Note: The sample shows the PID appended to "ATFCSD0", i.e.
        # ATFCSD0[PID]. Ensure your PID string is formatted appropriately.
        "ATFCSD0" + pid,
        "ATFCSM1"
    ]
    for cmd in cmds:
        scanner.send_command(cmd)

    # Finally, send the actual PID command. (In this example, the PID is sent as-is.)
    pid_response = scanner.send_command(pid)
    return pid_response

def main():
    parser = argparse.ArgumentParser(
        description="ECU/PID Scanner using a USB OBD-II adapter. "
                    "The program cycles through each ECU in the list and queries each PID."
    )
    parser.add_argument("--port", required=True,
                        help="Serial port for the OBD-II adapter (e.g., COM3 or /dev/ttyUSB0)")
    parser.add_argument("--baudrate", type=int, default=38400,
                        help="Serial communication baudrate (default: 38400)")
    parser.add_argument("--extended", action="store_true",
                        help="Use extended addressing (sends ATFCSH commands instead of ATSH)")
    parser.add_argument("--ecus", nargs="+", required=True,
                        help="List of known ECU addresses as hex strings (e.g., 6F1 A06 A08)")
    parser.add_argument("--pids", nargs="+", required=True,
                        help="List of known PID values as hex strings (e.g., 224002)")
    args = parser.parse_args()

    # Open the serial connection to the OBD-II adapter
    scanner = OBDScanner(args.port, args.baudrate)

    valid_results = []  # To store ECU/PID pairs that produce a valid response

    try:
        # Loop through each ECU and each PID
        for ecu in args.ecus:
            for pid in args.pids:
                logging.info("Scanning ECU %s with PID %s", ecu, pid)
                response = scan_pid_for_ecu(scanner, ecu, pid, use_extended=args.extended)
                if is_valid_response(response):
                    logging.info("Valid response from ECU %s, PID %s: %s", ecu, pid, response)
                    valid_results.append((ecu, pid, response))
                else:
                    logging.info("No valid data from ECU %s, PID %s", ecu, pid)
    finally:
        scanner.close()

    # Report the results
    print("\nScan Complete. Valid ECU/PID responses:")
    for ecu, pid, resp in valid_results:
        print(f"ECU: {ecu} | PID: {pid} | Response: {resp}")

if __name__ == "__main__":
    main()
