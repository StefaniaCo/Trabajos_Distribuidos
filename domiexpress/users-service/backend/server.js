const express = require('express');
const mysql   = require('mysql2');
const cors    = require('cors');

const app  = express();
const PORT = 3000;

// Middlewares
app.use(cors());
app.use(express.json());

// Config de la bd
const dbConfig = {
  host    : process.env.DB_HOST     || 'localhost',
  user    : process.env.DB_USER     || 'domiuser',
  password: process.env.DB_PASSWORD || 'domipass123',
  database: process.env.DB_NAME     || 'domiexpress',
};

// Conexión con reintentos 
let connection;

function conectarDB() {
  console.log('⏳ Intentando conectar a la base de datos...');

  connection = mysql.createConnection(dbConfig);

  connection.connect((err) => {
    if (err) {
      console.error('❌ No se pudo conectar. Reintentando en 5 segundos...', err.message);
      setTimeout(conectarDB, 5000);
      return;
    }

    console.log('✅ Conectado a MySQL correctamente');
    crearTabla();
  });


  connection.on('error', (err) => {
    console.warn('⚠️  Error de conexión MySQL:', err.code, '— Reconectando en 5s...');
    setTimeout(conectarDB, 5000);
  });
}

function crearTabla() {
  const sql = `
    CREATE TABLE IF NOT EXISTS usuarios (
      id              INT AUTO_INCREMENT PRIMARY KEY,
      nombre          VARCHAR(100)  NOT NULL,
      email           VARCHAR(150)  NOT NULL UNIQUE,
      password        VARCHAR(255)  NOT NULL,
      fecha_registro  TIMESTAMP     DEFAULT CURRENT_TIMESTAMP
    )
  `;

  connection.query(sql, (err) => {
    if (err) {
      console.error('❌ Error al crear la tabla:', err.message);
    } else {
      console.log('📋 Tabla "usuarios" lista');
    }
  });
}

app.post('/api/register', (req, res) => {
  const { nombre, email, password } = req.body;

  if (!nombre || !email || !password) {
    return res.status(400).json({
      success: false,
      message: 'Todos los campos son obligatorios',
    });
  }

  const sql = 'INSERT INTO usuarios (nombre, email, password) VALUES (?, ?, ?)';

  connection.query(sql, [nombre, email, password], (err, result) => {
    if (err) {
      if (err.errno === 1062) {
        return res.status(409).json({
          success: false,
          message: 'Ya existe una cuenta con ese correo electrónico',
        });
      }

      console.error('❌ Error al registrar usuario:', err.message);
      return res.status(500).json({
        success: false,
        message: 'Error interno del servidor',
      });
    }

    console.log('👤 Nuevo usuario registrado: ' + email + ' (ID: ' + result.insertId + ')');
    res.status(201).json({
      success: true,
      message: '¡Usuario registrado exitosamente!',
      userId: result.insertId,
    });
  });
});

app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'users-backend' });
});

// Arrancar el servidor
app.listen(PORT, () => {
  console.log('🚀 Servidor corriendo en http://localhost:' + PORT);
  conectarDB();
});
