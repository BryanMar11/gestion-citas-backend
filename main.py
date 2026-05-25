from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from database import engine, Base, get_db
import models
from datetime import datetime

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
    db_prestador = db.query(models.Prestador).filter(models.Prestador.email == prestador.email).first()
    if db_prestador:
        raise HTTPException(status_code=400, detail="El email del prestador ya está registrado")
    
    nuevo_prestador = models.Prestador(
        nombre=prestador.nombre,
        especialidad=prestador.especialidad,
        email=prestador.email
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
    nuevo_servicio = models.Servicio(
        nombre=servicio.nombre,
        descripcion=servicio.descripcion,
        precio=servicio.precio
    )
    db.add(nuevo_servicio)
    db.commit()
    db.refresh(nuevo_servicio)
    return nuevo_servicio

@app.get("/servicios/", response_model=list[ServicioResponse])
def obtener_servicios(db: Session = Depends(get_db)):
    return db.query(models.Servicio).all()

# --- ENDPOINTS PARA CITAS (AGENDAMIENTO) ---

@app.post("/citas/", response_model=CitaResponse)
def crear_cita(cita: CitaCreate, db: Session = Depends(get_db)):
    # 1. Validar que el usuario exista en la BD
    usuario = db.query(models.Usuario).filter(models.Usuario.id == cita.usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="El usuario especificado no existe")
        
    # 2. Validar que el prestador exista
    prestador = db.query(models.Prestador).filter(models.Prestador.id == cita.prestador_id).first()
    if not prestador:
        raise HTTPException(status_code=404, detail="El prestador especificado no existe")
        
    # 3. Validar que el servicio exista
    servicio = db.query(models.Servicio).filter(models.Servicio.id == cita.servicio_id).first()
    if not servicio:
        raise HTTPException(status_code=404, detail="El servicio especificado no existe")

    # 4. Si todo está melo, se crea la cita
    nueva_cita = models.Cita(
        usuario_id=cita.usuario_id,
        prestador_id=cita.prestador_id,
        servicio_id=cita.servicio_id,
        fecha_hora=cita.fecha_hora
    )
    db.add(nueva_cita)
    db.commit()
    db.refresh(nueva_cita)
    return nueva_cita

# Ruta para ver todas las citas agendadas
@app.get("/citas/", response_model=list[CitaResponse])
def obtener_citas(db: Session = Depends(get_db)):
    return db.query(models.Cita).all()