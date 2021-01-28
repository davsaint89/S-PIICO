import serial
import sys
import argparse
import json

try:

    parser= argparse.ArgumentParser()
    parser.add_argument("-json",help="message to send")
    args=parser.parse_args()
    dat= args.json
    ser = serial.Serial('/dev/ttyUSB0', 9600,timeout=5) # el timeout debe ser el mismo en cliente y servidor
    ser.write(str.encode(dat + "\r\n"))

except serial.serialutil.SerialException:
    print('Error: módulo Xbee desconectado')

