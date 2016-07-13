#!/usr/bin/env python
# -*- coding: cp1252 -*-
# Program fft_spectrum_gui.py   ¡¡ OK !!
# - Based on program frame_tab_plot_07.py
# - Sample acceleration data from a ADXL335 accelerometer.
# - Plot sampled data and its FFT spectrum.
# - Save data on file and open files with saved data.
# - Serial communication with microcontroller.
# - Serial port selection.
# - RadioButtons to select a Window function to apply.
# 13/07/2016

import matplotlib
matplotlib.use('TkAgg')

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
# implement the default mpl key bindings
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure

from scipy import fftpack, arange, signal
import numpy as np

import sys
if sys.version_info[0] < 3:
    import Tkinter as Tk
else:
    import tkinter as Tk

import tkFileDialog
import tkMessageBox
from ScrolledText import ScrolledText
import ttk

import string
import serial
import serial.tools.list_ports
import time

datos_a_leer = 16384     # Amount of samples to read.
sample_rate = 5000       # Sampling frequency (SPS).
g_scale = 3.0/512        # +- 3g. 10 bit ADC.
max_freq = 1500          # Maximum signal frequency, X and Y axis (accelerometer).

g_canal_1 = []           #Global canal_1
g_canal_2 = []           #Global canal_2


def scan_serial():
    """ Scans for serial ports"""
    portnames = []
    ports = (list(serial.tools.list_ports.comports()))
    for index in range(len(ports)):
        portnames.append(ports[index][0])
    return portnames


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


def conv_str_tag(canal, tag):
    """ Convert every channel from int to str, separated by a coma 
    and adds tags at the beggining and end. """
    n = len(canal)
    s_canal = '<' + tag + '>'
    for i in range(n-1):
        s_canal = s_canal + str(canal[i]) + ','
    s_canal = s_canal + str(canal[n-1]) + '</'+ tag + '>'
    return s_canal


def grabar(canal_1, canal_2, archivo):
    """ Saves X and Y axis data on file archivo"""
    str_canal = ''
    str_canal += conv_str_tag(canal_1, 'L1') + '\n'
    str_canal += conv_str_tag(canal_2, 'L2') + '\n'

    str_aux = ''
    str_aux += '<nd>' + str(datos_a_leer) + '</nd>' + '\n'
    str_aux += '<sr>' + str(sample_rate) + '<sr>' + '\n'
    #str_aux += '<gn>' + str(ganancia) + '</gn>' + '\n'
        
    # Write to file
    arch = open(archivo, "w")
    arch.write(str_aux)
    arch.write(str_canal)
    arch.close()

    
class Application:


    def __init__(self, parent):
        self.parent = parent
        self.frames()
        self.f_saved = True       #Sampled data saved
        root.protocol("WM_DELETE_WINDOW", self.on_closing)


    def on_closing(self):
        if (self.f_saved==False):
            if tkMessageBox.askokcancel("Quit", "Sampled data not saved. Do you wanto to quit?"):
                root.destroy()
        else:
            root.destroy()


    def frames(self):
        frame1 = Tk.Frame(root, bd=5, relief='raised', borderwidth=1)
        frame2 = Tk.Frame(root, bd=5, relief='raised')

        note = ttk.Notebook(frame2)
        self.tab1 = ttk.Frame(note)
        self.tab2 = ttk.Frame(note)

        note.add(self.tab1, text = "Frquency")
        note.add(self.tab2, text = "Time")

        # Positioning
        frame1.pack(side='left', fill='both', padx=5, pady=5)
        frame2.pack(side='right', fill='both', expand='true')

        boton_open = Tk.Button(frame1, text ="Open file", command=self.open_file)
        boton_save = Tk.Button(frame1, text ="Save to file", command=self.save_file)
        boton_scan = Tk.Button(frame1, text="Scan serial ports", command=self.scan_ports)
        boton_read = Tk.Button(frame1, text="Read serial data", command=self.read_serial)

        label1 = Tk.Label(frame1, text="Select Serial Port:")
        self.sel_puerto = ttk.Combobox(frame1, textvariable='', state="readonly")
        portnames = scan_serial()
        self.sel_puerto['values'] = portnames        
        if (portnames != []):
            self.sel_puerto.current(0)

        self.text_message = ScrolledText(frame1, height=10, width=20)

        self.window_var = Tk.IntVar()
        self.window_var.set(1)        #Option rectangular window 
        radio_button1 = Tk.Radiobutton(frame1, text="Rectangular Window",
                                       variable=self.window_var, value=1, command=self.win_sel)
        radio_button2 = Tk.Radiobutton(frame1, text="Hann Window",
                                       variable=self.window_var, value=2, command=self.win_sel)
        radio_button3 = Tk.Radiobutton(frame1, text="Flattop Window",
                                       variable=self.window_var, value=3, command=self.win_sel)
        # Grid
        boton_open.grid(row=1, column=0, padx=5, pady=5)
        boton_save.grid(row=2, column=0, padx=5, pady=5)
        boton_scan.grid(row=3, column=0, padx=5, pady=5)
        label1.grid(row=4, column=0, padx=5, pady=5)
        self.sel_puerto.grid(row=5, column=0, padx=5, pady=5)
        boton_read.grid(row=6, column=0, padx=5, pady=5)
        self.text_message.grid(row=7, column=0, padx=5, pady=5)
        radio_button1.grid(row=8, column=0, sticky="W")
        radio_button2.grid(row=9, column=0, sticky="W")
        radio_button3.grid(row=10, column=0, sticky="W")

        #note.grid(row = 0, column=0)
        note.pack(side='top', fill='both', padx=5, pady=5)

        #Figure 1
        fig1 = Figure(figsize=(10,7))
        fig1.suptitle('Sampled signal - Acceleration')
        ax_11 = fig1.add_subplot(2,1,1)
        ax_11.hold(False)
        ax_11.set_title("Channel X")
        ax_11.set_ylabel('g')
        ax_11.grid()                       #Shows grid.

        ax_12 = fig1.add_subplot(2,1,2)
        ax_12.hold(False)
        ax_12.set_title("Channel Y")
        ax_12.set_xlabel('ms')
        ax_12.set_ylabel('g')
        ax_12.grid()                       #Shows grid.

        #Figure 2
        fig2 = Figure(figsize=(10,7))
        fig2.suptitle('FFT spectrum')

        ax_21 = fig2.add_subplot(2,1,1)
        ax_21.hold(False)
        ax_21.set_title("Channel X")
        ax_21.set_ylabel('g')
        ax_21.set_xlim(xmax=max_freq)
        ax_21.grid()            

        ax_22 = fig2.add_subplot(2,1,2)
        ax_22.hold(False)
        ax_22.set_title("Channel Y")
        ax_22.set_xlabel('Hz')
        ax_22.set_xlim(xmax=max_freq)
        ax_22.set_ylabel('g')
        ax_22.grid()            

        # Canvas
        self.canvas2 = FigureCanvasTkAgg(fig1, master=self.tab2)
        self.canvas2.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)

        self.toolbar2 = NavigationToolbar2TkAgg(self.canvas2, self.tab2)
        self.toolbar2.update()
        self.canvas2._tkcanvas.pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)

        self.canvas1 = FigureCanvasTkAgg(fig2, master=self.tab1)
        self.canvas1.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)

        self.toolbar1 = NavigationToolbar2TkAgg(self.canvas1, self.tab1)
        self.toolbar1.update()
        self.canvas1._tkcanvas.pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)


    def read_serial(self):
        puerto = self.sel_puerto.get()
        print(puerto)
        message_string = "Port: {0} \n".format(puerto)
        self.show_message(self.text_message, message_string)

        estado_serial = False
        try:
            serial_avr = serial.Serial(port=puerto, baudrate=500000,
                           bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE,
                           stopbits=serial.STOPBITS_ONE, timeout=0)

            time.sleep(2)            # waiting the initialization...
            print("Initializing")
            message_string = "Initializing... \n"
            self.show_message(self.text_message, message_string)
    
            if (serial_avr.isOpen() == True):
                estado_serial = True
            else:
                estado_serial = False
        except (serial.SerialException, ValueError) as ex:
            #print "Can´t open serial port: " + str(ex)
            tkMessageBox.showerror( "Result", "Can't open serial port: " + str(ex))

        if (estado_serial == True):
            global g_canal_1, g_canal_2, datos_a_leer
            canal_1 = []
            canal_2 = []
            buffer = ''
            paquete = ''
            valores = []
            serial_avr.flushInput()
            serial_avr.flushOutput()

            valores_decod = []

            conta_datos_rx = 0;         #Received samples counter.

            print("Sending INI")
            message_string = "Sending INI \n"
            self.show_message(self.text_message, message_string)
            
            serial_avr.write('INI')         #Start data sampling command.
            #serial_avr.write(chr(0x22))    #CRC 'INI'. Not used.
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
            self.text_message.config(state=Tk.NORMAL)        #Enable to modify
            self.text_message.insert(Tk.END, "Sending PAR \n")
            self.text_message.config(state=Tk.DISABLED)      #Disable - Read only
            root.update_idletasks()        #Needed to make message visible
            
            serial_avr.write('PAR')          #Stop data sampling.
            serial_avr.write(chr(0x7E))      #End of packet.

            serial_avr.close()      #Close serial port.

            print("Amount of samples channel 1: %s" %len(canal_1))
            print("Amount of samples channel 2: %s" %len(canal_2))
            message_string = "Amount of samples channel 1: {0} \n".format(len(canal_1))
            message_string += "Amount of samples channel 2: {0} \n".format(len(canal_2))
            self.show_message(self.text_message, message_string)
            
            #Keep a copy of the original values
            g_canal_1 = canal_1[:]            #Copy list by value not by reference
            g_canal_2 = canal_2[:]

            self.f_saved = False                #Sampled data not saved

            self.window_var.set(1)        #Option rectangular window
            self.plot(self.tab1, self.tab2, canal_1, canal_2, win_var=1)


    def show_message(self, text_message, message_string):
        """Shows messages on a scrollable textbox"""
        text_message.config(state=Tk.NORMAL)        #Enable to modify
        text_message.insert(Tk.END, message_string)
        text_message.config(state=Tk.DISABLED)      #Disable - Read only
        text_message.see("end")        #Show the "end" of text
        root.update_idletasks()        #Needed to make message visible
        

    def scan_ports(self):
        portnames = []
        portnames = scan_serial()
        self.sel_puerto['values'] = portnames
        if (portnames != []):
            self.sel_puerto.current(0)



    def plot(self, tab1, tab2, canal_1, canal_2, win_var=1):
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
        #print("Vdc Channel 1: {0}, Vdc Channel 2: {1}".format(vdc_canal_1, vdc_canal_2))

        # Substract DC offset
        for indice in X:
            canal_1[indice] -= vdc_canal_1
            canal_2[indice] -= vdc_canal_2

        #----------------- Plotting ----------
        X1 = np.linspace(0, num_datos/5, num=num_datos)     # X axis, 5000 sps, 1/5 ms.

        # Figure 1. Sampled signals.
        #Channel X
        ax_11, ax_12 = self.canvas2.figure.get_axes()
        ax_11.clear()
        ax_11.plot(X1,canal_1)
        ax_11.set_title("Channel X")
        ax_11.set_ylabel('g')
        ax_11.grid()                       #Shows grid.
        
        #Channel Y
        ax_12.clear()
        ax_12.plot(X1,canal_2)
        ax_12.set_title("Channel Y")
        ax_12.set_xlabel('ms')
        ax_12.set_ylabel('g')
        ax_12.grid()                       #Shows grid.

        # Figure 2. FFT from signals.
        #Channel X
        canal_fft = []
        canal_fft = canal_1

        N = len(canal_fft)         # length of the signal

        #Window function
        if(win_var == 2):
            w = signal.hann(N, sym=False)      #Hann (Hanning) window
        elif(win_var == 3):
            w = signal.flattop(N, sym=False)   #Flattop window
        else:
            w = 1                              #Rectangular window
        
        T = 1.0 / sample_rate
        y = canal_fft
        yf = fftpack.fft(y*w)
        xf = np.linspace(0.0, 1.0/(2.0*T), N/2)

        ax_21, ax_22 = self.canvas1.figure.get_axes()
        ax_21.clear()
        ax_21.plot(xf, 2.0/N * np.abs(yf[:N/2]))
        ax_21.grid()
        ax_21.set_title("Channel X")
        ax_21.set_ylabel('g')
        ax_21.set_xlim(xmax=max_freq)

        #Channel Y
        canal_fft = []
        canal_fft = canal_2

        N = len(canal_fft)              # length of the signal
        T = 1.0 / sample_rate
        y = canal_fft
        yf = fftpack.fft(y*w)
        xf = np.linspace(0.0, 1.0/(2.0*T), N/2)

        ax_22.clear()
        ax_22.plot(xf, 2.0/N * np.abs(yf[:N/2]))
        ax_22.grid()
        ax_22.set_title("Channel Y")
        ax_22.set_xlabel('Hz')
        ax_22.set_xlim(xmax=max_freq)
        ax_22.set_ylabel('g')

        self.canvas1.draw()
        self.canvas2.draw()


    def win_sel(self):
        """Window selection. Every time a window is selected,
        the FFT spectrum is calculated, applying the selected window function"""
        global g_canal_1, g_canal_2
        canal_1 = g_canal_1[:]            #Copy list by value not by reference
        canal_2 = g_canal_2[:]            
        win_var = self.window_var.get()
        if(len(canal_1) != 0):            #Apply only if data available
            self.plot(self.tab1, self.tab2, canal_1, canal_2, win_var)


    def open_file(self):
        """Opens dialog to select a file, reads data from file and plots the data"""
        ftypes = [('Text files', '*.txt'), ('All files', '*')]
        dlg = tkFileDialog.Open(root, filetypes = ftypes)
        fl = dlg.show()
        if fl != '':
            # Open file for reading
            arch = open(fl, "r")
            datos_arch = arch.read()
            # Searches for every channel, delimited by L1 and L2 tags.
            canal_1 = extraer_int_tag(datos_arch, 'L1')
            canal_2 = extraer_int_tag(datos_arch, 'L2')

            print("Amount of samples in channel 1: %s" %len(canal_1))
            print("Amount of samples on channel 2: %s" %len(canal_2))
            message_string = "Amount of samples channel 1: {0} \n".format(len(canal_1))
            message_string += "Amount of samples channel 2: {0} \n".format(len(canal_2))
            self.show_message(self.text_message, message_string)

            global g_canal_1, g_canal_2
            #Keep a copy of the original values
            g_canal_1 = canal_1[:]            #Copy list by value not by reference
            g_canal_2 = canal_2[:]

            self.window_var.set(1)        #Option rectangular window
            self.plot(self.tab1, self.tab2, canal_1, canal_2, win_var=1)


    def save_file(self):
        ftypes = [('Text files', '*.txt'), ('All files', '*')]
        dlg = tkFileDialog.SaveAs(root, filetypes = ftypes)
        fl = dlg.show()
        if fl != '':
            global g_canal_1, g_canal_2
            if (len(g_canal_1) > 0):
                grabar(g_canal_1, g_canal_2, fl)
                self.f_saved = True               #Sampled data saved
            else:
                print("No samled data to save")
                message_string = "No samled data to save\n"
                self.show_message(self.text_message, message_string)


if __name__ == '__main__':
    root = Tk.Tk()
    root.title('FFT spectrum analyser for machinery vibration')
    app = Application(root)
    root.mainloop()
