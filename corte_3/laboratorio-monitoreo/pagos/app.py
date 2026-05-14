from flask import Flask, jsonify
import time

app = Flask(__name__)

lista_pagos = [
    {
        "id": 1,
        "cliente": "Daniel Castro",
        "metodo": "Nequi",
        "estado": "Aprobado"
    },
    {
        "id": 2,
        "cliente": "Sara Medina",
        "metodo": "Tarjeta Débito",
        "estado": "Rechazado"
    }
]


@app.route("/")
def home():
    return "Servicio pagos activo"


@app.route("/pagos")
def pagos():
    tiempo_inicio = time.time()
    print("[PAGOS] Procesando solicitudes de pago", flush=True)
    time.sleep(3)

    duracion = time.time() - tiempo_inicio

    print(f"[PAGOS] Tiempo total procesamiento: {duracion:.2f}",flush=True)

    return jsonify({"transacciones": lista_pagos,"cantidad": len(lista_pagos)})


@app.route("/health")
def health():

    return jsonify({
        "estado": "funcionando",
        "servicio": "pagos"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)