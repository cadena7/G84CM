#!/usr/bin/env python3

'''
ESPEJO DEL GUIADOR DEL TEL84CM - CLASE GLOBAL DE LAS VARIABLES
Version 0.1-dev          23/abril/2025
Edgar Omar Cadena Zepeda
IA-UNAM-ENS
cadena@astro.unam.mx

Mecanismo para meter y sacar el espejo del guiador en el telescopio de 84cm.

Funciones Añadidas:
Ver. 0.1 - Implementada
'''

#TAPA
class Variables():
    def __init__(self):
        # Entradas
        self.ESPEJO_SWITCH_METE = 23
        self.ESPEJO_SWITCH_SACA = 24

        # Variables extras
        self.ESPEJO_STOP = 0

        # Posición de ESPEJO
        self.ESPEJO_INIT = 0                # ESPEJO INICIALIZADO: SI O NO
        self.ESPEJO_METIDO = 0
        self.ESPEJO_SACADO = 0
        self.ESPEJO_POS_DESEADA = "NULL"      # ESPEJO POSICION DESEADA: 0-NULL 1-METE 2-SACA
        self.ESPEJO_ESTADO = "NULL" # ESPEJO: NULL, METIDO, SACADO, MOVIENDO, ERROR
