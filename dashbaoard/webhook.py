from flask import Flask, request, jsonify
import serial
import time

app = Flask(_name_)

# Puerto del Arduino
ARDUINO_PORT = "COM4"
BAUD = 9600

ser = serial.Serial(ARDUINO_PORT, BAUD, timeout=1)
time.sleep(2)

@app.route("/assistant", methods=["POST"])
def assistant():
    data = request.json
    intent = data.get("intent")

    print("Intent recibido:", intent)

    if intent == "get_temperature":
        ser.write(b"READ_TEMP\n")
        time.sleep(1)
        temp = ser.readline().decode().strip()
        return jsonify(reply=f"La temperatura es {temp} grados")

    elif intent == "get_door_state":
        ser.write(b"READ_DOOR\n")
        time.sleep(1)
        door = ser.readline().decode().strip()
        return jsonify(reply=f"La puerta está {door}")

    return jsonify(reply="No entendí el comando")

if _name_ == "_main_":
    app.run(port=5005)