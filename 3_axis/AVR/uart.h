/*
Programa uart.h
Código de 
http://www.downtowndougbrown.com/2014/08/microcontrollers-uarts/
*/

#ifndef UART_H_
#define UART_H_
 
#include <stdbool.h>
#include <stdint.h>
 
void uart_init(uint32_t baud);
void uart_write_char(char data);
char uart_read_char(void);
bool uart_rx_buffer_empty(void);
bool uart_tx_buffer_empty(void);
bool uart_rx_buffer_full(void);
bool uart_tx_buffer_full(void);
 
#endif /* UART_H_ */