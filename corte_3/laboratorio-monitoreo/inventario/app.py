from flask import Flask, jsonify
import time

app = Flask(__name__)

productos = [
    {
        "id": 1,
        "producto": "Laptop Lenovo",
        "stock": 5,
        "disponible": True
    },
    {
        "id": 2,
        "producto": "Monitor LG",
        "stock": 0,
        "disponible": False
    }
]


@app.route("/")
def inicio():
    return "Servicio inventario disponible"


@app.route("/inventario")
def inventario():
    
    inicio_consulta = time.time()
    print("[INVENTARIO] Verificando stock", flush=True)
    time.sleep(1)

    tiempo_total = time.time() - inicio_consulta

    print(f"[INVENTARIO] Tiempo respuesta: {tiempo_total:.2f}",flush=True)

    return jsonify({"cantidad_productos": len(productos),"inventario": productos})


@app.route("/health")
def health():

    return jsonify({
        "estado": "ok",
        "servicio": "inventario"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)