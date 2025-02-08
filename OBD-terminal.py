import serial
import time
import logging
import argparse

def setup_logging():
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')

def initialize_obd(port, baudrate=38400, timeout=1):
    try:
        ser = serial.Serial(port, baudrate=baudrate, timeout=timeout)
        logging.info("Connected to OBD-II adapter on %s", port)
        
        init_commands = ["ATWS", "ATE0", "ATM0", "ATS0", "ATAT1", "ATH1", "ATSP6", "ATS0", "ATDPN"]
        for cmd in init_commands:
            send_command(ser, cmd)
        logging.info("Initialization commands sent.")
        
        return ser
    except serial.SerialException as e:
        logging.error("Error opening serial port %s: %s", port, e)
        return None

def send_command(ser, cmd, delay=None):
    if ser:
        # Choose delay based on command
        if delay is None:
            delay = 0.7 if cmd.strip().startswith("22") else 0.3
        command = cmd.strip() + "\r"
        logging.debug("Sending: %s", command)
        ser.write(command.encode('utf-8'))
        time.sleep(delay)
        response = read_response(ser)
        logging.debug("Received: %s", response)
        return response
    return "Serial connection not available."

def read_response(ser):
    if ser:
        response = ser.read_all().decode('utf-8', errors='replace').strip()
        return response
    return ""

def interactive_terminal(ser):
    print("\nOBD-II Terminal. Type commands to send to the adapter.")
    print("Type 'exit' to quit.")
    
    while True:
        cmd = input("OBD> ").strip()
        if cmd.lower() == 'exit':
            break
        response = send_command(ser, cmd)
        print(response)

def main():
    parser = argparse.ArgumentParser(description="Interactive OBD-II Terminal using a USB adapter.")
    parser.add_argument("--port", required=True, help="Serial port for the OBD-II adapter (e.g., COM3 or /dev/ttyUSB0)")
    parser.add_argument("--baudrate", type=int, default=38400, help="Serial communication baudrate (default: 38400)")
    args = parser.parse_args()
    
    setup_logging()
    ser = initialize_obd(args.port, args.baudrate)
    
    if ser:
        try:
            interactive_terminal(ser)
        finally:
            ser.close()
            logging.info("Serial connection closed.")
    else:
        logging.error("Failed to initialize OBD-II adapter.")

if __name__ == "__main__":
    main()
