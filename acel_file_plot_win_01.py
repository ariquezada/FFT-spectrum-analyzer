#!/usr/bin/python
# -*- coding: cp1252 -*-
# Program acel_file_plot_win_01.py   ¡¡¡ OK !!!
# Program acel_file_plot_03.py modified:
# - Window funcions added.
# 09/06/2016
# Program acel_file_plot_03.py
# Program acel_file_plot_02.py modified:
# - Corrects signal and FFT scaling.
# 07/06/2016
# Program acel_file_plot_02.py
# Program acel_file_plot_01.py modified:
# - Tkes the samples media value to substract as offset DC.
# Program acel_file_plot_01.py
# - Calculates and plots the FFT from samples.
# - Plots the sampled data.
# - Reads sampled data from a file.
# - File name is introduced from console, no extension.
# - Separate channels according to labels.
# 02/06/2016

#from scipy.signal import filtfilt, iirfilter, butter, lfilter
from scipy import signal
from scipy import fftpack, arange
import numpy as np
import string
import matplotlib.pyplot as plt

sample_rate = 5000    # Sampling frequency (SPS).
g_scale = 3.0/512       # +- 3g. 10 bit ADC.
max_freq = 1500       # Maximum signal frequency, X and Y axis (accelerometer).

def simpleParse(mainString, beginString, endString ):
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

# Searches for each channel, delimited by L1 and L2 tags.
canal_1 = extraer_int_tag(datos_arch, 'L1')
canal_2 = extraer_int_tag(datos_arch, 'L2')

print("Amount of samples in channel 1: %s" %len(canal_1))
print("Amount of samples on channel 2: %s" %len(canal_2))

num_datos = len(canal_1)
X = range(0, num_datos, 1)

# Scale the signal in g's
for indice in X:
    canal_1[indice] *= g_scale
    canal_2[indice] *= g_scale

# Calculates medium value for each channel.
vdc_canal_1 = 0
vdc_canal_2 = 0
for indice in X:
    vdc_canal_1 += canal_1[indice]
    vdc_canal_2 += canal_2[indice]
vdc_canal_1 = vdc_canal_1 / num_datos
vdc_canal_2 = vdc_canal_2 / num_datos
print("Vdc Channel 1: {0}, Vdc Channel 2 {1}".format(vdc_canal_1, vdc_canal_2))

# Substract DC offset
for indice in X:
    canal_1[indice] -= vdc_canal_1
    canal_2[indice] -= vdc_canal_2

#----------------- Plotting ----------
X1 = np.linspace(0, num_datos/5, num=num_datos)     # Eje X, 5000 sps, 1/5 ms.
fig1 = plt.figure(num=1, figsize=(10,7))
fig1.suptitle('Sampled signal - Acceleration')

# Figure 1. Sampled signals.
#Channel X
ax = fig1.add_subplot(2,1,1)
ax.hold(False)
ax.plot(X1,canal_1)
ax.set_title("Channel X")
ax.set_ylabel('g')
ax.grid()                       #Shows grid.
        
#Channel Y
ax = fig1.add_subplot(2,1,2)
ax.hold(False)
ax.plot(X1,canal_2)
ax.set_title("Channel Y")
ax.set_xlabel('ms')
ax.set_ylabel('g')
ax.grid()                       #Shows grid.

# Figure 2. FFT from signals.
fig2 = plt.figure(num=2, figsize=(10,7))
fig2.suptitle('FFT spectrum')

#Channel X
canal_fft = []
canal_fft = canal_1

N = len(canal_fft) # length of the signal
T = 1.0 / sample_rate
y = canal_fft
yf = fftpack.fft(y)
xf = np.linspace(0.0, 1.0/(2.0*T), N/2)

ax = fig2.add_subplot(2,1,1)
ax.hold(False)
ax.plot(xf, 2.0/N * np.abs(yf[:N/2]))
ax.grid()
ax.set_title("Channel X")
ax.set_ylabel('g')
ax.set_xlim(xmax=max_freq)

#Channel Y
canal_fft = []
canal_fft = canal_2

N = len(canal_fft) # length of the signal
T = 1.0 / sample_rate
y = canal_fft
yf = fftpack.fft(y)
xf = np.linspace(0.0, 1.0/(2.0*T), N/2)

ax = fig2.add_subplot(2,1,2)
ax.hold(False)
ax.plot(xf, 2.0/N * np.abs(yf[:N/2]))
ax.grid()
ax.set_title("Channel Y")
ax.set_xlabel('Hz')
ax.set_xlim(xmax=max_freq)
ax.set_ylabel('g')

# Figure 3. FFT from signals.
fig3 = plt.figure(num=3, figsize=(10,7))
fig3.suptitle('FFT spectrum - window applied')

#Channel X
canal_fft = []
canal_fft = canal_1

N = len(canal_fft) # length of the signal

w = signal.hann(N, sym=False)    #Hann (Hanning) window
#w = signal.flattop(N, sym=False)   #Flattop window

T = 1.0 / sample_rate
y = canal_fft
yf = fftpack.fft(y*w)
xf = np.linspace(0.0, 1.0/(2.0*T), N/2)

ax = fig3.add_subplot(2,1,1)
ax.hold(False)
ax.plot(xf, 2.0/N * np.abs(yf[:N/2]))
ax.grid()
ax.set_title("Channel X")
ax.set_ylabel('g')
ax.set_xlim(xmax=max_freq)

#Channel Y
canal_fft = []
canal_fft = canal_2

N = len(canal_fft) # length of the signal

w = signal.hann(N, sym=False)    #Hann (Hanning) window
#w = signal.flattop(N, sym=False)   #Flattop window

T = 1.0 / sample_rate
y = canal_fft
yf = fftpack.fft(y*w)
xf = np.linspace(0.0, 1.0/(2.0*T), N/2)

ax = fig3.add_subplot(2,1,2)
ax.hold(False)
ax.plot(xf, 2.0/N * np.abs(yf[:N/2]))
ax.grid()
ax.set_title("Channel Y")
ax.set_xlabel('Hz')
ax.set_xlim(xmax=max_freq)
ax.set_ylabel('g')



plt.show()
