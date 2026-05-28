from flask import Flask, jsonify
import time

app = Flask(__name__)

lista_pedidos = [
    {
        "id": 1,
        "cliente": "Ana López",
        "producto": "Mouse Inalámbrico",
        "cantidad": 3
    },
    {
        "id": 2,
        "cliente": "Kevin Muñoz",
        "producto": "Teclado Mecánico",
        "cantidad": 1
    }
]


@app.route("/")
def home():
    return "Microservicio pedidos activo"


@app.route("/pedidos")
def pedidos():
    tiempo_inicio = time.time()
    print("[PEDIDOS] Generando listado de pedidos", flush=True)
    time.sleep(1)
    
    duracion = time.time() - tiempo_inicio

    print(f"[PEDIDOS] Consulta completada en {duracion:.2f} segundos",flush=True)

    return jsonify({"total_pedidos": len(lista_pedidos),"pedidos": lista_pedidos})


@app.route("/health")
def health():

    return jsonify({
        "estado": "activo",
        "microservicio": "pedidos"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)