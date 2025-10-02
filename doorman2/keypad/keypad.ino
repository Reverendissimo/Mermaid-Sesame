/* @file HelloKeypad.pde
|| @version 1.0
|| @author Alexander Brevig
|| @contact alexanderbrevig@gmail.com
||
|| @description
|| | Demonstrates the simplest use of the matrix Keypad library.
|| #
*/
#include <Keypad.h>
#define BUZZER  PIN_PB2
#define LED_RED PIN_PD4
#define LED_GREEN PIN_PC5

const byte ROWS = 4; //four rows
const byte COLS = 3; //three columns
char keys[ROWS][COLS] = {
  {'1','2','3'},
  {'4','5','6'},
  {'7','8','9'},
  {'*','0','#'}
};
byte rowPins[ROWS] = {PIN_PC1, PIN_PC0, PIN_PB5, PIN_PB4}; //connect to the row pinouts of the keypad
byte colPins[COLS] = {PIN_PB3, PIN_PB0, PIN_PD5}; //connect to the column pinouts of the keypad

bool quiet = true;
String buf;

Keypad keypad = Keypad( makeKeymap(keys), rowPins, colPins, ROWS, COLS );

void(* reset) (void) = 0; 

void click() {
  if (!quiet) {
    pinMode(BUZZER, OUTPUT);
    // too tired to check how to do proper PWM lol
    for(int i=0;i<10;i++) {
      digitalWrite(BUZZER, HIGH);
      delay(1);
      digitalWrite(BUZZER, LOW);
      delay(1);
    }
    pinMode(BUZZER, INPUT);
  }
}

void sad() {
  pinMode(BUZZER, OUTPUT);
  for(int i=0;i<75;i++) {
    digitalWrite(BUZZER, HIGH);
    delay(1);
    digitalWrite(BUZZER, LOW);
    delay(1);
  }
  for(int i=0;i<50;i++) {
    digitalWrite(BUZZER, HIGH);
    delay(1);
    digitalWrite(BUZZER, LOW);
    delay(2);
  }
  pinMode(BUZZER, INPUT);
}

void happy() {
  pinMode(BUZZER, OUTPUT);
  for(int i=0;i<25;i++) {
    digitalWrite(BUZZER, HIGH);
    delay(1);
    digitalWrite(BUZZER, LOW);
    delay(3);
  }
  for(int i=0;i<40;i++) {
    digitalWrite(BUZZER, HIGH);
    delay(1);
    digitalWrite(BUZZER, LOW);
    delay(2);
  }
  for(int i=0;i<45;i++) {
    digitalWrite(BUZZER, HIGH);
    delay(1);
    digitalWrite(BUZZER, LOW);
    delay(1);
  }
  pinMode(BUZZER, INPUT);
}

void setup(){
  Serial.begin(9600);
  keypad.setDebounceTime(1);
  pinMode(LED_RED, OUTPUT);
  pinMode(LED_GREEN, OUTPUT);
  digitalWrite(LED_GREEN, 0);
  delay(1000);
  digitalWrite(LED_GREEN, 1);
  happy();
}
  
void loop(){ 
  char key = keypad.getKey();
  
  if (key) {
  	/*
  		we don't really have a use for #/* keys; thus, we can define
  		magic key combos!

  		currently:
  		- *1337## resets the keypad
  	*/
    if (key == '*') {
      quiet = false;
      buf="";
      int i=0;
      while (true) {
        key = keypad.getKey();
        if (key) {
          click();
          buf+=key;
          i++;
        }
        if (i>6) break;
        if (buf == "1337##") {
          reset();
        }
      }
      quiet = true;
    }
    click();
    Serial.println(key);
  }
  while (Serial.available() > 0) {
    char a = Serial.read();
    if (a == 'H') {
      digitalWrite(LED_RED, HIGH);
      digitalWrite(LED_GREEN, LOW);
      happy();
      delay(1000);
      digitalWrite(LED_GREEN, HIGH);
    } else if (a == 'S') {
      digitalWrite(LED_GREEN, HIGH);
      digitalWrite(LED_RED, LOW);
      sad();
      delay(1000);
      digitalWrite(LED_RED, HIGH);
    } else if (a == 'F') { // flush
      digitalWrite(LED_GREEN, HIGH);
      digitalWrite(LED_RED, HIGH);
      quiet = true;
      pinMode(BUZZER, INPUT); // to be sure ;3
    } else if (a == 'G') { // green
      digitalWrite(LED_GREEN, LOW);
    } else if (a == 'R') { // red
      digitalWrite(LED_RED, LOW);
    } else if (a == 'Q') {
      quiet = false;
    }
  }
}
