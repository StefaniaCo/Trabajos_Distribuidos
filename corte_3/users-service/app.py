from flask import Flask, jsonify, request
import psycopg2
import os
import time

# Microservicio encargado solo de la gestión de usuarios.
# Tiene su propia base de datos PostgreSQL (db-users)

app = Flask(__name__)

def get_connection():
    # Lee las credenciales desde variables de entorno

    return psycopg2.connect(
        host=os.getenv("DB_HOST_USERS"),
        database="users_db",
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
                CREATE TABLE IF NOT EXISTS usuarios (
                    id SERIAL PRIMARY KEY,
                    nombre VARCHAR(100),
                    email  VARCHAR(100)
                )
            """)
            conn.commit()
            conn.close()
            print("Tabla usuarios lista", flush=True)
            return
        except:
            intentos += 1
            print(f"DB no lista, reintento {intentos}...", flush=True)
            time.sleep(3)

crear_tabla()


@app.route("/users", methods=["GET"])
def get_users():
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT id, nombre, email FROM usuarios")
    filas = cur.fetchall()
    conn.close()
    usuarios = [{"id": f[0], "nombre": f[1], "email": f[2]} for f in filas]
    return jsonify(usuarios)


@app.route("/users", methods=["POST"])
def crear_user():
    data = request.json
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(
        "INSERT INTO usuarios (nombre, email) VALUES (%s, %s) RETURNING id",
        (data["nombre"], data["email"])
    )
    nuevo_id = cur.fetchone()[0]
    conn.commit()
    conn.close()
    return jsonify({"mensaje": "Usuario creado", "id": nuevo_id})


@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT id, nombre, email FROM usuarios WHERE id = %s", (user_id,))
    fila = cur.fetchone()
    conn.close()
    if not fila:
        return jsonify({"error": "Usuario no encontrado"}), 404
    return jsonify({"id": fila[0], "nombre": fila[1], "email": fila[2]})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)