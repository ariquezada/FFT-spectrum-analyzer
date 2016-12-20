/*
Programa uart.c
Código de
http://www.downtowndougbrown.com/2014/08/microcontrollers-uarts/
Velocidades UART: http://wormfood.net/avrbaudcalc.php
Librería de UART para transmisión y recepción,
con buffer circular para Rx y Tx, e iterrupciones.
*/

#include "uart.h"
#include <avr/io.h>
#include <avr/interrupt.h>
 
#define RING_SIZE   64    //Tamaño de buffers Tx y Rx.
 
static volatile uint8_t tx_ring_head;
static volatile uint8_t tx_ring_tail;
static volatile char tx_ring_data[RING_SIZE];
 
static volatile uint8_t rx_ring_head;
static volatile uint8_t rx_ring_tail;
static volatile char rx_ring_data[RING_SIZE];
 
static int tx_ring_add(char c);
static int tx_ring_remove(void);
static int rx_ring_add(char c);
static int rx_ring_remove(void);
 
void uart_init(uint32_t baud) {

    // Set baud rate
    UBRR0 = (F_CPU / (16*baud)) - 1;

    UCSR0B = (1 << RXEN0) | (1 << TXEN0) | (1 << RXCIE0);  //Tx, Rx e interrupciones
    UCSR0C = (1<<UCSZ01)|(1<<UCSZ00);   //8 bits de datos, 1 de stop
 
    // Clear out head and tail just in case
    tx_ring_head = 0;
    rx_ring_head = 0;
    tx_ring_tail = 0;
    rx_ring_tail = 0;
}
 
void uart_write_char(char data) {
    // Wait until there's room in the ring buffer
    while (uart_tx_buffer_full());
 
    // Add the data to the ring buffer now that there's room
    tx_ring_add(data);
 
    // Ensure the data register empty interrupt is turned on
    // (it gets turned off automatically when the UART is idle)
    UCSR0B |= (1 << UDRIE0);
}
 
char uart_read_char(void) {
    // Wait until a character is available to read
    while (uart_rx_buffer_empty());
 
    // Then return the character
    return (char)rx_ring_remove();
}
 
bool uart_rx_buffer_empty(void) {
    // If the head and tail are equal, the buffer is empty.
    return (rx_ring_head == rx_ring_tail);
}
 
bool uart_tx_buffer_empty(void) {
    // If the head and tail are equal, the buffer is empty.
    return (tx_ring_head == tx_ring_tail);
}
 
bool uart_rx_buffer_full(void) {
    // If the head is one slot behind the tail, the buffer is full.
    return ((rx_ring_head + 1) % RING_SIZE) == rx_ring_tail;
}
 
bool uart_tx_buffer_full(void) {
    // If the head is one slot behind the tail, the buffer is full.
    return ((tx_ring_head + 1) % RING_SIZE) == tx_ring_tail;
}
 
static int tx_ring_add(char c) {
    uint8_t next_head = (tx_ring_head + 1) % RING_SIZE;
    if (next_head != tx_ring_tail) {
        /* there is room */
        tx_ring_data[tx_ring_head] = c;
        tx_ring_head = next_head;
        return 0;
    } else {
        /* no room left in the buffer */
        return -1;
    }
}
 
static int tx_ring_remove(void) {
    if (tx_ring_head != tx_ring_tail) {
        int c = tx_ring_data[tx_ring_tail];
        tx_ring_tail = (tx_ring_tail + 1) % RING_SIZE;
        return c;
    } else {
        return -1;
    }
}
 
static int rx_ring_add(char c) {
    uint8_t next_head = (rx_ring_head + 1) % RING_SIZE;
    if (next_head != rx_ring_tail) {
        /* there is room */
        rx_ring_data[rx_ring_head] = c;
        rx_ring_head = next_head;
        return 0;
    } else {
        /* no room left in the buffer */
        return -1;
    }
}
 
static int rx_ring_remove(void) {
    if (rx_ring_head != rx_ring_tail) {
        int c = rx_ring_data[rx_ring_tail];
        rx_ring_tail = (rx_ring_tail + 1) % RING_SIZE;
        return c;
    } else {
        return -1;
    }
}
 
ISR(USART_RX_vect) {
    char data = UDR0;
    rx_ring_add(data);
}
 
ISR(USART_UDRE_vect) {
    if (!uart_tx_buffer_empty()) {
        // Send the next character if we have one to send
        UDR0 = (char)tx_ring_remove();
    } else {
        // Turn off the data register empty interrupt if
        // we have nothing left to send
        UCSR0B &= ~(1 << UDRIE0);
    }
}