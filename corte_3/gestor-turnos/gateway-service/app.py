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
    "notifications": {"fallos": 0, "abierto": False, "desde": None},
    
}

peticiones = {"users": 0, 
              "turns": 0, 
              "notifications": 0}

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
    if c["abierto"]:
        print(f"Circuito {nombre} CERRADO (recuperado)", flush=True)
    c["fallos"]  = 0
    c["abierto"] = False
    c["desde"]   = None

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
    inicio = time.time()
    if not verificar_circuito("users"):
        return jsonify({"error": "Servicio usuarios bloqueado"}), 503
    try:
        r = requests.get("http://users-service:5000/users", timeout=2)
        registrar_exito("users")
        peticiones["users"] += 1
        fin = time.time()
        print(f"[INFO] Tiempo de respuesta users: {fin - inicio}", flush=True)
        return jsonify(r.json())
    except:
        registrar_fallo("users")
        peticiones["users"] += 1
        return jsonify({"error": "Servicio usuarios no disponible"}), 503


@app.route("/users", methods=["POST"])
def crear_user():
    inicio = time.time()
    if not verificar_circuito("users"):
        return jsonify({"error": "Servicio usuarios bloqueado"}), 503
    try:
        r = requests.post("http://users-service:5000/users", json=request.json, timeout=2)
        registrar_exito("users")
        peticiones["users"] += 1
        fin = time.time()
        print(f"[INFO] Tiempo de respuesta users POST: {fin - inicio}", flush=True)
        return jsonify(r.json())
    except:
        registrar_fallo("users")
        peticiones["users"] += 1
        return jsonify({"error": "Servicio usuarios no disponible"}), 503


# Endpoints de turnos

@app.route("/turn", methods=["POST"])
def crear_turno():
    inicio = time.time()
    if not verificar_circuito("turns"):
        return jsonify({"error": "Servicio turnos bloqueado"}), 503
    try:
        r = requests.post("http://turns-service:5000/turn", json=request.json, timeout=2)
        registrar_exito("turns")
        peticiones["turns"] += 1
        fin = time.time()
        print(f"[INFO] Tiempo de respuesta turns POST: {fin - inicio}", flush=True)
        return jsonify(r.json())
    except:
        registrar_fallo("turns")
        peticiones["turns"] += 1
        return jsonify({"error": "Servicio turnos no disponible"}), 503


@app.route("/turns", methods=["GET"])
def get_turns():
    inicio = time.time()
    if not verificar_circuito("turns"):
        return jsonify({"error": "Servicio turnos bloqueado"}), 503
    try:
        r = requests.get("http://turns-service:5000/turns", timeout=2)
        registrar_exito("turns")
        peticiones["turns"] += 1
        fin = time.time()
        print(f"[INFO] Tiempo de respuesta turns GET: {fin - inicio}", flush=True)
        return jsonify(r.json())
    except:
        registrar_fallo("turns")
        peticiones["turns"] += 1
        return jsonify({"error": "Servicio turnos no disponible"}), 503


@app.route("/notifications", methods=["GET"])
def get_notifications():
    inicio = time.time()
    if not verificar_circuito("notifications"):
        return jsonify({"error": "Servicio notificaciones bloqueado"}), 503
    try:
        r = requests.get("http://notifications-service:5000/notifications", timeout=2)
        registrar_exito("notifications")
        peticiones["notifications"] += 1
        fin = time.time()
        print(f"[INFO] Tiempo de respuesta notifications GET: {fin - inicio}", flush=True)
        return jsonify(r.json())
    except:
        registrar_fallo("notifications")
        peticiones["notifications"] += 1
        return jsonify({"error": "Servicio notificaciones no disponible"}), 503
    

@app.route("/notify", methods=["POST"])
def crear_notification():
    inicio = time.time()
    if not verificar_circuito("notifications"):
        return jsonify({"error": "Servicio notificaciones bloqueado"}), 503
    try:
        r = requests.post("http://notifications-service:5000/notify", json=request.json, timeout=2)
        registrar_exito("notifications")
        peticiones["notifications"] += 1
        fin = time.time()
        print(f"[INFO] Tiempo de respuesta notifications POST: {fin - inicio}", flush=True)
        return jsonify(r.json())
    except:
        registrar_fallo("notifications")
        peticiones["notifications"] += 1
        return jsonify({"error": "Servicio notificaciones no disponible"}), 503

# Resumen

@app.route("/resumen", methods=["GET"])
def resumen():
    if not verificar_circuito("users"):
        resultado_users = {"error": "circuito users abierto"}
    else:
        try:
            r = requests.get("http://users-service:5000/users", timeout=2)
            registrar_exito("users")
            peticiones["users"] += 1
            resultado_users = r.json()
        except:
            registrar_fallo("users")
            peticiones["users"] +=1
            resultado_users = {"error": "users no disponible"}

    if not verificar_circuito("turns"):
        resultado_turns = {"error": "circuito turns abierto"}
    else:
        try:
            r = requests.get("http://turns-service:5000/turns", timeout=2)
            registrar_exito("turns")
            peticiones["turns"] +=1
            resultado_turns = r.json()
        except:
            registrar_fallo("turns")
            peticiones["turns"] += 1
            resultado_turns = {"error": "turns no disponible"}

    if not verificar_circuito("notifications"):
        resultado_notifications = {"error": "circuito notifications abierto"}
    else:
        try:
            r = requests.get("http://notifications-service:5000/notifications", timeout=2)
            registrar_exito("notifications")
            peticiones["notifications"] += 1
            resultado_notifications = r.json()
        except:
            registrar_fallo("notifications")
            peticiones["notifications"] +=1
            resultado_notifications = {"error": "notifications no disponible"}

    return jsonify({
        "usuarios": resultado_users,
        "turnos":   resultado_turns,
        "notificaciones": resultado_notifications
    })

@app.route("/estado/users")
def estado_users():
    try:
        response = requests.get("http://users-service:5000/health", timeout=3)
        return jsonify(response.json())
    except:
        return jsonify({"status": "down"}), 503

@app.route("/estado/turns")
def estado_turns():
    try:
        response = requests.get("http://turns-service:5000/health", timeout=3)
        return jsonify(response.json())
    except:
        return jsonify({"status": "down"}), 503

@app.route("/estado/notifications")
def estado_notifications():
    try:
        response = requests.get("http://notifications-service:5000/health", timeout=3)
        return jsonify(response.json())
    except:
        return jsonify({"status": "down"}), 503


@app.route("/monitor")
def monitor():
    servicios = {
        "users-service":         "http://users-service:5000/health",
        "turns-service":         "http://turns-service:5000/health",
        "notifications-service": "http://notifications-service:5000/health",
    }
    resultado = {}
    for nombre, url in servicios.items():
        inicio = time.time()
        try:
            r = requests.get(url, timeout=2)
            latencia = time.time() - inicio
            resultado[nombre] = {
                "estado":   r.json().get("status", "ok"),
                "latencia": latencia,
            }
        except:
            latencia = time.time() - inicio
            resultado[nombre] = {
                "estado":   "sin conexión",
                "latencia": latencia,
            }

    return jsonify({
        "servicios": resultado,
        "fallos": {
            "users":         circuitos["users"]["fallos"],
            "turns":         circuitos["turns"]["fallos"],
            "notifications": circuitos["notifications"]["fallos"],
        },
        "peticiones": peticiones
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)