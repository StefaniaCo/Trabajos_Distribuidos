from flask import Flask, jsonify, request
import psycopg2
import os
import time

# Microservicio encargado de gestionar los tipos de servicios bancarios.
# Tiene su propia base de datos PostgreSQL (db-servicios)

app = Flask(__name__)

def get_connection():
    # Lee las credenciales desde variables de entorno

    return psycopg2.connect(
        host=os.getenv("DB_HOST_SERVICIOS"),
        database="servicios_db",
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

def crear_tabla():
    # Se ejecuta automáticamente al arrancar el servicio
    # Crear la tabla si no existe
    # Intenta conectarse hasta 5 veces porque PostgreSQL puede tardar en estar listo.

    intentos = 0
    while intentos < 5:
        try:
            conn = get_connection()
            cur  = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS servicios (
                    id          SERIAL PRIMARY KEY,
                    nombre      VARCHAR(100),
                    descripcion TEXT
                )
            """)
            conn.commit()
            conn.close()
            print("Tabla servicios lista", flush=True)
            return
        except:
            intentos += 1
            print(f"DB no lista, reintento {intentos}...", flush=True)
            time.sleep(3)

crear_tabla()

@app.route("/servicios", methods=["GET"])
# Devuelve todos los tipos de servicios bancarios registrados
def get_servicios():
    print("[SERVICIOS] Consultando servicios bancarios", flush=True)
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT id, nombre, descripcion FROM servicios")
    filas = cur.fetchall()
    conn.close()
    servicios = [{"id": f[0], "nombre": f[1], "descripcion": f[2]} for f in filas]
    print(f"[SERVICIOS] {len(servicios)} servicios encontrados", flush=True)
    return jsonify(servicios)


@app.route("/servicios", methods=["POST"])
# Registra un nuevo tipo de servicio bancario
def crear_servicio():
    data = request.json
    print(f"[SERVICIOS] Registrando servicio: {data['nombre']}", flush=True)
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(
        "INSERT INTO servicios (nombre, descripcion) VALUES (%s, %s) RETURNING id",
        (data["nombre"], data["descripcion"])
    )
    nuevo_id = cur.fetchone()[0]
    conn.commit()
    conn.close()
    print(f"[SERVICIOS] Servicio creado con id: {nuevo_id}", flush=True)
    return jsonify({"mensaje": "Servicio registrado", "id": nuevo_id,
                    "nombre": data["nombre"], "descripcion": data["descripcion"]})


@app.route("/health")
def health():
    return {"status": "ok", "service": "servicios-service"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)