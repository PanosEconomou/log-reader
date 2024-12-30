# Vassilis Economou data from microbit to .xlsx 

import serial
import serial.tools.list_ports as list_ports
import inquirer
import csv
from datetime import datetime
import signal
import sys
import os

# Select a port in a platform independent way
def pick_port():
    # Get the ports
    ports = list_ports.comports()
    
    # Select the connected ones only
    connected = [port for port in ports if port.description != "n/a"]

    # start the picking process
    questions = [inquirer.List('port',
                               message="Επιλέξτε τη θύρα του microprocessor",
                               choices=[(port.description,port) for port in connected]
                               ),]
    # Get the port that the user selected
    port_selected = inquirer.prompt(questions)

    return port_selected['port']

# Select an output file
def pick_output_location():
    # Create the question
    questions = [inquirer.Path('file',
                    message='Πού πρέπει να βρίσκονται τα αρχεία καταγραφής;',
                    default=os.path.join(os.getcwd(),"sensor_data.csv"),
                    path_type=inquirer.Path.FILE
                ),]
    
    # Get the path from the user
    path_selected = inquirer.prompt(questions)
    path = path_selected['file']

    # Make the path absolute
    path = os.path.abspath(os.path.expanduser(path))

    # Ensure that it is a csv file
    if not path.endswith('.csv'):
        if os.path.isdir(path):
            path = os.path.join(path,"sensor_data.csv") 
        else:
            path+= '.csv'

    # Ensure that the path exists
    directory = os.path.dirname(path)
    if not os.path.exists(directory):
        os.makedirs(directory)

    if not os.path.exists(path):
        with open(path,'w') as file:
            file.write('')
            print(f"Το αρχείο {path} δημιουργήθηκε")

    return path

# Pick baud rate
def pick_baud_rate():
    questions = [inquirer.List('baudrate',
                               message="Επιλέξτε το baud rate",
                               default=9600,
                               choices=[4800, 9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600]
        ),]
    rate_selected = inquirer.prompt(questions)
    return rate_selected['baudrate']

# Χειρισμός σήματος διακοπής
def signal_handler(sig, frame):
    print("\nΔιακοπή από τον χρήστη. Κλείσιμο σύνδεσης...")
    ser.close()
    print(f"Τα δεδομένα αποθηκεύτηκαν στο '{path}'.")
    sys.exit(0)

if __name__ == "__main__":   

    print("Εφαρμογή αυτόματης καταγραφής σε αρχείο (.csv) μετρήσεων από αισθητήρες v.1.0.0")

    # Port selection
    port = pick_port()

    # Baud rate selection
    baudrate = pick_baud_rate();

    # Σύνδεση στη σειριακή θύρα
    try:
        ser = serial.Serial(port.device, baudrate=baudrate, timeout=1)
        print("Σύνδεση επιτυχής στη θύρα!")
    except Exception as e:
        print(f"Αδυναμία σύνδεσης στη θύρα! Λεπτομέρειες: {e}")
        sys.exit()

    # Pick a file for the log
    path = pick_output_location()

    with open(path, mode='w', newline='') as file:
        # Δημιουργία αρχείου csv
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Sensor Data"])

        signal.signal(signal.SIGINT, signal_handler)  # SIGINT = Ctrl+C

        # Καταγραφή δεδομένων
        try:
            print("Πατήστε Ctrl + C (ή Command + .) για να σταματήσετε την καταγραφή.")
            while True:
                try:
                    line = ser.readline().decode('utf-8').strip()  # Ανάγνωση δεδομένων
                    if line:
                        print("Καταγραφή: ", line)
                        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        writer.writerow([timestamp, line])
                except UnicodeDecodeError:
                    # Χειρισμός μη έγκυρων δεδομένων
                    print("Μη έγκυρα δεδομένα αγνοήθηκαν.")
        except Exception as e:
            print(f"Σφάλμα: {e}")
        finally:
            ser.close()
