from collections import OrderedDict
import json
import os
import argparse
import sys
import bluetooth


class Archivo: 
    def Leer_Archivo(self,nombre,ruta):
        with open(str(ruta)+str(nombre),"r+") as archivo_conf:
            self.archivo_string = str(archivo_conf.read())
            self.archivo_json = json.dumps(self.archivo_string)
            return json.loads(self.archivo_json)



parser= argparse.ArgumentParser()
parser.add_argument("-json",help="message to send")
args= parser.parse_args()
leer_archivo = Archivo()
json_leer = json.loads(leer_archivo.Leer_Archivo("conf_l.json","/home/pi/Desktop/NODO_2/comunicacion/"))
mac = str(json_leer['interfaces'][1]['mac'])
port = int(json_leer['interfaces'][1]['port'])
info_socket = (mac,port) # tupla de string + int

try:
    mac = json_leer['interfaces'][1]['mac']
    port = int(json_leer['interfaces'][1]['port'])
    sock=bluetooth.BluetoothSocket( bluetooth.RFCOMM )
    sock.connect(info_socket)
    mensaje= args.json
    sock.send(mensaje)
    sock.close()

except(bluetooth.btcommon.BluetoothError):
    print('fallo conexion con servidor Bluetooth')

