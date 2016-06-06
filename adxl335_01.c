/************************************************
Program adxl335_01.c   ¡¡¡ OK !!!
- Reads two ADC channels ands sends data to serial port.
- Receives a packet on the serial port to start or stop sending data.
- Timer 2 in CTC mode with prescaler in 62, and 49count, 5000 Hz frequency.
- FCPU de 16 MHz.
- Maximum ADC sampling frequency is limited to 1 MHz.
01/06/2016
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
#define MAX_BUFFER 4    //ADC data buffer. 2 channels.
#define MAX_PAQ 5       //Maximum size for receiving buffer.

#define BAUD 500000     //0.5 Mbps

#define cuenta_timer 49   

//------ Globals -----
bool leer_adxl = false;      //To read or not the adxl335
//---------------------

int main(void) 
{
    uint8_t dato_rx;
	
	bool enviar;
	
	uint8_t paq[5];                     //Data received packet (commands).
    uint8_t paq_completo, index_paq;    //Received package handling flags.
	
	uint8_t datos[MAX_BUFFER];          //ADC data.
    uint8_t datos_cod[2*MAX_BUFFER];   //Maximun doble the original array size.
    int conta_cod, i;
	

    paq_completo = 0;
    index_paq = 0;
	
	enviar = false;

	cli();                           //Disable interrupts.
    uart_init(BAUD);
	
	DDRB |= (1<<PB0);         //PB0 as output.
	DDRB |= (1<<PB1);         //PB1 as output.
	
	PORTB &= ~(1<<PB0);       //PB0 = 0
	PORTB &= ~(1<<PB1);       //PB1 = 0
	
	//---- Timer 2 ----
	TCCR2A &= ~(1<<WGM20);    //CTC mode.
	TCCR2A |= (1<<WGM21);
	TCCR2B &= ~(1<<WGM22);
	
	OCR2A = cuenta_timer;
	
	TCCR2B &= ~(1<<CS20) & ~(1<<CS21);   //Prescaler in 64.
	TCCR2B |= (1<<CS22);
	
    TIMSK2 = (1<<OCIE2A);    //Enable Timer2 interrupt, compara A.
    //----- End Timer 2 -----
	
	//---- ADC ----
	ADMUX &= ~(1 << REFS0) & ~(1 << REFS1);      // Vref = AREF, REFS0 = REFS1 = 0.
    ADCSRA &= ~(1 << ADPS0) & ~(1 << ADPS1);     //ADC prescaler 16. Max Freq ADC = 1MHz.
	ADCSRA |= (1 << ADPS2);
    ADCSRA |= (1<<ADEN);                          //Enable ADC.
	//---- End ADC ----
	
	sei();           //Enable interrupts,
	
	
	while (1) 
    {    		
		//--------- Read data received in UART ----------------
		
		if (uart_rx_buffer_empty() == false)
		{
		    dato_rx = uart_read_char();
			
			if (dato_rx == 0x7E)          //End of packet?
		    {
		        paq_completo = 1;
			    index_paq = 0;			  
	        }
		    else 
		    {
		        paq[index_paq] = dato_rx;
			    ++index_paq;
		    }
		    if (index_paq > MAX_PAQ)     //Is array full?
		    {
		        index_paq = 0;
		    }
		}
		
		//---------- If packet is complete ------
		
		if (paq_completo == 1)
	    {
	        paq_completo = 0;
			
			if ((paq[0] == 'I') && (paq[1] == 'N') && (paq[2] == 'I'))   //Comand Start (INI).
			{
			    enviar = true;
			}
			
			if ((paq[0] == 'P') && (paq[1] == 'A') && (paq[2] == 'R'))   //Command stop (PAR).
			{
			    enviar = false;
			}						
		}
		
		//-------- Send data ?
		if ((leer_adxl == true)	 &&  (enviar == true))
		{		  
            leer_adxl = false;
			
			ADMUX |= (1 << MUX0) | (1 << MUX2);  //Channel 5. MUX0 = MUX2 = 1
            ADMUX &= ~(1 << MUX1);               //MUX1 = 0
			ADCSRA |= (1<<ADSC);                  //Start conversion
			loop_until_bit_is_clear(ADCSRA, ADSC);    //Wait for conversion to complete.
			
			datos[1] = ADCL;
			datos[0] = ADCH;
			
			ADMUX |= (1 << MUX1) | (1 << MUX2);    //Channel 6. MUX1 = MUX2 = 1
            ADMUX &= ~(1 << MUX0);                 //MUX0 = 0
			ADCSRA |= (1<<ADSC);              //Start conversion.
			loop_until_bit_is_clear(ADCSRA, ADSC);   //Wait for conversion to complete.
			
			datos[3] = ADCL;
			datos[2] = ADCH;			
			
			//Codiing datos[] in datos_cod[] - PPT
            conta_cod = 0;
            for(i=0; i<MAX_BUFFER; ++i)
            {
                if (datos[i] == 0x7E)
                {
                    datos_cod[conta_cod] = 0x7D;    //Escape character 0x7E.
                    ++conta_cod;
                    datos_cod[conta_cod] = 0x5E;
                    ++conta_cod;
                }
                else if (datos[i] == 0x7D)
                {
                    datos_cod[conta_cod] = 0x7D;    //Escape character 0x7D.
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
			
			//Transmmit datos_cod[]
            for(i=0; i < conta_cod; ++i)
            {
                uart_write_char(datos_cod[i]);
            }
			
            uart_write_char(0x7E);     //End of packet.	
		}	
				
		
    }  //From while(1).
	
	return (0);                            /* This line is never reached */
}
//----------------------------------------
// Timer2 CTC service interrupt.
//----------------------------------------
ISR(TIMER2_COMPA_vect)              //ISR Timer2 compara A
{
    PORTB ^= (1<<PB0);             //Invert PB0. Testing.
	leer_adxl = true;               //Read data from analog input.
}

