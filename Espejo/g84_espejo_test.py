#!/usr/bin/env python3

'''
ESPEJO DEL GUIADOR DEL TEL84CM - CLASE DE CONTROL/SERVIDOR
Version 0.3-dev          11/junio/2025
Edgar Omar Cadena Zepeda
IA-UNAM-ENS
cadena@astro.unam.mx

Mecanismo para meter y sacar el espejo del guiador en el telescopio de 84cm.

El sistema consta de:
1 - Motor DC para meter o sacar espejo del guiador
2 - Interruptores límite N.A. (abierto y cerrado)


Comandos que Ejecuta el Servidor:

ESTADO: Entrega variables del sistema           echo ESTADO | nc localhost 7777
METE: Mete el espejo                            echo METE  | nc localhost 7777
SACA: Saca el espejo                            echo SACA  | nc localhost 7777
INIT: Inicializa el espejo (lo saca)            echo INIT  | nc localhost 7777
STOP: Detiene el espejo                         echo STOP  | nc localhost 7777


Funciones Añadidas:
Ver. 0.3 - Se cambia la libreria del motor kit por esta: sudo pip3 install adafruit-circuitpython-motorkit
Ver. 0.2 - Los interruptores ahora son N.A. y el micro lee como low cuando se activan, los gpio como PUD_UP y la lectura de estado es inversa.
Ver. 0.1 - Implementada
'''


# Modulos externos
import os
import sys
from threading import Thread, Timer
import atexit
import socket
import simplejson as json
import queue as Queue
import time
import RPi.GPIO as GPIO
import board
from adafruit_motorkit import MotorKit

import g84_variables

variables = g84_variables.Variables()  # Variables

# Esperar 5 segundos antes de ejecutar el resto del programa
time.sleep(5)


# GPIOS Entradas
METE_PIN = variables.ESPEJO_SWITCH_METE  # 23
SACA_PIN = variables.ESPEJO_SWITCH_SACA  # 24
#METE_PIN = 23  # 23
#SACA_PIN = 24  # 24

# GPIOS
# Pin Setup:
GPIO.setmode(GPIO.BCM) # Broadcom pin-numbering scheme # GPIO pulled down, detecta  3.3V con la interrupcion
GPIO.setwarnings(False)
GPIO.setup(METE_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # 23  Pull_down
GPIO.setup(SACA_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # 24  Pull_down

# ADAFRUIT MOTORHATS
kit = MotorKit(i2c=board.I2C())
ESPEJO_TIMEOUT = 7  # segundos para el timeout

# recommended for auto-disabling motors on shutdown!
# Apaga todos los motores
def turnOffMotors():
    print("[+] apaga Motores")
    time.sleep(0.20)
    kit.motor1.throttle = 0
    kit.motor2.throttle = 0
    kit.motor3.throttle = 0
    kit.motor4.throttle = 0
    kit.motor1.throttle = None
    kit.motor2.throttle = None
    kit.motor3.throttle = None
    kit.motor4.throttle = None
    variables.ESPEJO_STOP = 1

# recommended for auto-disabling motors on shutdown!
atexit.register(turnOffMotors)

# Multithreaded Python server : TCP Server Socket Program Stub
TCP_IP = '0.0.0.0'
TCP_PORT = 7777
BUFFER_SIZE = 2048  # Usually 1024, but we need quick response

# create an INET, STREAMing socket
tcpServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcpServer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# bind the socket to a public host, and a well-known port
tcpServer.bind((TCP_IP, TCP_PORT))
threads = []
EspejoTimer = None



# Funciones normales
# Apaga el motor del espejo
def turnOffEspejo():
    print ("[+] apaga Espejo")
    time.sleep(0.20)
    kit.motor1.throttle = 0
    kit.motor1.throttle = None
    variables.ESPEJO_STOP = 1

# Apaga el motor del espejo por Timeout
def turnOffmeteEspejoTimeout():
    if GPIO.input(METE_PIN) == GPIO.LOW:
        print ("[+] Espejo llego antes del timeout")
        variables.ESPEJO_ESTADO = "METIDO"
    else:
        print ("[-] Apagando Espejo no llego por Timeout")
        variables.ESPEJO_ESTADO = "ERROR"
        turnOffEspejo()
    variables.ESPEJO_STOP = 1

def turnOffsacaEspejoTimeout():
    if GPIO.input(SACA_PIN) == GPIO.LOW:
        print("[+] Espejo llego antes del timeout")
        variables.ESPEJO_ESTADO = "SACADO"
    else:
        print("[-] Apagando Espejo no llego por Timeout")
        variables.ESPEJO_ESTADO = "ERROR"
        turnOffEspejo()
    variables.ESPEJO_STOP = 1

def turnOffinitEspejoTimeout():
    if GPIO.input(SACA_PIN) == GPIO.LOW:
        print("[+] Espejo llego antes del timeout")
        variables.ESPEJO_ESTADO = "SACADO"
        variables.ESPEJO_INIT = 1
    else:
        print("[-] Apagando Espejo no llego por Timeout")
        variables.ESPEJO_ESTADO = "ERROR"
        turnOffEspejo()
        variables.ESPEJO_INIT = 0
    variables.ESPEJO_STOP = 1


# mete espejo
def meteEspejo():
    global EspejoTimer
    variables.ESPEJO_POS_DESEADA = "METIDO"
    if GPIO.input(METE_PIN) == GPIO.LOW:
        variables.ESPEJO_METIDO = 1
        variables.ESPEJO_ESTADO = "METIDO"
        print ("[+] Espejo ya metido")
        turnOffEspejo()
    else:
        variables.ESPEJO_METIDO = 0
        variables.ESPEJO_ESTADO = "MOVIENDO"
        print ("[+] avanza Espejo")
        time.sleep(0.20)
        kit.motor1.throttle = 0.5  # Avanza a la mitad de la velocidad
        EspejoTimer = Timer(ESPEJO_TIMEOUT, turnOffmeteEspejoTimeout)
        EspejoTimer.start()

# saca espejo
def sacaEspejo():
    global EspejoTimer
    variables.ESPEJO_POS_DESEADA = "SACADO"
    if GPIO.input(SACA_PIN) == GPIO.LOW:
        variables.ESPEJO_SACADO = 1
        variables.ESPEJO_ESTADO = "SACADO"
        print("[+] Espejo ya sacado")
        turnOffEspejo()
    else:
        variables.ESPEJO_SACADO = 0
        variables.ESPEJO_ESTADO = "MOVIENDO"
        print("[+] retrocede Espejo")
        time.sleep(0.20)
        kit.motor1.throttle = -0.5  # Retrocede a la mitad de la velocidad
        EspejoTimer = Timer(ESPEJO_TIMEOUT, turnOffsacaEspejoTimeout)
        EspejoTimer.start()

# init espejo (que siempre lo saca al iniciar el programa)
def initEspejo():
    global EspejoTimer
    variables.ESPEJO_POS_DESEADA = "INIT"
    if GPIO.input(SACA_PIN) == GPIO.LOW:
        variables.ESPEJO_SACADO = 1
        variables.ESPEJO_ESTADO = "SACADO"
        print("[+] Espejo ya sacado")
        turnOffEspejo()
        variables.ESPEJO_INIT = 1
    else:
        variables.ESPEJO_SACADO = 0
        variables.ESPEJO_ESTADO = "MOVIENDO"
        variables.ESPEJO_INIT = 0
        print("[+] retrocede Espejo")
        time.sleep(0.20)
        kit.motor1.throttle = -0.5  # Retrocede a la mitad de la velocidad
        EspejoTimer = Timer(ESPEJO_TIMEOUT, turnOffinitEspejoTimeout)
        EspejoTimer.start()


#Clase Principal
class Principal():
    def __init__(self):
        print ("[+] Variables del programa Cargadas")


    # Funciones Callback
    # these will run in another thread when our events are detected
    def ESPEJO_METIDO(self, channel):    #switch normalmente abierto
        time.sleep(0.005) # debounce
        if GPIO.input(METE_PIN) == GPIO.LOW:
            variables.ESPEJO_METIDO = 1
            variables.ESPEJO_ESTADO = "METIDO"
            print(">>rising edge detectado en METE_PIN>>")
            print ("[+] metioEspejo")
            turnOffEspejo()
        else:
            variables.ESPEJO_METIDO = 0
            variables.ESPEJO_ESTADO = "MOVIENDO"
            print ("<<falling edge detectado on METE_PIN<<")


    def ESPEJO_SACADO(self, channel):    #switch normalmente abierto
        time.sleep(0.005) # debounce
        if GPIO.input(SACA_PIN) == GPIO.LOW:
            variables.ESPEJO_SACADO = 1
            variables.ESPEJO_ESTADO = "SACADO"
            print (">>rising edge detectado on SACA_PIN>>")
            print ("[+] sacoEspejo")
            turnOffEspejo()
        else:
            variables.ESPEJO_SACADO = 0
            variables.ESPEJO_ESTADO = "MOVIENDO"
            print("<<falling edge detectado on SACA_PIN<<")


    # Detectamos interrupciones
    def initInterrupciones(self):
        # when a rising edge is detected on gpio, regardless of whatever
        # else is happening in the program, the function my_callback will be run
        GPIO.add_event_detect(
            METE_PIN, GPIO.BOTH, callback=self.ESPEJO_METIDO, bouncetime=300)
        GPIO.add_event_detect(
            SACA_PIN, GPIO.BOTH, callback=self.ESPEJO_SACADO, bouncetime=300)


    # Estado inicial de los interruptores
    def initStatus(self):
       variables.ESPEJO_METIDO = int(not GPIO.input(METE_PIN))  # 23
       variables.ESPEJO_SACADO = int(not GPIO.input(SACA_PIN))  # 24
       estado = {
           'ESPEJO_INIT': variables.ESPEJO_INIT,
           'ESPEJO_METIDO': variables.ESPEJO_METIDO,
           'ESPEJO_SACADO': variables.ESPEJO_SACADO,
           'ESPEJO_POS_DESEADA': variables.ESPEJO_POS_DESEADA,
           'ESPEJO_ESTADO': variables.ESPEJO_ESTADO,
           'ESPEJO_STOP': variables.ESPEJO_STOP
            }
       estado_json = json.dumps(estado, separators=(',', ':'), sort_keys=True) #data serialized
       print ("[+] Estado inicial: ")
       print (estado_json)


    def run(self):
        self.initInterrupciones()
        time.sleep(0.20)
        print ("[+] Iniciando Servicio de Interrupciones OK")
        try:
            self.initStatus()
        except:
            print ("[-] ERROR DE INICIACION DE interrupciones")
            pass
        time.sleep(0.20)



# Multithreaded Python server : TCP Server Socket Thread Pool
class ClientThread(Thread):
    def __init__(self, ip, port, conn):
        super().__init__()
        self.ip = ip
        self.port = port
        self.conn = conn
        #print ("[+] Nuevo server socket thread iniciado desde " + ip + ":" + str(port))

    def run(self):
        global EspejoTimer
        while True:
            data = self.conn.recv(2048).strip()
            if not data:
                print ("Comando Recibido: NO DATA")
                break
            data = data.decode('utf-8') # decodificar el mensaje
            data = data.upper() # convertir a mayusculas
            print ("Comando Recibido: " + data)
            datasplit = data.split(' ')
            comando = datasplit[0]
            #print (datasplit) #debug
            time.sleep(0.20)
            
            # Comandos
            # mueve hacia METE
            if comando == 'METE':        #EJEMPLO: echo METE | nc ip 7777
                if EspejoTimer:
                    EspejoTimer.cancel()
                    EspejoTimer = None
                time.sleep(0.20)
                meteEspejo()
                try:
                    self.conn.send(str.encode('OK: ' + data + '\n'))  # echo
                except BrokenPipeError as e:
                    pass
                self.conn.close()
                break


            # mueve hacia SACA
            elif comando == 'SACA':  # EJEMPLO: echo SACA | nc ip 7777
                if EspejoTimer:
                    EspejoTimer.cancel()
                    EspejoTimer = None
                time.sleep(0.20)
                sacaEspejo()
                try:
                    self.conn.send(str.encode('OK: ' + data + '\n'))  # echo
                except BrokenPipeError as e:
                    pass
                self.conn.close()
                break


             # mueve hacia INIT
            elif comando == 'INIT':  # EJEMPLO: echo INIT | nc ip 7777
                if EspejoTimer:
                    EspejoTimer.cancel()
                    EspejoTimer = None
                time.sleep(0.20)
                initEspejo()
                try:
                    self.conn.send(str.encode('OK: ' + data + '\n'))  # echo
                except BrokenPipeError as e:
                    pass
                self.conn.close()
                break


            elif comando == 'ESTADO' or comando == "STATUS":     #REGRESA Estado ACTUAL
                variables.ESPEJO_METIDO = int(not GPIO.input(METE_PIN))  # 23
                variables.ESPEJO_SACADO = int(not GPIO.input(SACA_PIN))  # 24
                #print ("Peticicion del Cliente por Estado: ", data)
                estado = {
                        'ESPEJO_INIT': variables.ESPEJO_INIT,
                        'ESPEJO_METIDO': variables.ESPEJO_METIDO,
                        'ESPEJO_SACADO': variables.ESPEJO_SACADO,
                        'ESPEJO_POS_DESEADA': variables.ESPEJO_POS_DESEADA,
                        'ESPEJO_ESTADO': variables.ESPEJO_ESTADO,
                        'ESPEJO_STOP': variables.ESPEJO_STOP
                        }
                estado_json = json.dumps(estado, separators=(',', ':'), sort_keys=True) #data serialized
                try:
                    self.conn.send(str.encode(estado_json + '\n'))
                except BrokenPipeError as e:
                    pass
                self.conn.close()
                break


            elif comando == 'STOP':
                if EspejoTimer:
                    EspejoTimer.cancel()
                    EspejoTimer = None
                time.sleep(0.20)
                turnOffMotors()
                print ("[+] ESPEJO: MOTOR OFF")
                try:
                    self.conn.send(str.encode('OK: ' + data + '\n'))  # echo
                except BrokenPipeError as e:
                    pass
                self.conn.close()
                break


            elif comando == 'EXIT':
                now = time.strftime('%Y-%m-%d %H:%M')
                print(now + ' - Conexion Terminada por el Cliente')
                try:
                    self.conn.send(str.encode('Recibido: Adios' + '\n'))
                except BrokenPipeError as e:
                    pass
                self.conn.close()
                break


            else:
                now = time.strftime('%Y-%m-%d %H:%M')
                print(now + ' - No Existe el Comando - Conexion Terminada')
                try:
                    self.conn.send(str.encode('Adios' + '\n'))  # echo
                except BrokenPipeError as e:
                    pass
                self.conn.close()
                break



# Programa Principal
try:
    try:
        turnOffMotors()
    except:
        print ("[-] NO HAY COMUNICACIÓN CON EL MOTOR DRIVER")
        pass
    principal = Principal()
    principal.run()
    # Manda el espejo a posicion sacado al arrancar el programa
    #initEspejo()

    print ("[+] SERVIDOR DE ESPEJO DEL GUIADOR DEL TEL84CM Iniciado! Puerto: 7777 Presione CTRL+C para Salir")
    # become a server socket
    tcpServer.listen(12)

    while True:
        #print ("Esperando por Conexiones en el puerto: " + str(TCP_PORT))
        (conn, (ip, port)) = tcpServer.accept()

        threadSockets = ClientThread(ip, port, conn)
        threadSockets.start()
        threads.append(threadSockets)

    tcpServer.shutdown()
    tcpServer.close()
    # wait until worker threads are done to exit
    for t in threads:
        t.join()


except (KeyboardInterrupt, SystemExit): # If CTRL+C is pressed, exit cleanly:
    try:
        turnOffMotors()
    except:
        print ("[-] NO HAY COMUNICACIÓN CON EL MOTOR DRIVER")
        pass
    tcpServer.shutdown(socket.SHUT_RDWR)
    tcpServer.close()
    GPIO.cleanup()
    print("Adios Viajero")
    sys.exit()
