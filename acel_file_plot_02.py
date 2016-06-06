#!/usr/bin/python
# -*- coding: cp1252 -*-
# Program acel_file_plot_02.py    ¡¡¡ OK !!!
# Program acel_file_plot_01.py modified:
# - Tkes the samples media value to substract as offset DC.
# Program acel_file_plot_01.py
# - Calculates and plots the FFT from samples.
# - Plots the sampled data.
# - Reads sampled data from a file.
# - File name is introduced from console, no extension.
# - Separate channels according to labels.
# 02/06/2016

from scipy.signal import filtfilt, iirfilter, butter, lfilter
from scipy import fftpack, arange
import numpy as np
import string
import matplotlib.pyplot as plt

sample_rate = 5000    # Sampling frequency (SPS).

def simpleParse( mainString, beginString, endString ):
    """Searches for a substring between beginString and endString"""
    posBeginString = string.find(mainString, beginString) + len(beginString)
    posEndString = string.find(mainString, endString)
    resultado = mainString[posBeginString:posEndString]
    return resultado

def extraer_int_tag(datos_arch, tag):
    """ Extracts data from string datos_str, delimited by <tag> y </tag> 
        and convets it to integer numbers (list of integers)"""
    str_canal = ''
    beginString = '<' + tag + '>'
    endString = '</'+ tag + '>'
    str_parse = simpleParse(datos_arch, beginString, endString )
    str_canal = str_parse.split(',')    
    
    canal = []
    n = len(str_canal)
    for i in range(n):
        canal.append(int(str_canal[i]))
    return canal

# Ask for file name, no extension. Assumes .txt extension.
# .txt extenssion is added.
nombre_archivo = raw_input('File to open (no extenssion): ')
nombre_archivo += ".txt"
print 'Opening file: ' + nombre_archivo
archivo = nombre_archivo

# Open file for reading
arch = open(archivo, "r")
datos_arch = arch.read()
#print 'archivo: ' 
#print datos_arch

# Searches for every channel, delimited by L1 and L2 tags.
canal_1 = extraer_int_tag(datos_arch, 'L1')
canal_2 = extraer_int_tag(datos_arch, 'L2')

#print("Valores canal 1: %s" %canal_1)
print("Amount of samples in channel 1: %s" %len(canal_1))
#print("Valores canal 2: %s" %canal_2)
print("Amount of samples on channel 2: %s" %len(canal_2))

#----------------- Plotting ----------
num_datos = len(canal_1)
#X = range(0, num_datos*2, 2)   # Eje X en ms, 500 sps, 2 ms
X = range(0, num_datos, 1)     # Eje X, 1000 sps, 1 ms. 

fig1 = plt.figure(num=1, figsize=(10,7))

# Figure 1. Sampled signals.
#Channel 1
#ax = fig1.add_subplot(3,1,1, axisbg='black')
ax = fig1.add_subplot(2,1,1)
ax.hold(False)
#ax.plot(X,canal1, color='y')
ax.plot(X,canal_1)
ax.grid()                       #Shows grid.
        
#Channel 2
ax = fig1.add_subplot(2,1,2)
ax.hold(False)
ax.plot(X,canal_2)        
ax.grid()                       #Shows grid.

# Calculates medium value for each channel.
vdc_canal_1 = 0
vdc_canal_2 = 0
for indice in X:
    vdc_canal_1 += canal_1[indice]
    vdc_canal_2 += canal_2[indice]
vdc_canal_1 = vdc_canal_1 / num_datos
vdc_canal_2 = vdc_canal_2 / num_datos
print("Vdc Channel 1: {0}, Vdc Channel 2 {1}".format(vdc_canal_1, vdc_canal_2)) 

# Figure 2. FFT from signals.
fig2 = plt.figure(num=2, figsize=(10,7))
fig2.suptitle('FFT spectrum')

#Channel 1
canal_fft = []
n = len(canal_1)
for i in range(n):
    canal_fft.append(canal_1[i] - vdc_canal_1)   #Substract offset.

n = len(canal_fft) # length of the signal
k = arange(n)
fs = sample_rate/1.0
T = n/fs
frq = k/T # two sides frequency range
frq = frq[range(n/2)] # one side frequency range
Y = fftpack.fft(canal_fft)/n # fft computing and normalization
Y = Y[range(n/2)]   

ax = fig2.add_subplot(2,1,1)
ax.hold(False)
ax.plot(frq, abs(Y))
ax.grid()
ax.set_title("Channel 1")

#Channel 2
canal_fft = []
n = len(canal_2)
for i in range(n):
    canal_fft.append(canal_2[i] - vdc_canal_2)    #Substract offset.

n = len(canal_fft) # length of the signal
k = arange(n)
fs = sample_rate/1.0
T = n/fs
frq = k/T # two sides frequency range
frq = frq[range(n/2)] # one side frequency range
Y = fftpack.fft(canal_fft)/n # fft computing and normalization
Y = Y[range(n/2)]   

ax = fig2.add_subplot(2,1,2)
ax.hold(False)
ax.plot(frq, abs(Y))
ax.grid()
ax.set_title("Channel 2")

plt.show()
