#!/usr/bin/python
# -*- coding: cp1252 -*-
# Program serial_avr_01.py     ¡¡¡ OK !!!
# Recives data on serial port and separats packets.
# Saves data on file.
# 02/06/2016

import serial
import time
import datetime

datos_a_leer = 16384     # Amount of samples to read.
sampling_rate = 5000     # Sampling frequency (SPS).

canal_1 = []
canal_2 = []

# ----------
def conv_str_tag(canal, tag):
    """ Convert every channel from int to str, separated by a coma 
    and adds tags at the beggining and end. """
    n = len(canal)
    s_canal = '<' + tag + '>'
    for i in range(n-1):
        s_canal = s_canal + str(canal[i]) + ','
    s_canal = s_canal + str(canal[n-1]) + '</'+ tag + '>'
    return s_canal

# ---------- Add tags and save on file  -----------------
def grabar(canal_1, canal_2, archivo):
    str_canal = ''
    str_canal += conv_str_tag(canal_1, 'L1') + '\n'
    str_canal += conv_str_tag(canal_2, 'L2') + '\n'

    str_aux = ''
    str_aux += '<nd>' + str(datos_a_leer) + '</nd>' + '\n'
    str_aux += '<sr>' + str(sampling_rate) + '<sr>' + '\n'
    #str_aux += '<gn>' + str(ganancia) + '</gn>' + '\n'
        
    # Write to file
    arch = open(archivo, "w")
    arch.write(str_aux)
    arch.write(str_canal)
    arch.close()     
#--------------------------------------------
    
serial_avr = serial.Serial('COM37', 500000, timeout=0)   # On windows 
time.sleep(2)    #Wait for initialization.
print("Initializing")

buffer = ''
paquete = ''
valores = []
serial_avr.flushInput()
serial_avr.flushOutput()

valores_decod = []

conta_datos_rx = 0;     #Received samples counter.

print("Sending INI")
serial_avr.write('INI')         #Start data sampling command.
#serial_avr.write(chr(0x22))    #CRC die 'INI'. Not used.
serial_avr.write(chr(0x7E))     #End of packet.

while conta_datos_rx < datos_a_leer:
    if serial_avr.inWaiting():
        lectura = serial_avr.read(serial_avr.inWaiting())
        buffer = buffer + lectura
        valores = []
    if len(buffer) > 10:
        i = buffer.find(chr(0x7E))
        if i >= 0:
            paquete = buffer[:i]
            buffer =  buffer[i+1:]
            #print("Paquete: %s" % (paquete))
            valores=[ord(i) for i in paquete]
            paquete = ''

            x = 0
            while x < len(valores):
                if valores[x] == 0x7D:
                    valores_decod.append(valores[x+1] ^ 0x20)
                    x = x + 1
                else:    
                    valores_decod.append(valores[x])
                x = x + 1

            canal1 = (valores_decod[0] * 256) + valores_decod[1]
            canal2 = (valores_decod[2] * 256) + valores_decod[3]

            canal_1.append(canal1)
            canal_2.append(canal2)

            #print("Canal 1: %s    Canal2: %s  " % (canal1, canal2))

            valores = []
            valores_decod = []

            conta_datos_rx += 1 ;
            #print("conta_datos_rx =  %s" %conta_datos_rx)

    #time.sleep(0.001)   #Sin esta línea, el programa consume 90% de recursos CPU    
    #Cuando la velocidad del puerto serial es alta y se recibe una gran cantidad 
    #de datos, time.sleep() impone un tiempo demasiado largo.

print("Sending PAR")
serial_avr.write('PAR')          #Stop data sampling.
serial_avr.write(chr(0x7E))      #End of packet.

serial_avr.close()      #Cierra el purto serial.

#print("Valores canal 1: %s" %canal_1)
print("Amount of samples channel 1: %s" %len(canal_1))
#print("Valores canal 2: %s" %canal_2)
print("Amount of samples channel 2: %s" %len(canal_2))

archivo = "datos_"
archivo += datetime.datetime.now().strftime("%d-%m-%Y__%H_%M_%S")
archivo += ".txt"
print("Saving to %s" %archivo)
grabar(canal_1, canal_2, archivo)

print("END")
