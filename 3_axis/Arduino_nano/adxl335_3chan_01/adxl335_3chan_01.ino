/****************************************************
Program adxl335_3chan_01.ino
Program adxl335_3can_01.c modified:
- Uses Arduino structure.
10/04/2017
INI~
PAR~
*****************************************************/
#define MAX_BUFFER 6    //Buffer de datos de ADC. 3 canales.
#define MAX_PAQ 5   //Máximo tamaño de buffer de recepción.
#define BAUD 500000  //460800  //230400  //57600
#define cuenta_timer 49      //Prescaler 64, CTC, 5000 Hz
//-------------------------------------------------------
//------ Globals -----
static bool leer_adxl = false;
static bool enviar; 
static uint8_t paq[5];          //Command reception buffer.
static uint8_t paq_completo, index_paq;    //Pack management flags.  
static uint8_t datos[MAX_BUFFER];       //ADC data.
static uint8_t datos_cod[2*MAX_BUFFER];   //Maximum array size.
//---------------------
void setup() {  
    paq_completo = 0;
    index_paq = 0;
  
    enviar = false;

    cli(); // disable interrupts
    Serial.begin(BAUD);
  
    DDRB |= (1<<PB7);         //PB7 output
    DDRB |= (1<<PB1);         //PB1 output
  
    PORTB &= ~(1<<PB7);       //PB7 = 0
    PORTB &= ~(1<<PB1);       //PB1 = 0
  
    //---- Timer 0 ----
    TCCR0A &= ~(1<<WGM00);    //CTC mode
    TCCR0A |= (1<<WGM01);
    TCCR0B &= ~(1<<WGM02);
  
    OCR0A = cuenta_timer;
  
    TCCR0B |= (1<<CS00) | (1<<CS01);   //Prescaler = 64
    TCCR0B &= ~(1<<CS02);
  
    TIMSK0 = (1<<OCIE0A);    //Enable Timer0 interrupt, compare A
    //----- End Timer 0 -----
  
    //---- ADC ----
    ADMUX &= ~(1 << REFS0) & ~(1 << REFS1);      // Vref = AREF, REFS0 = REFS1 = 0
    ADCSRA &= ~(1 << ADPS0) & ~(1 << ADPS1);     //ADC prescaler 16. Max Freq ADC = 1MHz
    ADCSRA |= (1 << ADPS2);
    ADCSRA |= (1<<ADEN);     //Enable ADC
    //---- End ADC ----
    sei(); //Enable interrupts
}
void loop() {
    int conta_cod, i;
    uint8_t dato_rx[1];
    //--------- Read UART received data----------------
    if (Serial.available() > 0)
    {
        Serial.readBytes(dato_rx, 1); 
        if (dato_rx[0] == 0x7E)     //End of packet?
        {
            paq_completo = 1;
            index_paq = 0;        
        }
        else 
        {
            paq[index_paq] = dato_rx[0];
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
    if ((leer_adxl == true)  &&  (enviar == true))
    {     
        leer_adxl = false;

        ADMUX |= (1 << MUX0) | (1 << MUX2);  //Channel 5. MUX0 = MUX2 = 1
        ADMUX &= ~(1 << MUX1);               //MUX1 = 0
        ADCSRA |= (1<<ADSC);           // Start conversion
        //ait for conversion to complete 
        loop_until_bit_is_clear(ADCSRA, ADSC);
      
        datos[1] = ADCL;
        datos[0] = ADCH;
           
        ADMUX |= (1 << MUX1) | (1 << MUX2);  //Channel 6. MUX1 = MUX2 = 1
        ADMUX &= ~(1 << MUX0);                 //MUX0 = 0
        ADCSRA |= (1<<ADSC);           // Start conversion
        //Wait for conversion to complete
        loop_until_bit_is_clear(ADCSRA, ADSC);
      
        datos[3] = ADCL;
        datos[2] = ADCH;  

        ADMUX |= (1 << MUX0) | (1 << MUX1) | (1 << MUX2);   //Channel 7. MUX1 = MUX2 = MUX3 = 1
        ADCSRA |= (1<<ADSC);           // Start conversion
        loop_until_bit_is_clear(ADCSRA, ADSC);
      
        datos[5] = ADCL;
        datos[4] = ADCH;    
      
        //Encode datos[] in datos_cod[]
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
            Serial.write(datos_cod[i]);
        }
        Serial.write(0x7E);     //End of packet
    }         
}
//----------------------------------------
// Functions
//----------------------------------------
// Timer0 CTC service interrupt
//----------------------------------------
ISR(TIMER0_COMPA_vect)   //ISR Timer0 compere A
{
    PORTB ^= (1<<PB7);        //Invert PB7.
    leer_adxl = true;         //Read accelerometer data.
}

