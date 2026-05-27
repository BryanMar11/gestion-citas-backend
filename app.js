const API_URL = "http://127.0.0.1:8000";

// Variables globales para guardar la información completa y cruzar los nombres
let listaUsuarios = [];
let listaPrestadores = [];
let listaServicios = [];

// Ejecutar apenas cargue la página
document.addEventListener("DOMContentLoaded", async () => {
    // 1. Cargamos los datos de los formularios (Clientes, Barberos, Servicios) y esperamos a que terminen
    await cargarFormularios();
    
    // 2. Una vez tengamos los nombres cargados en la memoria global, listamos las citas en la tabla
    cargarCitas();

    // 3. Escuchar cuando se envíe el formulario para AGENDAR una cita
    document.getElementById("form-cita").addEventListener("submit", agendarCita);
    
    // 4. Escuchar cuando se envíe el formulario para REGISTRAR un nuevo cliente
    document.getElementById("form-usuario").addEventListener("submit", registrarUsuario);
});
// 1. CARGAR SELECTS DINÁMICAMENTE Y GUARDAR EN MEMORIA
async function cargarFormularios() {
    try {
        // Traer Usuarios
        const resUser = await fetch(`${API_URL}/usuarios/`);
        listaUsuarios = await resUser.json();
        const selectUser = document.getElementById("select-usuario");
        selectUser.innerHTML = '<option value="">Seleccione un cliente...</option>';
        listaUsuarios.forEach(u => {
            selectUser.innerHTML += `<option value="${u.id}">${u.nombre}</option>`;
        });

        // Traer Prestadores (Barberos)
        const resPrest = await fetch(`${API_URL}/prestadores/`);
        listaPrestadores = await resPrest.json();
        const selectPrest = document.getElementById("select-prestador");
        selectPrest.innerHTML = '<option value="">Seleccione un barbero...</option>';
        listaPrestadores.forEach(p => {
            selectPrest.innerHTML += `<option value="${p.id}">${p.nombre} (${p.especialidad})</option>`;
        });

        // Traer Servicios (Corte, cejas, etc.)
        const resServ = await fetch(`${API_URL}/servicios/`);
        listaServicios = await resServ.json();
        const selectServ = document.getElementById("select-servicio");
        selectServ.innerHTML = '<option value="">Seleccione un servicio...</option>';
        listaServicios.forEach(s => {
            // Validamos si viene como 'nombre' o 'nombre_servicio' por el mapeo del backend
            const nombreServicio = s.nombre || s.nombre_servicio || 'Servicio';
            selectServ.innerHTML += `<option value="${s.id}">${nombreServicio} - $${s.precio}</option>`;
        });

    } catch (error) {
        console.error("Error cargando los datos iniciales:", error);
    }
}

// 2. OBTENER Y PINTAR LAS CITAS EN LA TABLA (CON NOMBRES REALES)
async function cargarCitas() {
    const tbody = document.getElementById("tabla-citas-body");
    try {
        const res = await fetch(`${API_URL}/citas/`);
        const citas = await res.json();

        if (citas.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="py-4 text-center text-gray-400">No hay citas registradas.</td></tr>`;
            return;
        }

        tbody.innerHTML = ""; // Limpiar tabla
        citas.forEach(cita => {
            // 🔎 BUSQUEDA MÁGICA: Cruzamos el ID de la cita con el nombre de nuestras listas globales
            const usuario = listaUsuarios.find(u => u.id === cita.usuario_id);
            const prestador = listaPrestadores.find(p => p.id === cita.prestador_id);
            const servicio = listaServicios.find(s => s.id === cita.servicio_id);

            // Si por alguna razón no encuentra el registro, ponemos el ID como respaldo
            const nombreCliente = usuario ? usuario.nombre : `Cliente #${cita.usuario_id}`;
            const nombreBarbero = prestador ? prestador.nombre : `Barbero #${cita.prestador_id}`;
            const nombreServicio = servicio ? (servicio.nombre || servicio.nombre_servicio) : `Servicio #${cita.servicio_id}`;

            // Formatear la fecha para quitar la 'T'
            const fechaFormateada = cita.fecha_hora.replace("T", " ");

            tbody.innerHTML += `
                <tr class="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                    <td class="py-3 px-4 font-semibold">${cita.id}</td>
                    <td class="py-3 px-4 font-medium text-gray-900">${nombreCliente}</td>
                    <td class="py-3 px-4 text-gray-600">${nombreBarbero}</td>
                    <td class="py-3 px-4 text-gray-600">
                        <span class="bg-blue-50 text-blue-700 px-2 py-1 rounded text-xs font-semibold">
                            ${nombreServicio}
                        </span>
                    </td>
                    <td class="py-3 px-4 text-blue-600 font-medium">${fechaFormateada}</td>
                    <td class="py-3 px-4 text-center space-x-2">
                        <button onclick="reprogramarCita(${cita.id})" class="text-yellow-600 hover:text-yellow-700 font-medium text-xs bg-yellow-50 px-2.5 py-1 rounded border border-yellow-200">Reprogramar</button>
                        <button onclick="cancelarCita(${cita.id})" class="text-red-600 hover:text-red-700 font-medium text-xs bg-red-50 px-2.5 py-1 rounded border border-red-200">Cancelar</button>
                    </td>
                </tr>
            `;
        });
    } catch (error) {
        tbody.innerHTML = `<tr><td colspan="6" class="py-4 text-center text-red-500">Error al conectar con el servidor backend.</td></tr>`;
    }
}

// 3. CREAR NUEVA CITA (POST)
async function agendarCita(e) {
    e.preventDefault();
    mostrarAlerta(null);

    const datos = {
        usuario_id: parseInt(document.getElementById("select-usuario").value),
        prestador_id: parseInt(document.getElementById("select-prestador").value),
        servicio_id: parseInt(document.getElementById("select-servicio").value),
        fecha_hora: document.getElementById("input-fecha").value
    };

    try {
        const res = await fetch(`${API_URL}/citas/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(datos)
        });

        const resultado = await res.json();

        if (res.ok) {
            mostrarAlerta("¡Cita agendada con éxito!", "verde");
            document.getElementById("form-cita").reset();
            cargarCitas(); // Recargar la lista automáticamente
        } else {
            mostrarAlerta(resultado.detail || "Error al agendar la cita.", "rojo");
        }
    } catch (error) {
        mostrarAlerta("No se pudo conectar con el servidor.", "rojo");
    }
}

// 4. CANCELAR CITA (DELETE)
async function cancelarCita(id) {
    if (!confirm(`¿Estás seguro de que deseas cancelar la cita número ${id}?`)) return;

    try {
        const res = await fetch(`${API_URL}/citas/${id}`, { method: "DELETE" });
        if (res.ok) {
            cargarCitas();
        }
    } catch (error) {
        alert("Error al intentar cancelar la cita.");
    }
}

// 5. REPROGRAMAR CITA (PUT)
async function reprogramarCita(id) {
    const nuevaFecha = prompt("Introduce la nueva fecha y hora (Ej: 2026-05-30 15:30:00):");
    if (!nuevaFecha) return;

    try {
        const res = await fetch(`${API_URL}/citas/${id}?nueva_fecha_hora=${encodeURIComponent(nuevaFecha)}`, {
            method: "PUT"
        });
        const resultado = await res.json();

        if (res.ok) {
            alert("Cita reprogramada con éxito.");
            cargarCitas();
        } else {
            alert(resultado.detail || "Error al reprogramar.");
        }
    } catch (error) {
        alert("Error de conexión al reprogramar.");
    }
}

// Auxiliar para alertas
function mostrarAlerta(mensaje, tipo) {
    const alerta = document.getElementById("alerta");
    if (!mensaje) {
        alerta.classList.add("hidden");
        return;
    }
    alerta.classList.remove("hidden", "bg-green-100", "text-green-800", "bg-red-100", "text-red-800");
    if (tipo === "verde") {
        alerta.classList.add("bg-green-100", "text-green-800");
    } else {
        alerta.classList.add("bg-red-100", "text-red-800");
    }
    alerta.innerText = mensaje;
}

// 6. REGISTRAR NUEVO USUARIO/CLIENTE (POST)
async function registrarUsuario(e) {
    e.preventDefault();
    mostrarAlerta(null); // Limpiar alertas previas

    const datosUsuario = {
        nombre: document.getElementById("reg-nombre").value,
        telefono: document.getElementById("reg-telefono").value || null, // Opcional
        email: document.getElementById("reg-email").value
    };

    try {
        const res = await fetch(`${API_URL}/usuarios/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(datosUsuario)
        });

        const resultado = await res.json();

        if (res.ok) {
            mostrarAlerta(`¡Cliente "${datosUsuario.nombre}" registrado con éxito!`, "verde");
            document.getElementById("form-usuario").reset(); // Limpiar el formulario
            
            // 🔄 El truco clave: Recargar los selects en caliente para que el nuevo cliente aparezca de una vez en el menú de citas
            await cargarFormularios(); 
        } else {
            // Captura si el correo ya existe (Error 400 que programamos en el back)
            mostrarAlerta(resultado.detail || "Error al registrar el cliente.", "rojo");
        }
    } catch (error) {
        mostrarAlerta("No se pudo conectar con el servidor al registrar usuario.", "rojo");
    }
}