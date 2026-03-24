
const API_URL = 'http://localhost:3000/api/register';

const form          = document.getElementById('registerForm');
const mensajeDiv    = document.getElementById('mensaje');
const btnSubmit     = document.getElementById('btnSubmit');
const btnText       = btnSubmit.querySelector('.btn-text');
const btnLoader     = btnSubmit.querySelector('.btn-loader');


function mostrarMensaje(texto, tipo) {
  mensajeDiv.textContent = texto;
  mensajeDiv.className   = `mensaje ${tipo}`;  
  mensajeDiv.hidden      = false;
}

function ocultarMensaje() {
  mensajeDiv.hidden    = true;
  mensajeDiv.className = 'mensaje';
}

function setLoading(cargando) {
  btnSubmit.disabled = cargando;
  btnText.hidden     = cargando;
  btnLoader.hidden   = !cargando;
}

form.addEventListener('submit', async function (evento) {
  evento.preventDefault();
  ocultarMensaje();

  const nombre          = document.getElementById('nombre').value.trim();
  const email           = document.getElementById('email').value.trim();
  const password        = document.getElementById('password').value;
  const confirmPassword = document.getElementById('confirmPassword').value;

  if (!nombre || !email || !password || !confirmPassword) {
    mostrarMensaje('⚠️ Por favor completa todos los campos.', 'error');
    return;
  }

  if (password !== confirmPassword) {
    mostrarMensaje('❌ Las contraseñas no coinciden. Verifica e intenta de nuevo.', 'error');
    return;
  }

  if (password.length < 6) {
    mostrarMensaje('❌ La contraseña debe tener al menos 6 caracteres.', 'error');
    return;
  }

  setLoading(true);  

  try {
    const respuesta = await fetch(API_URL, {
      method : 'POST',
      headers: { 'Content-Type': 'application/json' },
      body   : JSON.stringify({ nombre, email, password }),
    });

    const datos = await respuesta.json();

    if (respuesta.ok && datos.success) {
      mostrarMensaje(
        '🎉 ¡Registro exitoso! Bienvenido/a a DomiExpress.',
        'exito'
      );
      form.reset(); 
    } else {
      mostrarMensaje(`❌ ${datos.message || 'No se pudo completar el registro.'}`, 'error');
    }

  } catch (error) {
    console.error('Error al conectar con el servidor:', error);
    mostrarMensaje(
      '❌ No se pudo conectar con el servidor. Verifica que el backend esté corriendo.',
      'error'
    );
  } finally {
    setLoading(false);
  }
});
