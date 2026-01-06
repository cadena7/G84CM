#!/usr/bin/env python3

'''
ESPEJO DEL GUIADOR DEL TEL84CM - CLASE DE MQTT
Version 0.1-dev          7/noviembre/2025
Edgar Omar Cadena Zepeda
IA-UNAM-ENS
cadena@astro.unam.mx

Mecanismo para meter y sacar el espejo del guiador en el telescopio de 84cm.

El sistema consta de:
1 - Motor DC para meter o sacar espejo del guiador
2 - Interruptores límite N.A. (abierto y cerrado)


Ejemplos con Mosquitto:

Subscribirse a todos los topicos:
mosquitto_sub -h 192.168.0.4 -t oan/control/84cm/guiador/espejo/# -d

mosquitto_pub -h 192.168.0.4 -t oan/control/84cm/guiador/espejo/control -m INIT
mosquitto_pub -h 192.168.0.4 -t oan/control/84cm/guiador/espejo/control -m ESTADO
mosquitto_pub -h 192.168.0.4 -t oan/control/84cm/guiador/espejo/control -m METE
mosquitto_pub -h 192.168.0.4 -t oan/control/84cm/guiador/espejo/control -m SACA


Funciones Añadidas:
Ver. 0.1 - En Desarrollo
'''



# Modulos externos
import time, datetime
import os
import sys
import paho.mqtt.client as mqtt
import subprocess
from threading import Thread
import simplejson as json

# Esperar 7 segundos antes de ejecutar el resto del programa
time.sleep(7)

# MQTT IP
LOCAL_IP = "nc 192.168.0.208 7777"
ESPEJO_IP = "nc localhost 7777"
#MQTT_HOST = "192.168.0.4"  # Broker Labo Ensenada
MQTT_HOST = "192.168.0.239"   # Broker Tel 84cm

MQTT_TOPIC = "oan/control/84cm/guiador/espejo/#"
MQTT_CONTROL = "oan/control/84cm/guiador/espejo/control"
MQTT_ESTADO = "oan/control/84cm/guiador/espejo/estado"


# MQTT on_connect
def on_connect(client, user_data, flags, rc):
    print ("Resultado de conexion: " + str(rc))
    client.subscribe(MQTT_TOPIC)
    print ("Conectado a: " + MQTT_TOPIC)


# MQTT on_message
def on_message(client, user_data, msg):
    #status = str(msg.payload)
    #print ("Received message '" + str(msg.payload.decode("utf-8")) + "' on topic '" + str(msg.topic) + "' with QoS " + str(msg.qos))
    topic = str(msg.topic)   # decodificar la string
    status = str(msg.payload.decode("utf-8"))   # decodificar la string
    status2 = status.upper() # convertir a mayusculas
    print ("Topico MQTT: " + topic + " Mensaje MQTT: " + status)

    if topic == MQTT_CONTROL:
        if status2 == 'STATUS' or status2 == "ESTADO":
            publicaestado()

        elif status2 == 'INIT' or status2 == "INICIO":
            initespejo = subprocess.Popen(ESPEJO_IP, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
            print ("[+] SOLICITANDO INIT")
            initespejo1 = initespejo.communicate(str.encode("INIT"))
            initespejo.kill()
            print ("[+] INICIO ESPEJO OK")
            publicaestado()

        elif status2 == 'METE':
            meteespejo = subprocess.Popen(ESPEJO_IP, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print("[+] SOLICITANDO METE")
            meteespejo1 = meteespejo.communicate(str.encode("METE"))
            meteespejo.kill()
            print("[+] METE ESPEJO OK")
            publicaestado()

        elif status2 == 'SACA':
            sacaespejo = subprocess.Popen(ESPEJO_IP, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print("[+] SOLICITANDO SACA")
            sacaespejo1 = sacaespejo.communicate(str.encode("SACA"))
            sacaespejo.kill()
            print("[+] SACA ESPEJO OK")
            publicaestado()

        elif status2 == 'STOP' or status2 == "PARA":
            stopespejo = subprocess.Popen(ESPEJO_IP, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
            print ("[+] SOLICITANDO STOP ESPEJO")
            stopespejo1 = stopespejo.communicate(str.encode("STOP"))
            stopespejo.kill()
            print ("[+] STOP ESPEJO OK")
            publicaestado()


def publicaestado():
    estado = subprocess.Popen(ESPEJO_IP, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
    estado1 = estado.communicate(str.encode("ESTADO"))[0]  #regresa un tuple [0,1]
    print ("[+] SOLICITANDO VARIABLES ESTADO ESPEJO")
    #print(estado1)
    estadojson = estado1.decode('utf-8')    #decodificar el mensaje
    #print(estadojson)
    estado.kill()
    estadojson1 = json.loads(estadojson)
    msg = {
        'ESPEJO_INIT': estadojson1['ESPEJO_INIT'],
        'ESPEJO_METIDO': estadojson1['ESPEJO_METIDO'],
        'ESPEJO_SACADO': estadojson1['ESPEJO_SACADO'],
        'ESPEJO_POS_DESEADA': estadojson1['ESPEJO_POS_DESEADA'],
        'ESPEJO_ESTADO': estadojson1['ESPEJO_ESTADO'],
        'ESPEJO_STOP': estadojson1['ESPEJO_STOP']
        }
    msg_json = json.dumps(msg, separators=(',', ':'), sort_keys=True) #data serialized
    #print(msg_json)
    client.publish(MQTT_ESTADO, msg_json, retain=True)
    print ("[+] STATUS DE VARIABLES ENVIADO OK")




#Loop que publica los datos de estado en el broker MQTT
class MQTTLOOP(Thread):
    def __init__(self):
        Thread.__init__(self)
        print ("[+] Inicia thread de monitoreo de estado y publicacion en MQTT")

    def run(self):
        while True :
            try:
                publicaestado()
            except:
                pass
            time.sleep(2) #actualiza el estado en MQTT cada 2 segundos


# Programa Principal
try:
    print ("[+] INTERPRETE MQTT DEL ESPEJO DEL GUIADOR DE TELESCOPIO 84CM Iniciado! Presione CTRL+C para Salir")
    client = mqtt.Client()
    client.connect(MQTT_HOST, 1883, 60)
    client.on_connect = on_connect
    client.on_message = on_message
    #client.loop_start()

    MQTTloop = MQTTLOOP()
    MQTTloop.setDaemon(True)
    MQTTloop.start()
    client.loop_forever()


except (KeyboardInterrupt, SystemExit): # If CTRL+C is pressed, exit cleanly:
    print("Adios Viajero")
    client.loop_stop()
    sys.exit()
