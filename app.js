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
    <tr>
        <td style="color: var(--gold); font-weight: 600;">${cita.id}</td>
        <td style="color: var(--text-light); font-weight: 500;">${nombreCliente}</td>
        <td>${nombreBarbero}</td>
        <td><span class="service-badge">${nombreServicio}</span></td>
        <td style="color: #8892b0;">${fechaFormateada}</td>
        <td class="text-center" style="white-space: nowrap;">
            <button onclick="reprogramarCita(${cita.id})" class="btn btn-action-edit" style="margin-right: 5px;">Reprogramar</button>
            <button onclick="cancelarCita(${cita.id})" class="btn btn-action-delete">Cancelar</button>
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

// Auxiliar para alertas adaptadas al tema oscuro
function mostrarAlerta(mensaje, tipo) {
    const alerta = document.getElementById("alerta");
    if (!mensaje) {
        alerta.classList.add("hidden");
        return;
    }
    alerta.classList.remove("hidden", "bg-green-950/40", "text-green-400", "border-green-800", "bg-red-950/40", "text-red-400", "border-red-800");
    
    if (tipo === "verde") {
        alerta.classList.add("bg-green-950/40", "text-green-400", "border-green-800");
    } else {
        alerta.classList.add("bg-red-950/40", "text-red-400", "border-red-800");
    }
    alerta.innerText = mensaje;
}

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
// Ejemplo de cómo debe quedar adaptada tu función de cancelar
async function cancelarCita(id) {
    // 🔥 Reemplazamos el confirm viejo por nuestro modal premium asíncrono
    const confirmado = await mostrarConfirmacionCustom(`¿Estás seguro de que deseas cancelar la cita número ${id}?`);
    
    if (!confirmado) return; // Si le da a "Volver", rompemos el flujo de forma segura

    try {
        const res = await fetch(`${API_URL}/citas/${id}`, {
            method: "DELETE"
        });

        if (res.ok) {
            mostrarAlerta(`Cita número ${id} cancelada con éxito.`, "verde");
            cargarCitas(); // Recargar la tabla en caliente
        } else {
            mostrarAlerta("No se pudo cancelar la cita en el servidor.", "rojo");
        }
    } catch (error) {
        mostrarAlerta("Error de conexión al intentar cancelar la cita.", "rojo");
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

function mostrarAlerta(mensaje, tipo) {
    const alerta = document.getElementById("alerta");
    if (!mensaje) {
        alerta.classList.add("hidden");
        return;
    }
    alerta.classList.remove("hidden", "alert-success", "alert-error");
    
    if (tipo === "verde") {
        alerta.classList.add("alert-success");
    } else {
        alerta.classList.add("alert-error");
    }
    alerta.innerText = mensaje;
}

// Función para disparar el modal de confirmación premium de forma asíncrona
function mostrarConfirmacionCustom(mensaje) {
    return new Promise((resolve) => {
        const modal = document.getElementById("custom-confirm-modal");
        const txtMensaje = document.getElementById("custom-modal-message");
        const btnConfirm = document.getElementById("btn-modal-confirm");
        const btnCancel = document.getElementById("btn-modal-cancel");

        // Asignamos el texto dinámico
        txtMensaje.innerText = mensaje;
        
        // Mostramos el modal quitando la clase hidden
        modal.classList.remove("hidden");

        // Función interna para cerrar el modal limpiamente
        function cerrar() {
            modal.classList.add("hidden");
            btnConfirm.removeEventListener("click", onConfirm);
            btnCancel.removeEventListener("click", onCancel);
        }

        function onConfirm() { cerrar(); resolve(true); }
        function onCancel() { cerrar(); resolve(false); }

        // Escuchamos los clicks de los botones del modal
        btnConfirm.addEventListener("click", onConfirm);
        btnCancel.addEventListener("click", onCancel);
    });
}