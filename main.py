import argparse
import json
import paho.mqtt.client as mqtt
import datetime
import threading
import time
from gpiozero import LED
from time import sleep
from datetime import date, datetime, time, timedelta
import paho.mqtt.subscribe as subscribe
import paho.mqtt.client as mqtt
import sys
import os
import paho.mqtt.publish as publish
import calendar
from gpiozero import MCP3008
from gpiozero import Button
import board
import busio
import adafruit_am2320
import math
import traceback
from air_speed import speed_data
from pluviometer import rain_data
from AM2315 import tem_data, hum_data
from estado_actuador import estado_valvula
import RPi.GPIO as GPIO
from wifi_update import createWifiConfig
#Variables GLOBALES
PYTHONHASHSEED=0 # IMPORTANTE ORDENAR para evitar desorden en el json por XBEE y error en servidor zigbee
hostname = ""
puerto = 0  
adc1 = MCP3008 (channel=1)
adc0 = MCP3008 (channel=0)
electrovalve = LED(21)
humi = False
radi = False
velo = False
dire = False
pluv = False
temp = False
indZigbee = False
indBlue = False
indPublicador = False
########################################

hashseed = os.getenv('PYTHONHASHSEED')
if not hashseed:
    os.environ['PYTHONHASHSEED'] = '0'
    os.execv(sys.executable, [sys.executable] + sys.argv)


channel = 21
GPIO.setmode(GPIO.BCM)  
# Setup your channel
GPIO.setup(channel, GPIO.OUT)

def lectura_estado(tipo):

    with open('conf_l.json') as file:
        datajson = json.load(file)
        for sensor in datajson['sensors']:
            if sensor['type'] == tipo:
                return sensor['state']

def lectura_ide(tipo):

    with open('conf_l.json') as file:
        datajson = json.load(file)
        for sensor in datajson['sensors']:
            if sensor['type'] == tipo:
                return sensor['sensor_id']


def id_node():
     with open('conf_l.json') as file:
        datajson = json.load(file)
        return datajson['node_id']

################# metodos actuador ##############

def lectura_estadoAc(tipo):

    with open('conf_l.json') as file:
        datajson = json.load(file)
        for actuator in datajson['actuators']:
            if actuator['type'] == tipo:
                return actuator['state']


def lectura_ideAc(tipo):

    with open('conf_l.json') as file:
        datajson = json.load(file)
        for actuator in datajson['actuators']:
            if actuator['type'] == tipo:
                return actuator['actuator_id']


#################    Actuador    ################ 
class Actuator():
    def __init__(self,typ,sta,ide,valve):
        self.__ide = ide
        self.__sta = sta
        self.__typ = typ
        self.__valve = valve

    def getIde(self):
        return self.__ide

    def setIde(self,ide):
        self.__ide=ide    
    
    def getTyp(self):
        return self.__typ
    
    def setTyp(self,typ):
        self.__typ=typ      
    
    def getSta(self):
        return self.__sta
    
    def setSta(self,sta):
        self.__sta=sta

    def getValve(self):
        return self.__valve
    
    def setValve(self,valve):
        self.__valve=valve

    def toJason(self):
        self.__attributes = {"type" : "-","actuator_id" : "-","state":"-","valvula":"-"}
        self.__attributes["type"]=self.getTyp()
        self.__attributes["actuator_id"]=self.getIde()
        self.__attributes["state"]=self.getSta()
        self.__attributes["valvula"]=self.getValve()
        self.__datajson = json.dumps(self.__attributes, indent=4,separators=(',',':'),sort_keys=False)
        return self.__datajson

    def __str__(self):           
        return self.toJason()

class ReadActuator():
    def __init__(self):
        self.__actuators=[]

    
    def create_electro(self,typ):
        
        typ = typ
        state = lectura_estadoAc(typ)
        ide = lectura_ideAc(typ)
        valve = estado_valvula(21) # se le ingresa el canal o pin
        if state == 'enabled':
            return Actuator(typ,state,ide,valve).toJason()  

    def createActuator(self,actuatorType):
        if actuatorType == 'asp':              
            return self.create_electro('asp')


##############  Sensores    ###################
class Sensor():
    def __init__(self,typ,ide,mag,val,sta):
        self.__ide=ide
        self.__typ=typ
        self.__mag=mag
        self.__val=val
        self.__sta = sta
    
    def getIde(self):
        return self.__ide
    
    def setIde(self,ide):
        self.__ide=ide    
    
    def getTyp(self):
        return self.__typ
    
    def setTyp(self,typ):
        self.__typ=typ      
    
    def getSta(self):
        return self.__sta
    
    def setSta(self,sta):
        self.__sta=sta   

    def getMag(self):
        return self.__mag
    
    def setMag(self,mag):
        self.__mag=mag
    
    def getVal(self):
        return self.__val
    
    def setVal(self,val):
        self.__val=val
        
    def toJason(self):
        self.__attributes = {"type" : "-","sensor_id" : "-","value" : "-", "magnitude" : "-","state":"-"}
        self.__attributes["type"]=self.getTyp()
        self.__attributes["sensor_id"]=self.getIde()
        self.__attributes["value"]=self.getVal()
        self.__attributes["magnitude"]=self.getMag()
        self.__attributes["state"]=self.getSta()
        self.__datajson = json.dumps(self.__attributes, indent=4,separators=(',',':'),sort_keys=False)
        return self.__datajson
    
    def __str__(self):           
        return self.toJason()


class ReadSensor():
    def __init__(self):
        self.__sensors=[]
    
    
    def create_temp(self,typ):
        global temperature
        global am2315t
        global temp
        typ = typ
        state = lectura_estado(typ)
        ide = lectura_ide(typ)
        mag = 'Celsius'
        if state == 'enabled' and temp == True:
            am2315t = 'on'
            value = tem_data()          
            return Sensor(typ,ide,mag,value,state).toJason()

    def create_hum(self,typ):
        global humi
        typ = typ
        state = lectura_estado(typ)
        ide = lectura_ide(typ)
        mag = 'Porcentage'
        if state == 'enabled' and humi == True:
            value = hum_data()
            return Sensor(typ,ide,mag,value,state).toJason()

    def create_rad(self,typ):
        global radi
        typ = typ
        state = lectura_estado(typ)
        ide = lectura_ide(typ)
        mag = 'W/m2'
        if state == 'enabled' and radi == True:
            value = "{0:.3f}".format(adc0.value*1800.0)
            return Sensor(typ,ide,mag,value,state).toJason()
            

    def create_dir(self,typ):
        global dire
        direction = ""
        valoradc1 = round(adc1.value*3.3,2) #redondea a un entero con 2 decimales
        typ = typ
        state = lectura_estado(typ)
        ide = lectura_ide(typ)
        #print(valoradc1)
        if   valoradc1 == 0.1:
            direction = 'ESTE'
        elif valoradc1 >= 0.2 and valoradc1 <0.4:
            direction =  'SUR-ESTE'
        elif valoradc1 >= 0.4 and valoradc1 <0.7:
            direction =  'SUR'
        elif valoradc1 >= 0.7 and valoradc1 <1.2:
            direction =  'NOR-ESTE'
        elif valoradc1 >= 1.2 and valoradc1 <1.8:
            direction =  'SUR-OESTE'
        elif valoradc1 >= 1.8 and valoradc1 <2.3:
            direction =  'NORTE'
        elif valoradc1 >= 2.4 and valoradc1 <2.7:
            direction =  'NOR-OESTE'
        elif valoradc1 >= 2.7:
            direction =  'OESTE'
        mag = 'Cardinal_point'
        if state == 'enabled' and dire == True:
            value = direction
            return Sensor(typ,ide,mag,value,state).toJason()

    def create_vel(self,typ):
        global velo
        typ = typ
        state = lectura_estado(typ)
        ide = lectura_ide(typ)
        mag = 'Km/h'
        if state == 'enabled' and velo == True:
            value = "{0:.2f}".format(speed_data())
            return Sensor(typ,ide,mag,value,state).toJason()

    def create_plu(self,typ):
        global pluv
        typ = typ
        state = lectura_estado(typ)
        ide = lectura_ide(typ)
        mag = 'mm'
        if state == 'enabled' and pluv == True:
            value = rain_data()
            return Sensor(typ,ide,mag,value,state).toJason()    
        
    def createSensor(self,sensorType):
        if sensorType == 'tem':            
            return self.create_temp('tem') # depende del archivo de entrada  
        elif sensorType == 'hum':
            return self.create_hum('hum') 
        elif sensorType == 'vel':
            return self.create_vel('vel') 
        elif sensorType == 'dir':
            return self.create_dir('dir')
        elif sensorType == 'plu':
            return self.create_plu('plu') 
        elif sensorType == 'rad':
            return self.create_rad('rad')
########################################

class EstadoAct: 
    def armar_json(self,data):
        hoy= datetime.today()
        formatdate= "%d/%m/%Y %H:%M:%S"
        now = hoy.strftime(formatdate)
        gps = {
        "lon": 4.25,
        "lat": -75.8
        }
        
        leer_archivo = Archivo()
        leer_conf = json.loads(leer_archivo.Leer_Archivo("conf_l.json","/home/pi/Desktop/NODO_2/comunicacion/"))
        nuevo_json = {}
        nuevo_json['node_id']= data['node_id']
        nuevo_json['date'] = now
        if (indPublicador == True) or (indZigbee == True) or (indBlue == True):
            nuevo_json['state']  = "sending"
        else:
            nuevo_json['state'] = "listening"
        nuevo_json['broker'] ={}
        nuevo_json['broker']['publish'] = []
        nuevo_json['broker']['suscribe'] = []
        nuevo_json['interfaces'] = []
        nuevo_json['sensors'] =[]
        nuevo_json['actuators'] =[]
        
        if data['information']['mqtt'] == "true":
            nuevo_json['broker']['ip'] = leer_conf['broker']['broker_address']
            nuevo_json['broker']['port'] = leer_conf['broker']['port']
            nuevo_json['broker']['qos'] = leer_conf['broker']['qos']
            nuevo_json['broker']['user'] = leer_conf['broker']['user']
            nuevo_json['broker']['publish'].append({
                                "type": "sen_l"})
            nuevo_json['broker']['publish'].append({
                                "type": "sta_l"})
            nuevo_json['broker']['suscribe'].append({
                                "type": "conf_l"})
            nuevo_json['broker']['suscribe'].append({
                                "type": "req_l"})
            nuevo_json['broker']['suscribe'].append({
                                "type": "act_l"})
        if data['information']['location'] == 'true':
            nuevo_json['gps'] = gps

        if data['information']['interfaces'] == "true":
            for interfaz in leer_conf['interfaces']:
                if interfaz['type'] == "wifi":
                    nuevo_json['interfaces'].append({
                                "type": "wifi",
                                "state": 'enabled',
                                "dir": ""+leer_conf['broker']['broker_address']+"" })
                if interfaz['type'] == "blue":
                    nuevo_json['interfaces'].append({
                                "type": "blue",
                                "state": 'enabled',
                                "mac": ""+interfaz['mac']+"",
                                "mode": "direct"})
                if interfaz['type'] == "xbee":
                    nuevo_json['interfaces'].append({
                                "type": "xbee",
                                "state": 'enabled',
                                "pan_id": "1234",
                                "mac": ""+interfaz['mac']+""})
        if data['information']['sensors'] == "true":
            
            for sensor in leer_conf['sensors']:
                if sensor['type'] == "tem":
                    nuevo_json['sensors'].append({
                                "sensor_id": "Temperature",
                                "state": 'enabled', 
                                "on":str(temp)})
                if sensor['type'] == "hum":
                    nuevo_json['sensors'].append({
                                "sensor_id": "Humidity",
                                "state": 'enabled',
                                "on":str(humi)})
                if sensor['type'] == "vel":
                    nuevo_json['sensors'].append({
                                "sensor_id": "Velocity",
                                "state": 'enabled',
                                "on":str(velo)})
                if sensor['type'] == "dir":
                    nuevo_json['sensors'].append({
                                "sensor_id": "Direction",
                                "state": 'enabled',
                                "on":str(dire)})
                if sensor['type'] == "plu":
                    nuevo_json['sensors'].append({
                                "sensor_id": "Pluviometer",
                                "state": 'enabled',
                                "on":str(pluv)})
                if sensor['type'] == "rad":
                    nuevo_json['sensors'].append({
                                "sensor_id": "Radiation",
                                "state": 'enabled',
                                "on":str(radi)})
        if data['information']['actuators'] == "true":

            nuevo_json['actuators'] =[]
            with open('conf_l.json') as file:

                    datajson = json.load(file)
                    
                    for actuator in datajson['actuators']:
                        #print(actuator['type'])
                        estacion_act = ReadActuator().createActuator(actuator['type'])
                
                        nuevo_json['actuators'].append(json.loads(estacion_act))
        return nuevo_json

#Creacion del json de estado del nodo sta_l, tanto para req_l info como act_l info

#Modo de escucha suscriptor
class ConexionMqtt: 
    def sucriptor(self, hostSub, puertoSub):
        client = mqtt.Client(client_id='Sevin', clean_session=False)
        client.on_connect = on_connect
        client.on_message = on_message
        print("hostname= ",hostSub,"puerto= ",puertoSub)
        client.connect(host=hostSub, port=puertoSub, keepalive = 1200)
        client.loop_forever()
#Modo de envio de informacion de los sensores sen_l
class ConexionPub: 
    def publicadorMas(self, topicoPub, mensajePub):
        leer_archivo = Archivo()
        json_leer = json.loads(leer_archivo.Leer_Archivo("conf_l.json","/home/pi/Desktop/NODO_2/comunicacion/"))
        hostPub = json_leer['broker']['broker_address']
        puertoPub = int(json_leer['broker']['port'])
        
def sensado():
    leer_archivo = Archivo()
    json_leer = json.loads(leer_archivo.Leer_Archivo("conf_l.json","/home/pi/Desktop/NODO_2/comunicacion/"))
    host = json_leer['broker']['broker_address']
    #print(host)
    qos = int(json_leer['broker']['qos'])

    while indPublicador == True:   
        hoy= datetime.today()
        formatdate= "%d/%m/%Y %H:%M:%S"
        now = hoy.strftime(formatdate)
        nuevo_json = {}
        gps = {
        "lon": -72.85,
        "lat": 4.85
        }
        nuevo_json['gps'] = gps
        nuevo_json['node_id']= id_node()
        nuevo_json['date'] = now
        nuevo_json['sensors'] =[]
        nuevo_json['protocols'] = []
        nuevo_json['protocols'].append('Wifi')

        if indBlue == True:
            nuevo_json['protocols'].append('Bluetooth')
            if indZigbee== True:
                nuevo_json['protocols'].append('Zigbee')
        elif indZigbee == True:
            nuevo_json['protocols'].append('Zigbee')
            if indBlue== True:
                nuevo_json['protocols'].append('Bluetooth')
        
        with open('conf_l.json') as file:
            datajson = json.load(file)
            for sensor in datajson['sensors']:
                estacion = ReadSensor().createSensor(sensor['type'])
                if estacion != None:
                    nuevo_json['sensors'].append(json.loads(estacion))
        mensaje = json.dumps(nuevo_json, indent=4,sort_keys=True)
        publish.single("sen_l",mensaje, hostname=host, keepalive=2000,qos=qos)
        sleep(int(json_leer['send_frequency']))

def sensado_zigbee():
    
    leer_archivo = Archivo()
    json_leer = json.loads(leer_archivo.Leer_Archivo("conf_l.json","/home/pi/Desktop/NODO_2/comunicacion/"))
    while indZigbee == True:
           
        hoy= datetime.today()
        formatdate= "%d/%m/%Y %H:%M:%S"
        now = hoy.strftime(formatdate)
        nuevo_json = {}
        gps = {
        "lon": -72.85,
        "lat": 4.85
        }
        nuevo_json['gps'] = gps
        nuevo_json['node_id']= id_node()
        nuevo_json['date'] = now
        nuevo_json['sensors'] =[]
        nuevo_json['protocols'] = []
        nuevo_json['protocols'].append('Zigbee')
        
        if indBlue == True:
            nuevo_json['protocols'].append('Bluetooth')
            if indPublicador== True:
                nuevo_json['protocols'].append('Wifi')
        elif indPublicador == True:
            nuevo_json['protocols'].append('Wifi')
            if indBlue== True:
                nuevo_json['protocols'].append('Bluetooth')


        with open('conf_l.json') as file:
            datajson = json.load(file)
            for sensor in datajson['sensors']:
                estacion = ReadSensor().createSensor(sensor['type'])
                if estacion != None:
                    nuevo_json['sensors'].append(json.loads(estacion))
        mensaje = json.dumps(nuevo_json, sort_keys=True)  
        #print(mensaje)
        send = "python3 xbee_send.py -json '%s'" % mensaje
        os.system(send)
        #print(json_leer['send_frequency'])
        sleep(int(json_leer['send_frequency']))
        # if indBlue == True:
        #     send1 = "python3 blue_send.py -json '%s'" % mensaje
        #     os.system(send1)

def bluetooth():
    leer_archivo = Archivo()
    json_leer = json.loads(leer_archivo.Leer_Archivo("conf_l.json","/home/pi/Desktop/NODO_2/comunicacion/"))
    while indBlue == True:   
        hoy= datetime.today()
        formatdate= "%d/%m/%Y %H:%M:%S"
        now = hoy.strftime(formatdate)
        nuevo_json = {}
        gps = {
        "lon": -72.85,
        "lat": 4.85
        }
        #nuevo_json['protocolo'] = "bluetooth"
        nuevo_json['gps'] = gps
        nuevo_json['node_id']= id_node()
        nuevo_json['date'] = now
        nuevo_json['sensors'] =[]
        nuevo_json['protocols'] = []
        nuevo_json['protocols'].append('Bluetooth')
        
        if indPublicador == True:
            nuevo_json['protocols'].append('Wifi')
            if indZigbee== True:
                nuevo_json['protocols'].append('Zigbee')
        elif indZigbee == True:
            nuevo_json['protocols'].append('Zigbee')
            if indPublicador== True:
                nuevo_json['protocols'].append('Wifi')
        
        with open('conf_l.json') as file:
            datajson = json.load(file)
            for sensor in datajson['sensors']:
                estacion = ReadSensor().createSensor(sensor['type'])
                if estacion != None:
                    nuevo_json['sensors'].append(json.loads(estacion))
        message = json.dumps(nuevo_json, indent=4,sort_keys=True)
        carga = "python3 blue_send.py -json '%s'" % message
        os.system(carga)
        sleep(int(json_leer['send_frequency']))
    #print('mensaje enviado')

#Envio de estado del nodo sta_l
class ConexionSta: 
    def publicador(self, topicoPubSta, mensajePubSta):
        leer_archivo = Archivo()
        json_leer = json.loads(leer_archivo.Leer_Archivo("conf_l.json","/home/pi/Desktop/NODO_2/comunicacion/"))
        hostPubSta = json_leer['broker']['broker_address']
        puertoPubSta = int(json_leer['broker']['port'])
        service = mqtt.Client('piicoPub') # Creación del cliente?Ė
        service.connect(host= hostPubSta, port=puertoPubSta)
        topic = topicoPubSta
        mensaje = mensajePubSta
        service.publish(topic, json.dumps(mensaje))  

#Clase para leer el archivo
class Archivo: 
    def Leer_Archivo(self,nombre,ruta):
        with open(str(ruta)+str(nombre),"r+") as archivo_conf:
            self.archivo_string = str(archivo_conf.read())
            self.archivo_json = json.dumps(self.archivo_string)
            return json.loads(self.archivo_json)

#Argumentos de entrada para el programa de PYTHON
parser = argparse.ArgumentParser(
    prog='Estacion PIICO USB',
    description='Comandos para el inicio de la estacion.',
    epilog="mas informacion en https://piico.ingusb.com",
    add_help=True
)
parser.add_argument(
    '-v','--version',
    dest='version',
    action='version',
    version='%(prog)s 1.0'
)
parser.add_argument(
    '-n','--name', '--nameid',
    dest='name',
    required=True,
    nargs=1,
    type=str,
    help='nombre identificador del nodo'
)
parser.add_argument(
    '-p','--pass', '--password',
    dest='password',
    required=True,
    nargs=1,
    type=str,
    help='Contraseña identificador del actuador a activar'
)
#Transformacion del mensaje
def json_decode(data):  
    string_data = data.decode('ASCII')
    json_data = json.loads(string_data)
    return json_data

#Conexion del suscriptor por medio de cuales topicos
def on_connect(client, userdata, flags, rc): 
    client.subscribe([("conf_l", 2),("req_l", 2),("act_l",2)])

#Analisis del mensaje que recibimos del publicador, segun el topico, el nodo publica la informacion correspondiente
def on_message(client, userdata, message):
    global pluv, humi, radi, temp, velo, dire
    global indPublicador, indZigbee, indBlue # banderas para activar transmisión de datos en hilos
    construir_json = EstadoAct()
    brokerPub = ConexionPub()
    brokerPubSta = ConexionSta()
    construir_json = EstadoAct()
    

    topico = message.topic
    json_resultado = json_decode(message.payload)
    print(topico)
    print(json_resultado['node_id'])
    if json_resultado['node_id'] == 'estacion_2':
        if topico == "conf_l":

            nuevared = json_resultado['interfaces'][0]['ssid']
            print(nuevared)
            newpass = json_resultado['interfaces'][0]['psk']
            print(newpass)
            archivo = open('/home/pi/Desktop/NODO_2/comunicacion/conf_l.json','r')
            data_conf = json.load(archivo)
            archivo.close()
            oldred = data_conf['interfaces'][0]['ssid']
            oldpass = data_conf['interfaces'][0]['psk']

            if nuevared != oldred:
                createWifiConfig(nuevared,newpass) # añade red en wpa_supplicant
            else:
                if newpass != oldpass:
                    createWifiConfig(nuevared,newpass)
            print("Nuevo archivo de configuración almacenado y sobreescribido")
            with open("/home/pi/Desktop/NODO_2/comunicacion/conf_l.json","r+") as archivo_conf:
                    archivo_conf.seek(0)
                    archivo_conf.truncate()
                    archivo_conf.seek(0)
                    archivo_conf.writelines(json.dumps(json_resultado))
            leer_archivo = Archivo()
            json_leer = json.loads(leer_archivo.Leer_Archivo("conf_l.json","/home/pi/Desktop/NODO_2/comunicacion/"))
            os.system("sudo reboot")
            

        elif topico == "req_l":
            data = json_decode(message.payload)
            if data['request'] == "send":
                for i in range(3):
                    protocolo = data['protocols'][i]['network']
                    if protocolo == 'wifi':
                        indPublicador = True
                        print('wifi')
                    elif protocolo == 'zigbee':
                        print('zigbee')
                        indZigbee = True
                    elif protocolo == 'bluetooth':
                        indBlue = True
                        print('blue')
                        
                for sensor in data['sensors']:      
                    if sensor['sensor_id'] == "Temperature":
                        temp = True  
                    elif sensor['sensor_id'] == "Humidity":
                        humi = True
                    elif sensor['sensor_id'] == "Velocity":
                        velo = True
                    elif sensor['sensor_id'] == "Direction":
                        dire = True
                    elif sensor['sensor_id'] == "Radiation":
                        radi = True   
                    elif sensor['sensor_id'] == "Pluviometer":
                        pluv = True
                hilo = threading.Thread(target=bluetooth)
                hilo.start()
                hilo1 = threading.Thread(target=sensado_zigbee)
                hilo1.start()
                hilo2 = threading.Thread(target=sensado)
                hilo2.start()

            elif data['request'] == "stop":
                indPublicador = False
                indZigbee = False
                indBlue = False
                pluv = False
                radi = False
                temp = False
                velo = False
                dire = False
                humi = False
            elif data['request'] == "info":
                nuevo_json = construir_json.armar_json(data)
                carga = json.dumps(nuevo_json, indent = 2)
                topic = "sta_l"
                threadPublicadorSta = threading.Thread(name="Publicador", target=brokerPubSta.publicador, args=( topic, carga))
                threadPublicadorSta.start()
        elif topico == "act_l":
            data = json_decode(message.payload)   
            if data['request'] == 'info':       
                hoy= datetime.today()
                formatdate= "%d/%m/%Y %H:%M:%S"
                now = hoy.strftime(formatdate)
                nuevo_json = {}
                nuevo_json['node_id']= 'estacion_2'
                nuevo_json['date'] = now
                nuevo_json['actuators'] =[]
                with open('conf_l.json') as file:

                    datajson = json.load(file)
                    
                    for actuator in datajson['actuators']:
                        #print(actuator['type'])
                        estacion_act = ReadActuator().createActuator(actuator['type'])
                        nuevo_json['actuators'].append(json.loads(estacion_act))
                
                carga = json.dumps(nuevo_json, indent = 2)

                topic = "sta_l"
                threadPublicadorSta = threading.Thread(name="Publicador", target=brokerPubSta.publicador, args=(topic, nuevo_json))
                threadPublicadorSta.start()
            elif data['request'] == "act":
                for actor in data['actuators']:
                    if actor['actuator_id'] == 'Lawn_sprinkler':
                        if actor['order'] == 'on':                       
                            electrovalve.on()           
                        elif actor['order'] == 'off':
                            electrovalve.off()

def main():     
    args = parser.parse_args()
    estacion=args.name
    password = args.password
    with open("/home/pi/Desktop/NODO_2/comunicacion/station.pass","w") as archivo_pass:
        archivo_pass.seek(0)
        archivo_pass.truncate()
        password_act = "PASSWORD_ACT="
        password_act += str(password)
        archivo_pass.write(password_act)
        print("Se guardo la contraseña del actuador en el archivo",archivo_pass.name)
    leer_archivo = Archivo()
    json_leer = json.loads(leer_archivo.Leer_Archivo("conf_l.json","/home/pi/Desktop/NODO_2/comunicacion/"))
    hostname = json_leer['broker']['broker_address']
    puerto = int(json_leer['broker']['port'])
    broker = ConexionMqtt()
    threadSuscriptor = threading.Thread(name="Suscriptor", target=broker.sucriptor, args=(hostname, puerto))
    threadSuscriptor.start()
if  __name__ ==  '__main__':
    main()