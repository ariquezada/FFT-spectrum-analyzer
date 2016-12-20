/************************************************
Program adxl335_3can_01_en.c
- Samples and sends three ADC channels using the serial port.
- Serial port speed 5000000 baud. 
- Sampling speed 5000Hz, using Timer2 CTC mode, prescaler 64, counts 49.
- Waits for start (INI~) and finish (PAR~) commands.
- Packages are separated by 0x7E.
- CPU frequency 16MHz.
- Works with program fft_spectrum_gui_3can.py.
15/11/2016
************************************************/

/***********************************************
Includes
************************************************/
#include <avr/io.h>                   
#include <util/delay.h> 
#include <avr/interrupt.h>
#include "uart.h"               
/***********************************************
Macros and defines
************************************************/
#define MAX_BUFFER 6    //ADC data buffer. 3 channels.
#define MAX_PAQ 5       //Max reception byte size.

#define BAUD 500000  //460800  //230400  //57600

#define cuenta_timer 49      //Prescaler 64, CTC, 5000 Hz
//------------------------------------------------------

#define low(x)   ((x) & 0xFF)
#define high(x)   (((x)>>8) & 0xFF)

//------ Globals -----
bool leer_adxl = false;
//---------------------

int main(void) 
{
    uint8_t dato_rx;
	
	bool enviar;
	
	uint8_t paq[5];                     //Command reception packet.
    uint8_t paq_completo, index_paq;    //Received packet handling flags.
	
	uint8_t datos[MAX_BUFFER];          //ADC samples.
    uint8_t datos_cod[2*MAX_BUFFER];   //Coded data. Max double size of original array.
    int conta_cod, i;
	

    paq_completo = 0;
    index_paq = 0;
	
	enviar = false;

	cli();                            //Disable interrupts.
    uart_init(BAUD);
	
	DDRB |= (1<<PB0);         //PB0 as output.
	DDRB |= (1<<PB1);         //PB1 as otuput.
	
	PORTB &= ~(1<<PB0);       //PB0 = 0
	PORTB &= ~(1<<PB1);       //PB1 = 0
	
	//---- Timer 2 ----
	TCCR2A &= ~(1<<WGM20);    //CTC mode
	TCCR2A |= (1<<WGM21);
	TCCR2B &= ~(1<<WGM22);
	
	OCR2A = cuenta_timer;
	
	TCCR2B &= ~(1<<CS20) & ~(1<<CS21);   //Prescaler = 64.
	TCCR2B |= (1<<CS22);
	
    TIMSK2 = (1<<OCIE2A);     //Enable Timer2 interrupt, comp A.
	
	//---- ADC ----
	ADMUX &= ~(1 << REFS0) & ~(1 << REFS1);      // Vref = AREF, REFS0 = REFS1 = 0
    ADCSRA &= ~(1 << ADPS0) & ~(1 << ADPS1);     //ADC prescaler 16. Max Freq ADC = 1MHz
	ADCSRA |= (1 << ADPS2);
    ADCSRA |= (1<<ADEN);     //Enable ADC
	//--------
	sei();                   //Enable interrupts.
	
	
	while (1) 
    {    		
		//--------- Read data received in UART ----------------
		
		if (uart_rx_buffer_empty() == false)
		{
		    dato_rx = uart_read_char();
			
			if (dato_rx == 0x7E)        //End of packet?
		    {
		        paq_completo = 1;
			    index_paq = 0;			  
	        }
		    else 
		    {
		        paq[index_paq] = dato_rx;
			    ++index_paq;
		    }
		    if (index_paq > MAX_PAQ)
		    {
		        index_paq = 0;
		    }
		}
		
		//---------- If packet complete ------
		
		if (paq_completo == 1)
	    {
	        paq_completo = 0;
			
			if ((paq[0] == 'I') && (paq[1] == 'N') && (paq[2] == 'I'))
			{
			    enviar = true;
			}
			
			if ((paq[0] == 'P') && (paq[1] == 'A') && (paq[2] == 'R'))
			{
			    enviar = false;
			}						
		}
		
		if ((leer_adxl == true)	 &&  (enviar == true))
		{		  
            leer_adxl = false;
			
			ADMUX |= (1 << MUX0) | (1 << MUX2);  //Channel 5. MUX0 = MUX2 = 1
            ADMUX &= ~(1 << MUX1);               //MUX1 = 0
			ADCSRA |= (1<<ADSC);                 //Start conversion
        
			loop_until_bit_is_clear(ADCSRA, ADSC);   //Wait for conversion to complete
			
			datos[1] = ADCL;
			datos[0] = ADCH;
			
			ADMUX |= (1 << MUX1) | (1 << MUX2);    //Channel 6. MUX1 = MUX2 = 1
            ADMUX &= ~(1 << MUX0);                 //MUX0 = 0
			ADCSRA |= (1<<ADSC);                   //Start conversion
        
			loop_until_bit_is_clear(ADCSRA, ADSC);  //Wait for conversion to complete.
				
			datos[3] = ADCL;
			datos[2] = ADCH;	

            ADMUX |= (1 << MUX0) | (1 << MUX1) | (1 << MUX2);  //Channel 7. MUX1 = MUX2 = MUX3 = 1
			ADCSRA |= (1<<ADSC);                                //Start conversion
			loop_until_bit_is_clear(ADCSRA, ADSC);
			
			datos[5] = ADCL;
			datos[4] = ADCH;		
			
            //--- Packet encoding ----
			conta_cod = 0;
            for(i=0; i<MAX_BUFFER; ++i)
            {
                if (datos[i] == 0x7E)
                {
                    datos_cod[conta_cod] = 0x7D;
                    ++conta_cod;
                    datos_cod[conta_cod] = 0x5E;
                    ++conta_cod;
                }
                else if (datos[i] == 0x7D)
                {
                    datos_cod[conta_cod] = 0x7D;
                    ++conta_cod;
                    datos_cod[conta_cod] = 0x5D;
                    ++conta_cod;
                }
                else
                {
                    datos_cod[conta_cod] = datos[i];
                    ++conta_cod;
                }
            }
			
			//Send datos_cod[]
            for(i=0; i < conta_cod; ++i)
            {
                uart_write_char(datos_cod[i]);
            }
			
            uart_write_char(0x7E);     //End of packet	
		}	
		
    }  //while(1) 
	
	return (0);                            /* This line is never reached */
}
//----------------------------------------
// Functions
//----------------------------------------
// Timer 2 CTC interrupt service routine.
//----------------------------------------
ISR(TIMER2_COMPA_vect)   //ISR Timer2 comp A
{
    PORTB ^= (1<<PB0);        //Inverti PB0 (just for testing).
	leer_adxl = true;         //Read accelerometer data.
}
