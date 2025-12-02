import serial
import threading
import time
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext

# ================= CONFIGURACIÓN =================
TOKEN = "8316622488:AAFOXwf7gxPKu0dpBMt8JDWr74i4YwTMkYY"
COM_PORT = "COM4"   # arduino
BAUD = 115200

# Variables de estado
estado_actual = {
    "TEMP": "--",
    "HUM": "--",
    "LDR": "--",
    "DAYNIGHT": "--",
    "DOOR": "--"
}

# ================= SERIAL =================
try:
    arduino = serial.Serial(COM_PORT, BAUD, timeout=1)
    time.sleep(2)  # Esperar a que Arduino se inicie
except Exception as e:
    print("No se pudo conectar al Arduino:", e)
    arduino = None

def leer_serial():
    global estado_actual
    if not arduino:
        return
    while True:
        try:
            line = arduino.readline().decode().strip()
            if not line:
                continue
            if line == "---":
                continue
            if ":" in line:
                key, val = line.split(":", 1)
                estado_actual[key.upper()] = val.strip()
        except Exception as e:
            print("Error lectura serial:", e)
        time.sleep(0.05)

# ================= TELEGRAM =================
def estado(update: Update, context: CallbackContext):
    msg = (
        f" Temperatura: {estado_actual['TEMP']} °C\n"
        f" Humedad: {estado_actual['HUM']} %\n"
        f" Luz: {estado_actual['LDR']}\n"
        f" Día/Noche: {estado_actual['DAYNIGHT']}\n"
        f" Puerta: {estado_actual['DOOR']}"
    )
    update.message.reply_text(msg)

def abrir(update: Update, context: CallbackContext):
    if arduino:
        arduino.write(b'ABRIR\n')
        update.message.reply_text("Comando: Abrir puerta enviado")
    else:
        update.message.reply_text("Arduino no conectado")

def cerrar(update: Update, context: CallbackContext):
    if arduino:
        arduino.write(b'CERRAR\n')
        update.message.reply_text("omando: Cerrar puerta enviado")
    else:
        update.message.reply_text(" Arduino no conectado")

def puerta(update: Update, context: CallbackContext):
    update.message.reply_text(f" Puerta: {estado_actual['DOOR']}")

# ================= MAIN =================
def main():
    # Hilo de lectura Serial
    hilo = threading.Thread(target=leer_serial, daemon=True)
    hilo.start()

    # Bot Telegram
    updater = Updater(TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("estado", estado))
    dp.add_handler(CommandHandler("abrir", abrir))
    dp.add_handler(CommandHandler("cerrar", cerrar))
    dp.add_handler(CommandHandler("puerta", puerta))

    print("Bot Telegram corriendo...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()