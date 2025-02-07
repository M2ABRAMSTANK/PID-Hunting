import obd

# Connect to the first detected USB OBD-II adapter
connection = obd.OBD("/dev/tty.usbserial-130")

if connection.is_connected():
    print("Connected to OBD-II adapter!")

    # Send a request for vehicle RPM
    response = connection.query(obd.commands.RPM)
    print("RPM:", response.value)

else:
    print("Failed to connect.")
