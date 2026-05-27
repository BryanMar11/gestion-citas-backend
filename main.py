from fastapi import FastAPI, Depends, HTTPException, status, CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from database import engine, Base, get_db
import models
from datetime import datetime

# Configuración de CORS para que tu frontend se pueda conectar sin bloqueos
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite peticiones desde cualquier origen (ideal para desarrollo)
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos: GET, POST, PUT, DELETE
    allow_headers=["*"],
)

# Esquema para crear la cita (lo que envía el cliente)
class CitaCreate(BaseModel):
    usuario_id: int
    prestador_id: int
    servicio_id: int
    fecha_hora: datetime

# Esquema para la respuesta (lo que devuelve la API)
class CitaResponse(BaseModel):
    id: int
    usuario_id: int
    prestador_id: int
    servicio_id: int
    fecha_hora: datetime

    class Config:
        from_attributes = True

# 1. Crear las tablas en la base de datos si no existen
Base.metadata.create_all(bind=engine)

app = FastAPI()

# 2. Esquemas de Pydantic (Validadores de datos)
class UsuarioCreate(BaseModel):
    nombre: str
    telefono: str | None = None
    email: EmailStr

class UsuarioResponse(BaseModel):
    id: int
    nombre: str
    telefono: str | None = None
    email: str

    class Config:
        from_attributes = True


# 3. ENDPOINTS (Rutas de la API)

# Ruta para crear un usuario nuevo
@app.post("/usuarios/", response_model=UsuarioResponse)
def crear_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    # Verificar si el email ya está registrado
    db_usuario = db.query(models.Usuario).filter(models.Usuario.email == usuario.email).first()
    if db_usuario:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    # Crear la instancia del modelo SQLAlchemy
    nuevo_usuario = models.Usuario(
        nombre=usuario.nombre,
        telefono=usuario.telefono,
        email=usuario.email
    )
    
    db.add(nuevo_usuario) # Agregarlo a la sesión
    db.commit()           # Guardar en MariaDB
    db.refresh(nuevo_usuario) # Traer el ID generado
    return nuevo_usuario

# Ruta para listar todos los usuarios
@app.get("/usuarios/", response_model=list[UsuarioResponse])
def obtener_usuarios(db: Session = Depends(get_db)):
    usuarios = db.query(models.Usuario).all()
    return usuarios

# Esquemas para Prestadores
class PrestadorCreate(BaseModel):
    nombre: str
    especialidad: str
    email: EmailStr

class PrestadorResponse(BaseModel):
    id: int
    nombre: str
    especialidad: str
    email: str

    class Config:
        from_attributes = True

# Esquemas para Servicios
class ServicioCreate(BaseModel):
    nombre: str
    descripcion: str | None = None
    precio: float

class ServicioResponse(BaseModel):
    id: int
    nombre: str
    descripcion: str | None = None
    precio: float

    class Config:
        from_attributes = True
        
# --- ENDPOINTS PARA PRESTADORES ---

@app.post("/prestadores/", response_model=PrestadorResponse)
def crear_prestador(prestador: PrestadorCreate, db: Session = Depends(get_db)):
    # Buscar si ya existe por email
    db_prestador = db.query(models.Prestador).filter(models.Prestador.email == prestador.email).first()
    if db_prestador:
        raise HTTPException(status_code=400, detail="El email del prestador ya está registrado")
    
    nuevo_prestador = models.Prestador(
        nombre=prestador.nombre,
        especialidad=prestador.especialidad,
        email=prestador.email # Mapeo limpio
    )
    db.add(nuevo_prestador)
    db.commit()
    db.refresh(nuevo_prestador)
    return nuevo_prestador

@app.get("/prestadores/", response_model=list[PrestadorResponse])
def obtener_prestadores(db: Session = Depends(get_db)):
    return db.query(models.Prestador).all()


# --- ENDPOINTS PARA SERVICIOS ---

@app.post("/servicios/", response_model=ServicioResponse)
def crear_servicio(servicio: ServicioCreate, db: Session = Depends(get_db)):
    datos_servicio = servicio.model_dump()
    
    nuevo_servicio = models.Servicio(
        nombre_servicio=datos_servicio.get("nombre") or datos_servicio.get("nombre_servicio"),
        precio=datos_servicio.get("precio"),
        duracion_minutos=next(
            (v for k, v in datos_servicio.items() if "duracion" in k or "minutos" in k), 
            30
        )
    )
    
    db.add(nuevo_servicio)
    db.commit()
    db.refresh(nuevo_servicio)
    
    # El truco mágico para engañar a FastAPI:
    nuevo_servicio.nombre = nuevo_servicio.nombre_servicio
    
    return nuevo_servicio

# 👇 LE QUITAMOS EL response_model=list[ServicioResponse] PARA QUE DEJE PASAR LOS DATOS DE LA BD
@app.get("/servicios/") 
def obtener_servicios(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    servicios = db.query(models.Servicio).offset(skip).limit(limit).all()
    return servicios

# --- ENDPOINTS PARA CITAS (AGENDAMIENTO) ---

@app.post("/citas/")
def crear_cita(cita: CitaCreate, db: Session = Depends(get_db)):
    
    # === NUEVA VALIDACIÓN DE EXISTENCIA ===
    # 1. Verificar si el usuario existe
    if not db.query(models.Usuario).filter(models.Usuario.id == cita.usuario_id).first():
        raise HTTPException(status_code=404, detail="El usuario especificado no existe.")
        
    # 2. Verificar si el prestador existe
    if not db.query(models.Prestador).filter(models.Prestador.id == cita.prestador_id).first():
        raise HTTPException(status_code=404, detail="El prestador (barbero) especificado no existe.")
        
    # 3. Verificar si el servicio existe
    if not db.query(models.Servicio).filter(models.Servicio.id == cita.servicio_id).first():
        raise HTTPException(status_code=404, detail="El servicio especificado no existe.")
    
    # === TU LÓGICA DE CONTROL DE CHOQUES QUE YA FUNCIONA ===
    fecha_busqueda = cita.fecha_hora
    if isinstance(fecha_busqueda, str):
        fecha_busqueda = fecha_busqueda.replace("T", " ")
    
    cita_existente = db.query(models.Cita).filter(
        models.Cita.prestador_id == cita.prestador_id,
        models.Cita.fecha_hora == fecha_busqueda
    ).first()
    
    if cita_existente:
        raise HTTPException(
            status_code=400,
            detail="El prestador ya tiene una cita agendada para esta fecha y hora."
        )
    
    # === GUARDADO EN BASE DE DATOS ===
    nueva_cita = models.Cita(
        usuario_id=cita.usuario_id,
        prestador_id=cita.prestador_id,
        servicio_id=cita.servicio_id,
        fecha_hora=fecha_busqueda
    )
    
    db.add(nueva_cita)
    db.commit()
    db.refresh(nueva_cita)
    return nueva_cita

@app.delete("/citas/{cita_id}")
def cancelar_cita(cita_id: int, db: Session = Depends(get_db)):
    # Buscar la cita por su ID
    cita = db.query(models.Cita).filter(models.Cita.id == cita_id).first()
    
    # Si no existe, tiramos error 404
    if not cita:
        raise HTTPException(status_code=404, detail="La cita no existe.")
    
    # Si existe, la borramos de la base de datos
    db.delete(cita)
    db.commit()
    
    return {"message": f"Cita con ID {cita_id} cancelada exitosamente."}

@app.put("/citas/{cita_id}")
def modificar_cita(cita_id: int, nueva_fecha_hora: str, db: Session = Depends(get_db)):
    # 1. Buscar la cita que se quiere modificar
    cita = db.query(models.Cita).filter(models.Cita.id == cita_id).first()
    if not cita:
        raise HTTPException(status_code=404, detail="La cita no existe.")
    
    # Limpiar el string de la fecha por si viene con la 'T' de Swagger
    fecha_limpia = nueva_fecha_hora.replace("T", " ")
    
    # 2. VALIDACIÓN: Revisar que el barbero no esté ocupado en ese nuevo horario
    # (Ignoramos la cita actual para que no choque consigo misma si mandan la misma hora)
    horario_ocupado = db.query(models.Cita).filter(
        models.Cita.prestador_id == cita.prestador_id,
        models.Cita.fecha_hora == fecha_limpia,
        models.Cita.id != cita_id  # Que sea una cita diferente
    ).first()
    
    if horario_ocupado:
        raise HTTPException(
            status_code=400, 
            detail="El prestador ya tiene otra cita agendada en ese horario."
        )
    
    # 3. Si todo está bien, actualizamos la fecha y hora
    cita.fecha_hora = fecha_limpia
    db.commit()
    db.refresh(cita)
    
    return {"message": "Cita reprogramada con éxito.", "cita": cita}