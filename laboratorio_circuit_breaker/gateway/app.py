from flask import Flask, jsonify
import requests
import time

app = Flask(__name__)

Limite_fallos   = 3
Espera_segundos = 10

# Estado de cada circuito (ahora incluye "desde" para el half-open)
circuitos = {
    "backend":  {"fallos": 0, "abierto": False, "desde": None},
    "usuarios": {"fallos": 0, "abierto": False, "desde": None},
}

def verificar_circuito(nombre):
    c = circuitos[nombre]
    if not c["abierto"]:
        return True
    # Han pasado los segundos de espera? → entrar en half-open
    if time.time() - c["desde"] >= Espera_segundos:
        print(f"HALF-OPEN {nombre}: probando si el servicio volvió...", flush=True)
        return True
    # Todavía no ha pasado el tiempo → seguir bloqueado
    return False

def registrar_exito(nombre):
    c = circuitos[nombre]
    c["fallos"]  = 0
    c["abierto"] = False
    c["desde"]   = None
    print(f"Circuito {nombre} CERRADO (recuperado)", flush=True)

def registrar_fallo(nombre):
    c = circuitos[nombre]
    c["fallos"] += 1
    print(f"Fallo {nombre} #{c['fallos']}", flush=True)
    if c["fallos"] >= Limite_fallos:
        c["abierto"] = True
        c["desde"]   = time.time()
        print(f"Circuito {nombre} ABIERTO. Reintento en {Espera_segundos}s", flush=True)


@app.route("/mascotas")
def mascotas():
    if not verificar_circuito("backend"):
        return jsonify({"error": "Servicio mascotas bloqueado"}), 503
    try:
        r = requests.get("http://backend:5000/mascotas", timeout=2)
        registrar_exito("backend")
        return jsonify(r.json())
    except:
        registrar_fallo("backend")
        return jsonify({"error": "Servicio mascotas no disponible"}), 503


@app.route("/usuarios")
def usuarios():
    if not verificar_circuito("usuarios"):
        return jsonify({"error": "Servicio usuarios bloqueado"}), 503
    try:
        r = requests.get("http://usuarios:5000/usuarios", timeout=2)
        registrar_exito("usuarios")
        return jsonify(r.json())
    except:
        registrar_fallo("usuarios")
        return jsonify({"error": "Servicio usuarios no disponible"}), 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
