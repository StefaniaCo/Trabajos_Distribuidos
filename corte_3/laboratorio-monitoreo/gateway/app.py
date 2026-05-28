from flask import Flask, jsonify
import requests
import time

app = Flask(__name__)

contador_fallos = 0
peticiones_pagos = 0


@app.route("/")
def inicio():
    return "Gateway operativo"


@app.route("/pedidos")
def obtener_pedidos():
    tiempo_inicio = time.time()
    print("[GATEWAY] Solicitando información de pedidos", flush=True)
    try:
        respuesta = requests.get("http://pedidos:5000/pedidos",timeout=4)
        tiempo_total = time.time() - tiempo_inicio

        print(f"[PEDIDOS] Respuesta recibida en {tiempo_total:.2f} segundos",flush=True)

        return jsonify({"servicio": "pedidos","datos": respuesta.json()})
    
    except requests.exceptions.RequestException:
        print("[ERROR] No fue posible conectar con pedidos", flush=True)

        return jsonify({"mensaje": "Servicio pedidos fuera de línea"}), 503


@app.route("/inventario")
def obtener_inventario():
    tiempo_inicio = time.time()
    print("[GATEWAY] Consultando inventario disponible", flush=True)

    try:
        respuesta = requests.get("http://inventario:5000/inventario",timeout=4)
        duracion = time.time() - tiempo_inicio
        print(f"[INVENTARIO] Tiempo de consulta: {duracion:.2f} segundos",flush=True)

        return jsonify({"inventario": respuesta.json()})
    
    except requests.exceptions.RequestException:
        print("[ERROR] Fallo en conexión con inventario", flush=True)

        return jsonify({"error": "Inventario no disponible"}), 503


@app.route("/pagos")
def obtener_pagos():
    global contador_fallos
    global peticiones_pagos

    tiempo_inicio = time.time()

    print("[GATEWAY] Iniciando consulta al servicio pagos", flush=True)

    try:

        respuesta = requests.get("http://pagos:5000/pagos",timeout=4)
        peticiones_pagos += 1
        tiempo_total = time.time() - tiempo_inicio

        print(f"[PAGOS] Tiempo de respuesta: {tiempo_total:.2f} segundos",flush=True)

        if respuesta.status_code != 200:
            contador_fallos += 1

        return jsonify({"resultado": respuesta.json(),"errores": contador_fallos,"consultas": peticiones_pagos}), respuesta.status_code

    except requests.exceptions.RequestException:

        contador_fallos += 1
        print(f"[ERROR] Servicio pagos caído. Total errores: {contador_fallos}",flush=True)

        return jsonify({"mensaje": "No se pudo acceder al servicio de pagos","errores_detectados": contador_fallos}), 503


@app.route("/monitor")
def monitor_general():

    servicios = {
        "pedidos": "http://pedidos:5000/health",
        "inventario": "http://inventario:5000/health",
        "pagos": "http://pagos:5000/health"
    }

    estado_servicios = {}
    for nombre, url in servicios.items():
        try:
            respuesta = requests.get(url, timeout=2)
            estado_servicios[nombre] = respuesta.json()
        except:
            estado_servicios[nombre] = {"estado": "sin conexión"}

    return jsonify(estado_servicios)


@app.route("/metricas")
def metricas():

    return jsonify({
        "errores_pagos": contador_fallos,
        "consultas_pagos": peticiones_pagos
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)