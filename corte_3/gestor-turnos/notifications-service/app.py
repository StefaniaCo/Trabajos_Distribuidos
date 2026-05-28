from flask import Flask, jsonify, request
import psycopg2
import os
import time

# Microservicio encargado de guardar el historial de notificaciones
# Es llamado por turns-service cada vez que se crea un turno exitosamente
# Tiene su propia base de datos PostgreSQL (db-notifications)

app = Flask(__name__)

def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST_NOTIFICATIONS"),
        database="notifications_db",
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
                CREATE TABLE IF NOT EXISTS notificaciones (
                    id      SERIAL PRIMARY KEY,
                    user_id INTEGER,
                    turno   VARCHAR(10),
                    mensaje TEXT
                )
            """)
            conn.commit()
            conn.close()
            print("Tabla notificaciones lista", flush=True)
            return
        except:
            intentos += 1
            print(f"DB no lista, reintento {intentos}...", flush=True)
            time.sleep(3)

crear_tabla()


@app.route("/notify", methods=["POST"])
# Recibe la notificación de turns-service y la guarda
def notify():
    data = request.json
    print(f"[NOTIFICATIONS] Registrando notificación para user_id: {data['user_id']} turno: {data['turno']}", flush=True)
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(
        "INSERT INTO notificaciones (user_id, turno, mensaje) VALUES (%s, %s, %s)",
        (data["user_id"], data["turno"], data["mensaje"])
    )
    conn.commit()
    conn.close()
    print("[NOTIFICATIONS] Notificación guardada", flush=True)
    return jsonify({"mensaje": "Notificación registrada"})


@app.route("/notifications", methods=["GET"])
# Devuelve el historial completo de notificaciones

def get_notifications():
    print("[NOTIFICATIONS] Consultando historial de notificaciones", flush=True)
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT id, user_id, turno, mensaje FROM notificaciones")
    filas = cur.fetchall()
    conn.close()
    notifs = [{"id": f[0], "user_id": f[1], "turno": f[2], "mensaje": f[3]} for f in filas]
    return jsonify(notifs)

@app.route("/health")
def health():
    return {"status": "ok", "service": "notifications-service"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)