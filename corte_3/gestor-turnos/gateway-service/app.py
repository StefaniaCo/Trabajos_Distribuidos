from flask import Flask, jsonify, request
import requests
import time

# Punto de entrada único del sistema. El cliente nunca habla directo con los servicios,
# todo pasa por aquí

app = Flask(__name__)

LIMITE_FALLOS   = 3  # Límite de fallos antes de abrir el circuito
ESPERA_SEGUNDOS = 10  # Tiempo que espera antes de intentar reconectarse (half-open)

# Circuit breaker independiente por servicio
circuitos = {
    "users": {"fallos": 0, "abierto": False, "desde": None},
    "turns": {"fallos": 0, "abierto": False, "desde": None},
}

def verificar_circuito(nombre):
    c = circuitos[nombre]

    # Si el circuito está cerrado, deja pasar la petición normal
    if not c["abierto"]:
        return True
    
    # Si está abierto pero ya pasaron 10 segundos, entra en half-open
    # y deja pasar una petición de prueba para ver si el servicio volvió
    if time.time() - c["desde"] >= ESPERA_SEGUNDOS:
        print(f"HALF-OPEN {nombre}: probando reconexión...", flush=True)
        return True
    
    # Si todavía no pasaron los 10 segundos, bloquea la petición.
    return False

def registrar_exito(nombre):
# La petición funcionó: reinicia el contador y cierra el circuito.  
    c = circuitos[nombre]
    c["fallos"]  = 0
    c["abierto"] = False
    c["desde"]   = None
    print(f"Circuito {nombre} CERRADO (recuperado)", flush=True)

def registrar_fallo(nombre):
    # La petición falló: suma un fallo. Si llega a 3, abre el circuito
    # y guarda el momento exacto en que se abrió (para medir los 10 segundos).
    c = circuitos[nombre]
    c["fallos"] += 1
    print(f"Fallo {nombre} #{c['fallos']}", flush=True)
    if c["fallos"] >= LIMITE_FALLOS:
        c["abierto"] = True
        c["desde"]   = time.time()
        print(f"Circuito {nombre} ABIERTO. Reintento en {ESPERA_SEGUNDOS}s", flush=True)


# Endpoints de usuarios

@app.route("/users", methods=["GET"])
def get_users():
    if not verificar_circuito("users"):
        return jsonify({"error": "Servicio usuarios bloqueado"}), 503
    try:
        r = requests.get("http://users-service:5000/users", timeout=2)
        registrar_exito("users")
        return jsonify(r.json())
    except:
        registrar_fallo("users")
        return jsonify({"error": "Servicio usuarios no disponible"}), 503


@app.route("/users", methods=["POST"])
def crear_user():
    if not verificar_circuito("users"):
        return jsonify({"error": "Servicio usuarios bloqueado"}), 503
    try:
        r = requests.post("http://users-service:5000/users", json=request.json, timeout=2)
        registrar_exito("users")
        return jsonify(r.json())
    except:
        registrar_fallo("users")
        return jsonify({"error": "Servicio usuarios no disponible"}), 503


# Endpoints de turnos

@app.route("/turn", methods=["POST"])
def crear_turno():
    if not verificar_circuito("turns"):
        return jsonify({"error": "Servicio turnos bloqueado"}), 503
    try:
        r = requests.post("http://turns-service:5000/turn", json=request.json, timeout=2)
        registrar_exito("turns")
        return jsonify(r.json())
    except:
        registrar_fallo("turns")
        return jsonify({"error": "Servicio turnos no disponible"}), 503


@app.route("/turns", methods=["GET"])
def get_turns():
    if not verificar_circuito("turns"):
        return jsonify({"error": "Servicio turnos bloqueado"}), 503
    try:
        r = requests.get("http://turns-service:5000/turns", timeout=2)
        registrar_exito("turns")
        return jsonify(r.json())
    except:
        registrar_fallo("turns")
        return jsonify({"error": "Servicio turnos no disponible"}), 503


# Resumen

@app.route("/resumen", methods=["GET"])
def resumen():
    if not verificar_circuito("users"):
        resultado_users = {"error": "circuito users abierto"}
    else:
        try:
            r = requests.get("http://users-service:5000/users", timeout=2)
            registrar_exito("users")
            resultado_users = r.json()
        except:
            registrar_fallo("users")
            resultado_users = {"error": "users no disponible"}

    if not verificar_circuito("turns"):
        resultado_turns = {"error": "circuito turns abierto"}
    else:
        try:
            r = requests.get("http://turns-service:5000/turns", timeout=2)
            registrar_exito("turns")
            resultado_turns = r.json()
        except:
            registrar_fallo("turns")
            resultado_turns = {"error": "turns no disponible"}

    return jsonify({
        "usuarios": resultado_users,
        "turnos":   resultado_turns
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)