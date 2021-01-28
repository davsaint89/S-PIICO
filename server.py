import argparse
import json
import sys
import paho.mqtt.client as mqtt
from datetime import date, datetime, time, timedelta
import threading
import time
import serial
import paho.mqtt.publish as publish
import bluetooth
import os

tiempo1 = 0
tiempo2 = 0
tiempo3 = 0
restaWifi = 0
restaZigbee = 0
restaBlue = 0


def Zigbee_server():
    
    global tiempo1, tiempo2, tiempo3, restaZigbee, restaWifi, restaBlue
    ser =serial.Serial('/dev/ttyUSB0', 9600)      
    while True:
        gps = {
                "lon": -74.06,
                "lat": 4.69
            }
        incoming=ser.readline().strip()
        #print(incoming)
        message = str(incoming.decode('ASCII'))
        #print(message)
        mensaje = json.loads(message)
        marca = mensaje['date']
        #print(marca)        
        if marca:
            marca0 = datetime.strptime(marca, "%d/%m/%Y %H:%M:%S")
            print("xbee",marca)
            timestamp = datetime.timestamp(marca0)
            tiempo1 = round(timestamp)
            #print(tiempo1) 
            hoy= datetime.today()
            formatdate= "%d/%m/%Y %H:%M:%S"
            now = hoy.strftime(formatdate)
            datos = []
            datos.append(mensaje)
            nuevo_json = {}
            nuevo_json['Gateway_id'] = "Gateway_1"
            nuevo_json['gps'] = gps
            nuevo_json['date'] = now
            nuevo_json['topic']= 'sen_j'
            nuevo_json['nodes'] = datos
            sensors_data = json.dumps(nuevo_json, indent = 2)
            if tiempo2 !=0:
                
                restaZigbee = tiempo1-tiempo2 # resta con wifi
                print("zigbee-resta con wifi",restaZigbee)
                if tiempo3 !=0:
                    if restaZigbee<restaWifi and restaZigbee<restaBlue:
                        print("se fue con zigbee")
                        publish.single("sen_j", sensors_data, hostname="broker.hivemq.com", keepalive = 1200)
                elif restaZigbee < restaWifi:
                    print("se fue con Zigbee")
                    publish.single("sen_j", sensors_data, hostname="broker.hivemq.com", keepalive = 1200)
            # else:
            #     publish.single("sen_j", sensors_data, hostname="broker.hivemq.com", keepalive = 1200)
            if tiempo3 !=0:
                
                restaZigbee = tiempo1-tiempo3 # resta con bluetooth
                print("zigbee-resta con Blue",restaZigbee)
                if tiempo2 !=0:
                    if restaZigbee<restaWifi and restaZigbee<restaBlue:
                        print("se fue con zigbee")
                        publish.single("sen_j", sensors_data, hostname="broker.hivemq.com", keepalive = 1200)
                elif restaZigbee < restaBlue:
                    print("envio de zigbee por restaZigbee")
                    publish.single("sen_j", sensors_data, hostname="broker.hivemq.com", keepalive = 1200)

            else:
                publish.single("sen_j", sensors_data, hostname="broker.hivemq.com", keepalive = 1200)
        else:
            marca =0
            tiempo1 =0
def Blue_server():
    global tiempo1, tiempo2, tiempo3, restaBlue,restaZigbee, restaWifi
    port = 1
    while True:
        try:
            gps = {
                "lon": -74.06,
                "lat": 4.69
            }
            server_sock=bluetooth.BluetoothSocket( bluetooth.RFCOMM )
            server_sock.bind(("",port))
            server_sock.listen(2)
            client_sock,address = server_sock.accept()         
            data = client_sock.recv(1024)
            datos = data.decode('ASCII')
            mensaje = json.loads(datos)      
            marca1 = (mensaje['date'])

            if marca1:
                marca2 = datetime.strptime(marca1, "%d/%m/%Y %H:%M:%S")
                #print("bluetooth", marca1)
                timestamp = datetime.timestamp(marca2)
                tiempo3 = round(timestamp)
                hoy= datetime.today()
                formatdate= "%d/%m/%Y %H:%M:%S"
                now = hoy.strftime(formatdate)
                datos = []
                datos.append(mensaje)
                nuevo_json = {}
                nuevo_json['Gateway_id'] = "Gateway_1"
                nuevo_json['gps'] = gps
                nuevo_json['date'] = now
                nuevo_json['topic']= 'sen_j'
                nuevo_json['nodes'] = datos
                sensors_data = json.dumps(nuevo_json, indent = 2)
                if tiempo2 !=0:
                    restaBlue = tiempo3-tiempo2 #resta con wifi
                    print("bluetooth-resta con wifi",restaBlue)
                    if tiempo1 !=0:
                        if restaBlue<restaZigbee and restaBlue<restaWifi:
                            print("se fue por Bluetooth")
                            publish.single("sen_j", sensors_data, hostname="broker.hivemq.com", keepalive = 1200)
                    elif restaBlue<restaWifi:
                        publish.single("sen_j", sensors_data, hostname="broker.hivemq.com", keepalive = 1200)
                else:
                    publish.single("sen_j", sensors_data, hostname="broker.hivemq.com", keepalive = 1200)
                if tiempo1 !=0:
                    restaBlue = tiempo3-tiempo1 # resta con Zigbee
                    print("bluetooth-resta con zigbee",restaBlue)
                    if tiempo2 !=0:

                        if restaBlue<restaZigbee and restaBlue<restaWifi:
                            print("se fue por Bluetooth")
                            publish.single("sen_j", sensors_data, hostname="broker.hivemq.com", keepalive = 1200)
                    elif restaBlue<restaZigbee:
                        publish.single("sen_j", sensors_data, hostname="broker.hivemq.com", keepalive = 1200)
                    elif restaBlue==restaZigbee:
                        publish.single("sen_j", sensors_data, hostname="broker.hivemq.com", keepalive = 1200)
                # else:
                #     publish.single("sen_j", sensors_data, hostname="broker.hivemq.com", keepalive = 1200)

            else:
                marca1 =0
                tiempo3 =0   
        except KeyboardInterrupt:

            client_sock.close()
            server_sock.close()


def json_decode(data):  
    string_data = data.decode('ASCII')
    json_data = json.loads(string_data)
    return json_data

# Modo escucha local
class ConexionMqtt: 
    def subscriptor(self, hostSub, puertoSub):
        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_message = on_message
        print("hostname= ",hostSub,"puerto= ",puertoSub)
        client.connect(host=hostSub, port=puertoSub)
        client.loop_forever()

# Modo escucha pública
class MqttPublic:
    def suscripcion(self, host, port):
        client1 = mqtt.Client()
        client1.on_connect = on_connect2
        client1.on_message = on_message2
        print("hostname= ",host,"puerto= ",port)
        client1.connect(host=host, port= port)
        client1.loop_forever()

# topicos locales de respuesta del nodo y escucha del Gateway

def on_connect(client, userdata, flags, rc): 
    client.subscribe([('sta_l', 2),('sen_l', 2),('req_l',2)])#,('xbee', 2),('blue', 2)])

# topicos publicos de escucha del Gateway por broker publico

def on_connect2(client1, userdata, flags, rc):
    client1.subscribe([('req_p', 2),('conf_p', 2),('act_p', 2)])

# redireccion de mensajes a los nodos segun topico en broker público

def on_message2(client1, userdata, message1):
    
    topico = message1.topic
    json_resultado = json_decode(message1.payload)
    #print(topico)
  
    if topico == 'act_p':
        mensaje = json.dumps(json_resultado, indent = 2)
        publish.single("act_l", mensaje, hostname="192.168.4.1")
        #print(json.dumps(json_resultado, indent = 2))

    if topico == 'req_p':
        salida = json.dumps(json_resultado, indent = 2)
        publish.single("req_l", salida, hostname="192.168.4.1")
        #print(json.dumps(json_resultado, indent = 2))

    if topico == 'conf_p':
        salida2 = json.dumps(json_resultado, indent = 2)
        publish.single("conf_l", salida2, hostname="192.168.4.1")
        #print(json.dumps(json_resultado, indent = 2))
        
# redireccion de mensajes de los nodos al broker público

def on_message(client, userdata, message):
    global tiempo1, tiempo2, tiempo3, restaZigbee, restaWifi, restaBlue
    gps = {
        "lon": -74.06,
        "lat": 4.69
    }
    topico = message.topic
    json_resultado = json_decode(message.payload)

    if topico == 'sta_l':
        json_resultado = json.loads(json_resultado)
        #print(json_resultado['node_id'])
        if json_resultado['node_id'] == 'estacion_2':
            datum = []
            datum.append(json_resultado)
            hoy= datetime.today()
            formatdate= "%d/%m/%Y %H:%M:%S"
            now = hoy.strftime(formatdate)
            nuevo_json = {}
            nuevo_json['Gateway_id'] = "Gateway_1"
            nuevo_json['gps'] = gps
            nuevo_json['date'] = now
            nuevo_json['topic']= 'sta_p'
            nuevo_json['nodes'] = datum
            #print(nuevo_json)
            with open('/home/pi/Documents/comunicacion/data.json', 'w') as outfile:
                json.dump(nuevo_json, outfile)
            mensaje = json.dumps(nuevo_json, indent = 2)
            
            publish.single("sta_p", mensaje, hostname="broker.hivemq.com")
        elif json_resultado['node_id'] == 'estacion_1':
            datum = []
            datum.append(json_resultado)
            hoy= datetime.today()
            formatdate= "%d/%m/%Y %H:%M:%S"
            now = hoy.strftime(formatdate)
            nuevo_json = {}
            nuevo_json['Gateway_id'] = "Gateway_1"
            nuevo_json['gps'] = gps
            nuevo_json['date'] = now
            nuevo_json['topic']= 'sta_p'
            nuevo_json['nodes'] = datum
            #print(nuevo_json)
            with open('/home/pi/Documents/comunicacion/data1.json', 'w') as outfile:
                json.dump(nuevo_json, outfile)
            mensaje = json.dumps(nuevo_json, indent = 2)
            
            publish.single("sta_p", mensaje, hostname="broker.hivemq.com")
               
    elif topico == 'sen_l':
       
        if json_resultado['node_id'] == 'estacion_2':
            marca_tiempo = json_resultado['date']
            
            if marca_tiempo:
                marca_tiempo1 = datetime.strptime(marca_tiempo, "%d/%m/%Y %H:%M:%S")
                print("wifi",marca_tiempo)
                #time.sleep(5)
                timestamp = datetime.timestamp(marca_tiempo1)
                tiempo2 = round(timestamp)
                #print(tiempo2)
                hoy= datetime.today()
                formatdate= "%d/%m/%Y %H:%M:%S"
                now = hoy.strftime(formatdate)
                datos = []
                datos.append(json_resultado)
                nuevo_json = {}
                nuevo_json['Gateway_id'] = "Gateway_1"
                nuevo_json['gps'] = gps
                nuevo_json['date'] = now
                nuevo_json['topic']= 'sen_j'
                nuevo_json['nodes'] = datos
                # control = datetime.strptime(now, "%d/%m/%Y %H:%M:%S")
                # print("fechaWifi",control)
                sensors_data = json.dumps(nuevo_json, indent = 2)
                if tiempo1 !=0:
                    #print("en wifi",tiempo1)
                    restaWifi = tiempo2-tiempo1
                    print("wifi-restaWifi",restaWifi)
                    if tiempo3 !=0:
                        # resta2 = tiempo2-tiempo3
                        # total3 = restaWifi + resta2
                        print("hola")
                        #if total3<total2 and total3<total1:
                        if restaWifi<restaBlue and restaWifi<restaZigbee:
                            print("se fue por wifi")
                            publish.single("sen_j", sensors_data, hostname="broker.hivemq.com", keepalive = 1200)

                    elif restaWifi < restaZigbee:
                        print("envio wifi por restaWifi")
                        publish.single("sen_j", sensors_data, hostname="broker.hivemq.com", keepalive = 1200)

                    elif restaWifi == restaZigbee:
                        print("envio wifi por restaWifi")
                        publish.single("sen_j", sensors_data, hostname="broker.hivemq.com", keepalive = 1200)
                # else:
                #     print("envio wifi por restaWifi")
                #     publish.single("sen_j", sensors_data, hostname="broker.hivemq.com", keepalive = 1200)
                if tiempo3 !=0:
                    #print("en wifi",tiempo1)
                    restaWifi = tiempo2-tiempo3 # resta con bluetooth
                    print("wifi-restaWifiBlue",restaWifi)
                    if tiempo1 !=0:
                        if restaWifi<restaBlue and restaWifi<restaZigbee:
                        #if total3<total2 and total3<total1:
                            print("se fue por wifi")
                            publish.single("sen_j", sensors_data, hostname="broker.hivemq.com", keepalive = 1200)
                    elif restaWifi < restaBlue:
                        print("envio wifi por restaWifi")
                        publish.single("sen_j", sensors_data, hostname="broker.hivemq.com", keepalive = 1200)

                    elif restaWifi == restaBlue:
                        print("envio wifi por restaWifi")
                        publish.single("sen_j", sensors_data, hostname="broker.hivemq.com", keepalive = 1200)
                else:
                    publish.single("sen_j", sensors_data, hostname="broker.hivemq.com", keepalive = 1200)
            else: 
                marca_tiempo = 0
                tiempo2 =2
        elif json_resultado['node_id'] == 'estacion_1':
            marca_tiempo = json_resultado['date']
            
            if marca_tiempo:
                marca_tiempo1 = datetime.strptime(marca_tiempo, "%d/%m/%Y %H:%M:%S")
                print("wifi",marca_tiempo)
                #time.sleep(5)
                timestamp = datetime.timestamp(marca_tiempo1)
                tiempo2 = round(timestamp)
                #print(tiempo2)
                hoy= datetime.today()
                formatdate= "%d/%m/%Y %H:%M:%S"
                now = hoy.strftime(formatdate)
                datos = []
                datos.append(json_resultado)
                nuevo_json = {}
                nuevo_json['Gateway_id'] = "Gateway_1"
                nuevo_json['gps'] = gps
                nuevo_json['date'] = now
                nuevo_json['topic']= 'sen_j'
                nuevo_json['nodes'] = datos
                # control = datetime.strptime(now, "%d/%m/%Y %H:%M:%S")
                # print("fechaWifi",control)
                sensors_data = json.dumps(nuevo_json, indent = 2)
                if tiempo1 !=0:
                    #print("en wifi",tiempo1)
                    restaWifi = tiempo2-tiempo1
                    print("wifi-restaWifi",restaWifi)
                    if tiempo3 !=0:
                        # resta2 = tiempo2-tiempo3
                        # total3 = restaWifi + resta2
                        print("hola")
                        #if total3<total2 and total3<total1:
                        if restaWifi<restaBlue and restaWifi<restaZigbee:
                            print("se fue por wifi")
                            publish.single("sen_j", sensors_data, hostname="broker.hivemq.com", keepalive = 1200)

                    elif restaWifi < restaZigbee:
                        print("envio wifi por restaWifi")
                        publish.single("sen_j", sensors_data, hostname="broker.hivemq.com", keepalive = 1200)

                    elif restaWifi == restaZigbee:
                        print("envio wifi por restaWifi")
                        publish.single("sen_j", sensors_data, hostname="broker.hivemq.com", keepalive = 1200)
                # else:
                #     print("envio wifi por restaWifi")
                #     publish.single("sen_j", sensors_data, hostname="broker.hivemq.com", keepalive = 1200)
                if tiempo3 !=0:
                    #print("en wifi",tiempo1)
                    restaWifi = tiempo2-tiempo3 # resta con bluetooth
                    print("wifi-restaWifiBlue",restaWifi)
                    if tiempo1 !=0:
                        if restaWifi<restaBlue and restaWifi<restaZigbee:
                        #if total3<total2 and total3<total1:
                            print("se fue por wifi")
                            publish.single("sen_j", sensors_data, hostname="broker.hivemq.com", keepalive = 1200)
                    elif restaWifi < restaBlue:
                        print("envio wifi por restaWifi")
                        publish.single("sen_j", sensors_data, hostname="broker.hivemq.com", keepalive = 1200)

                    elif restaWifi == restaBlue:
                        print("envio wifi por restaWifi")
                        publish.single("sen_j", sensors_data, hostname="broker.hivemq.com", keepalive = 1200)
                else:
                    publish.single("sen_j", sensors_data, hostname="broker.hivemq.com", keepalive = 1200)
            else: 
                marca_tiempo = 0
                tiempo2 =2

    elif topico == "req_l":
        
        if json_resultado['request'] == "stop":
            #print("paro y resetea")
            tiempo1 = 0
            tiempo2 = 0
            tiempo3 = 0
            restaBlue = 0
            restaWifi = 0
            restaZigbee = 0

def main():

    try:
        hostname = '192.168.4.1'
        host = 'broker.hivemq.com'
        puerto = 1883
        broker = ConexionMqtt()
        broker2 = MqttPublic()
        threadSuscriptor = threading.Thread(name="Subscriptor", target=broker.subscriptor, args=(hostname, puerto))
        threadSuscriptor.start()
        threadPublico = threading.Thread(name="Subscripcion_publica", target =broker2.suscripcion, args=(host, puerto))
        threadPublico.start()
        hilo = threading.Thread(target = Zigbee_server)
        hilo.start()
        hilo1 = threading.Thread(target = Blue_server)
        hilo1.start()
    except KeyboardInterrupt:
        hilo1.stop()
        hilo.stop()

if  __name__ ==  '__main__':
    main()
            