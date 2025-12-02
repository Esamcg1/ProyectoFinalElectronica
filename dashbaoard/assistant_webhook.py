from flask import Flask, request, jsonify
from dashboard_render import leer_serial

app = Flask(__name__)

#  Obtiene las ultimas lecturas
estado = {
    "temperatura": None,
    "humedad": None,
    "puerta": None,
    "dia_noche": None
}

@app.route("/assistant", methods=["POST"])
def assistant():
    data = request.json
    comando = data.get("command", "").lower()

    # ===== RESPUESTAS =====
    if "temperatura" in comando:
        if estado["temperatura"] is not None:
            return jsonify({"response": f"La temperatura actual es {estado['temperatura']} grados"})
        return jsonify({"response": "No tengo la temperatura en este momento"})

    if "humedad" in comando:
        if estado["humedad"] is not None:
            return jsonify({"response": f"La humedad es {estado['humedad']} por ciento"})
        return jsonify({"response": "No tengo la humedad en este momento"})

    if "puerta" in comando:
        if estado["puerta"] is not None:
            return jsonify({"response": f"La puerta está {estado['puerta']}"})
        return jsonify({"response": "No tengo información de la puerta ahora mismo"})

    if "día" in comando or "noche" in comando:
        if estado["dia_noche"] is not None:
            return jsonify({"response": f"Actualmente es {estado['dia_noche']}"})
        return jsonify({"response": "No tengo información de luz ambiental"})

    return jsonify({"response": "No entendí el comando"})

if __name__ == "__main__":
    app.run(port=5005)