import serial
import threading
import time
from collections import deque

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ---------------- CONFIGURACIÓN ARDUINO ----------------
PORT = 'COM4'
BAUD = 9600

arduino = None
lock = threading.Lock()

# Datos actuales de sensores
current_data = {
    "TEMP": "--",
    "HUM": "--",
    "LDR": "--",
    "DAYNIGHT": "--",
    "DOOR": "--"
}

# ---------------- FUNCIONES ARDUINO ----------------
def conectar_arduino():
    global arduino
    try:
        arduino = serial.Serial(PORT, BAUD, timeout=1)
        print(f"Conectado al Arduino en {PORT}")
    except Exception as e:
        print(f"No se pudo conectar al Arduino: {e}")
        arduino = None

def leer_linea():
    """Lee línea de Arduino y actualiza current_data"""
    if not arduino:
        return
    try:
        line = arduino.readline().decode().strip()
        if line == "---":  # fin de paquete
            return
        if ":" in line:
            key, val = line.split(":", 1)
            with lock:
                current_data[key.strip().upper()] = val.strip()
    except Exception as e:
        print(f"Error leyendo Arduino: {e}")

def hilo_arduino():
    while True:
        if arduino:
            leer_linea()
        time.sleep(0.1)

# ---------------- COMANDOS TELEGRAM ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hola! Soy tu bot de casa inteligente.\n"
        "Usa /temp, /hum, /door, /daynight para consultar los sensores."
    )

async def temp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with lock:
        valor = current_data.get("TEMP", "--")
    await update.message.reply_text(f"Temperatura actual: {valor} °C")

async def hum(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with lock:
        valor = current_data.get("HUM", "--")
    await update.message.reply_text(f"Humedad actual: {valor} %")

async def door(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with lock:
        valor = current_data.get("DOOR", "--")
    await update.message.reply_text(f"Puerta: {valor}")

async def daynight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with lock:
        valor = current_data.get("DAYNIGHT", "--")
    await update.message.reply_text(f"Es de día o noche: {valor}")

# ---------------- MAIN ----------------
def main():
    conectar_arduino()
    # Iniciar hilo de lectura Arduino
    t = threading.Thread(target=hilo_arduino, daemon=True)
    t.start()

    TOKEN = "8316622488:AAFOXwf7gxPKu0dpBMt8JDWr74i4YwTMkYY"
    app = ApplicationBuilder().token(TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("temp", temp))
    app.add_handler(CommandHandler("hum", hum))
    app.add_handler(CommandHandler("door", door))
    app.add_handler(CommandHandler("daynight", daynight))

    # Ejecutar bot
    print("Bot de Telegram listo...")
    app.run_polling()

if __name__ == "__main__":
    main()