import serial
import time
import random
from constants import constantes

USE_SIMULATION = True   # Modo similarioc
ser = None

def conectar_arduino():
    """Conecta al puerto real"""
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
    """Lee datos reales o simula valores"""

    global ser

    # Si es simulacion
    if USE_SIMULATION:
        time.sleep(0.5)

        temp = round(random.uniform(20, 30), 1)
        hum = round(random.uniform(40, 80), 1)
        ldr = random.randint(0, 1023)
        puerta = random.choice(["Abriendo puerta", "Cerrando puerta"])
        dia_noche = "DIA" if ldr > 400 else "NOCHE"

        simulated = f"T:{temp} H:{hum} {dia_noche} {puerta}"
        return simulated

    # Usar el arduino serial 
    if ser is None:
        conectar_arduino()

    try:
        line = ser.readline().decode(errors="ignore").strip()
        return line
    except:
        return ""