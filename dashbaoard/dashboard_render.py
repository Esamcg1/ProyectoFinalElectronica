import serial
import time
from constants import constantes

USE_SIMULATION = False
ser = None

def conectar_arduino():
    global ser
    while True:
        try:
            print(f"Conectando Arduino al puerto {constantes.PORT}")
            ser = serial.Serial(constantes.PORT, constantes.BAUD, timeout=1)
            print(">> Arduino conectado.")
            return ser
        except:
            print("No se pudo conectar. Reintentando...")
            time.sleep(1)


def leer_serial():
    """
    Lee una línea del Arduino.
        TEMP:24.5
        HUM:60
        LDR:350
        DAYNIGHT:DAY
        DOOR:OPEN
        MOTION:1
        ---
    """
    global ser

    if USE_SIMULATION:
        # Generar datos falsos
        import random
        time.sleep(0.5)

        temp = round(random.uniform(20,30),1)
        hum = round(random.uniform(40,80),1)
        ldr = random.randint(0,1023)
        day = "DAY" if ldr > 500 else "NIGHT"
        door = random.choice(["OPEN","CLOSED"])

        return [
            f"TEMP:{temp}",
            f"HUM:{hum}",
            f"LDR:{ldr}",
            f"DAYNIGHT:{day}",
            f"DOOR:{door}",
            "MOTION:0",
            "---"
        ]

    # Lectura real
    if ser is None:
        conectar_arduino()

    try:
        line = ser.readline().decode(errors="ignore").strip()
        return line
    except:
        return ""