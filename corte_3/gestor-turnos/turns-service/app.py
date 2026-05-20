from flask import Flask, jsonify, request
import psycopg2
import requests
import os
import time

# Microservicio encargado de asignar turnos consecutivos (T1, T2, T3...).
# Se comunica con otros dos servicios: users-service y notifications-service.

app = Flask(__name__)

def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST_TURNS"),
        database="turns_db",
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

def crear_tabla():
    # Crear la tabla si no existe al arrancar el servicio
    intentos = 0
    while intentos < 5:
        try:
            conn = get_connection()
            cur  = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS turnos (
                    id      SERIAL PRIMARY KEY,
                    turno   VARCHAR(10),
                    user_id INTEGER
                )
            """)
            conn.commit()
            conn.close()
            print("Tabla turnos lista", flush=True)
            return
        except:
            intentos += 1
            print(f"DB no lista, reintento {intentos}...", flush=True)
            time.sleep(3)

crear_tabla()


@app.route("/turns", methods=["GET"])
def get_turns():
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT id, turno, user_id FROM turnos")
    filas = cur.fetchall()
    conn.close()
    turnos = [{"id": f[0], "turno": f[1], "user_id": f[2]} for f in filas]
    return jsonify(turnos)


@app.route("/turn", methods=["POST"])
def crear_turno():
    data    = request.json
    user_id = data.get("user_id")

    # Paso 1 (Validar que el usuario existe en users-service con un timeout de 3s) 
    try:
        r = requests.get(f"http://users-service:5000/users/{user_id}", timeout=3)
        print(f"Validando usuario {user_id}, respuesta: {r.status_code}", flush=True)
        if r.status_code == 404:
            return jsonify({"error": "Usuario no encontrado"}), 404
    except:
        return jsonify({"error": "No se pudo validar el usuario"}), 503

    # Paso 2 (Generar turno consecutivo (T1, T2, T3...))
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM turnos")
    total = cur.fetchone()[0]
    turno = f"T{total + 1}"

    cur.execute(
        "INSERT INTO turnos (turno, user_id) VALUES (%s, %s)",
        (turno, user_id)
    )
    conn.commit()
    conn.close()

    # Paso 3 (Notificar al notifications-service)
    try:
        requests.post("http://notifications-service:5000/notify", json={
            "user_id": user_id,
            "turno":   turno,
            "mensaje": f"Tu turno es {turno}"
        }, timeout=2)
    except:
        print("Notificación no enviada, pero el turno fue creado", flush=True)

    return jsonify({"mensaje": "Turno creado", "turno": turno, "user_id": user_id})

@app.route("/health")
def health():
    return {"status": "ok", "service": "turns-service"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)