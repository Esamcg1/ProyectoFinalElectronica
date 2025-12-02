#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <DHT.h>
#include <Servo.h>
#include <SPI.h>
#include <MFRC522.h>

// ----------- CONFIGURACIÓN HARDWARE -----------
LiquidCrystal_I2C lcd(0x27, 16, 2);

#define DHTPIN 2
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

#define LDR_PIN A1        
int umbralLuz = 500;

#define MOTOR_PIN 7       
#define RELAY_PIN 8       
#define PIR_PIN 3         
#define SERVO_PIN 9       

#define TOUCH_PIN 10       // Botón táctil

// ----------- RFID RC522 -----------
#define SS_PIN 4
#define RST_PIN 5
MFRC522 rfid(SS_PIN, RST_PIN);

// UID Permitido (A3 FB 16 FD)
byte tarjetaPermitida[] = {0xA3, 0xFB, 0x16, 0xFD};

Servo servo;

bool puertaAbierta = false;
unsigned long tiempoUltimaDeteccion = 0;

// Tiempo abierto 10s
const unsigned long tiempoCierre = 10000UL; 

// Modo manual por botón táctil
bool overridePorBoton = false;
bool toqueAnterior = false;

// ----------- FUNCIONES SERVICIO -----------
// Apertura suave (rápida)
void abrirPuertaSuave() {
  Serial.println(">> Abriendo puerta...");
  for (int ang = 0; ang <= 90; ang++) {
    servo.write(ang);
    delay(8);
  }
}

// Cierre suave (rápida)
void cerrarPuertaSuave() {
  Serial.println(">> Cerrando puerta...");
  for (int ang = 90; ang >= 0; ang--) {
    servo.write(ang);
    delay(8);
  }
}

// Lectura DHT con reintentos
bool leerDHTconRetry(float &temp, float &hum, int intentos = 3, unsigned long esperaMs = 250) {
  for (int i = 0; i < intentos; ++i) {
    temp = dht.readTemperature();
    hum = dht.readHumidity();
    if (!isnan(temp) && !isnan(hum)) return true;
    delay(esperaMs);
  }
  return false;
}

// ----------- RFID ----------
bool esTarjetaValida() {
  if (rfid.uid.size != 4) return false;

  for (byte i = 0; i < 4; i++) {
    if (rfid.uid.uidByte[i] != tarjetaPermitida[i])
      return false;
  }
  return true;
}

bool leerRFID() {

  if (!rfid.PICC_IsNewCardPresent()) return false;
  if (!rfid.PICC_ReadCardSerial()) return false;

  // --- Mostrar UID en Serial ---
  Serial.print("Tarjeta detectada UID: ");
  for (byte i = 0; i < rfid.uid.size; i++) {
    Serial.print(rfid.uid.uidByte[i], HEX);
    Serial.print(" ");
  }
  Serial.println();

  bool valida = esTarjetaValida();

  if (valida) Serial.println(">> TARJETA VALIDA - Acceso permitido");
  else        Serial.println(">> Tarjeta NO autorizada");

  rfid.PICC_HaltA();
  return valida;
}

// ----------- SETUP -----------
void setup() {
  Serial.begin(115200);
  Serial.println("\n--- Sistema Iniciado ---");

  lcd.init();
  lcd.backlight();

  dht.begin();
  servo.attach(SERVO_PIN);
  servo.write(0);

  pinMode(MOTOR_PIN, OUTPUT);
  pinMode(RELAY_PIN, OUTPUT);
  pinMode(PIR_PIN, INPUT);
  pinMode(LDR_PIN, INPUT);
  pinMode(TOUCH_PIN, INPUT);

  digitalWrite(MOTOR_PIN, LOW);
  digitalWrite(RELAY_PIN, HIGH);

  lcd.clear();
  lcd.setCursor(0,0);
  lcd.print("Iniciando...");
  delay(800);
  lcd.clear();

  // Inicializar RFID
  SPI.begin();
  rfid.PCD_Init();

  Serial.println("RFID listo. Acerca una tarjeta...");
}

// ----------- LOOP -----------
void loop() {

  // --- Lectura de LDR ---
  int valorLDR = analogRead(LDR_PIN);
  bool esNoche = (valorLDR < umbralLuz);

  if (esNoche) digitalWrite(RELAY_PIN, LOW);
  else digitalWrite(RELAY_PIN, HIGH);

  // --- Lectura DHT ---
  float t = NAN, h = NAN;
  bool okDHT = leerDHTconRetry(t, h, 3, 200);

  if (!okDHT) {
    lcd.clear();
    lcd.setCursor(0,0);
    lcd.print(" ERROR DHT22 ");
    lcd.setCursor(0,1);
    lcd.print("Revisar sensor");
    delay(800);
    return;
  }

  // --- Motor por temperatura ---
  if (t >= 30) digitalWrite(MOTOR_PIN, HIGH);
  else digitalWrite(MOTOR_PIN, LOW);

  // --- BOTÓN TÁCTIL ---
  bool toque = digitalRead(TOUCH_PIN);

  if (toque && !toqueAnterior) {

    if (!overridePorBoton) {
      overridePorBoton = true;

      if (!puertaAbierta) {
        abrirPuertaSuave();
        puertaAbierta = true;
      } else {
        cerrarPuertaSuave();
        puertaAbierta = false;
      }

    } else {
      overridePorBoton = false;
    }
  }

  toqueAnterior = toque;

  // --- MODO MANUAL ---
  if (overridePorBoton) {

    lcd.clear();

    lcd.setCursor(0,0);
    lcd.print("T:");
    lcd.print(t,1);
    lcd.print(" H:");
    lcd.print(h,0);

    lcd.setCursor(0,1);
    lcd.print("MANUAL MODE ");

    delay(200);
    return;
  }

  // --- MODO AUTOMÁTICO ---
  if (!esNoche) {

    // --- PIR O RFID activan la puerta ---
    if (digitalRead(PIR_PIN) == HIGH || leerRFID()) {

      if (digitalRead(PIR_PIN) == HIGH) {
        Serial.println("PIR detectó movimiento");
      }

      if (!puertaAbierta) {
        abrirPuertaSuave();
        puertaAbierta = true;
      }
      tiempoUltimaDeteccion = millis();
    }

    // Cierre automático tras 10s
    if (puertaAbierta && (millis() - tiempoUltimaDeteccion >= tiempoCierre)) {
      cerrarPuertaSuave();
      puertaAbierta = false;
      Serial.println(">> Puerta cerrada por timeout");
    }

  } else {
    if (puertaAbierta) {
      cerrarPuertaSuave();
      puertaAbierta = false;
    }
  }

  // --- PANTALLA ---
  lcd.clear();

  lcd.setCursor(0,0);
  lcd.print("T:");
  lcd.print(t,1);
  lcd.print(" H:");
  lcd.print(h,0);

  lcd.setCursor(0,1);
  if (esNoche) lcd.print("NOCHE ");
  else lcd.print("DIA   ");

  lcd.setCursor(8,1);
  if (puertaAbierta) lcd.print("P:OPEN ");
  else lcd.print("P:CLOSE");

  delay(250);
}
