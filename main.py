from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from database import engine, Base, get_db
import models
from datetime import datetime

# 1. CREAR LA APLICACIÓN (¡Solo una vez!)
app = FastAPI()

# 2. CONFIGURACIÓN DE CORS (Habilita la conexión con tu index.html)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite peticiones desde cualquier origen
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos: GET, POST, PUT, DELETE
    allow_headers=["*"],
)

# 3. ESQUEMAS DE PYDANTIC (Validadores de Datos)

# Esquemas para Citas
class CitaCreate(BaseModel):
    usuario_id: int
    prestador_id: int
    servicio_id: int
    fecha_hora: datetime

class CitaResponse(BaseModel):
    id: int
    usuario_id: int
    prestador_id: int
    servicio_id: int
    fecha_hora: datetime

    class Config:
        from_attributes = True

# Esquemas para Usuarios
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


# 4. CREACIÓN DE TABLAS EN LA BASE DE DATOS
Base.metadata.create_all(bind=engine)

# 🔥 LOGICA DE INSERCIÓN AUTOMÁTICA MEJORADA
@app.on_event("startup")
def cargar_servicios_defecto():
    from database import SessionLocal
    db = SessionLocal()
    try:
        # 🚨 Validamos si existe el servicio "string" o si queremos renovar la lista
        existe_string = db.query(models.Servicio).filter(models.Servicio.nombre_servicio == "string").first()
        
        # Si encuentra datos feos o está vacía, limpiamos y metemos los reales
        if existe_string or db.query(models.Servicio).count() <= 3:
            print("🧹 Limpiando servicios antiguos o de prueba...")
            db.query(models.Servicio).delete() # Borra lo viejo para resetear
            db.commit()

            servicios_predeterminados = [
                {"nombre_servicio": "Corte de Cabello Clasico", "precio": 18000.0, "duracion_minutos": 30},
                {"nombre_servicio": "Perfilado de Barba", "precio": 12000.0, "duracion_minutos": 20},
                {"nombre_servicio": "Diseño y Depilacion de Cejas", "precio": 8000.0, "duracion_minutos": 15},
                {"nombre_servicio": "Combo: Corte + Barba + Cejas", "precio": 32000.0, "duracion_minutos": 60},
                {"nombre_servicio": "Lavado y Exfoliacion Facial", "precio": 15000.0, "duracion_minutos": 25}
            ]
            
            for s in servicios_predeterminados:
                nuevo_servicio = models.Servicio(
                    nombre_servicio=s["nombre_servicio"],
                    precio=s["precio"],
                    duracion_minutos=s["duracion_minutos"]
                )
                db.add(nuevo_servicio)
            
            db.commit()
            print("💈 ¡Servicios predeterminados cargados exitosamente en MariaDB!")
    except Exception as e:
        print(f"Error cargando servicios en el startup: {e}")
    finally:
        db.close()

# 5. ENDPOINTS (Rutas de la API)

# --- ENDPOINTS PARA USUARIOS ---

@app.post("/usuarios/", response_model=UsuarioResponse)
def crear_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    db_usuario = db.query(models.Usuario).filter(models.Usuario.email == usuario.email).first()
    if db_usuario:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    nuevo_usuario = models.Usuario(
        nombre=usuario.nombre,
        telefono=usuario.telefono,
        email=usuario.email
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    return nuevo_usuario

@app.get("/usuarios/", response_model=list[UsuarioResponse])
def obtener_usuarios(db: Session = Depends(get_db)):
    return db.query(models.Usuario).all()


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
    
    # Mapeo para que FastAPI no se confunda con el esquema de respuesta
    nuevo_servicio.nombre = nuevo_servicio.nombre_servicio
    return nuevo_servicio

@app.get("/servicios/") 
def obtener_servicios(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    servicios = db.query(models.Servicio).offset(skip).limit(limit).all()
    # Ajustamos el atributo para la respuesta frontend
    for s in servicios:
        s.nombre = s.nombre_servicio
    return servicios


# --- ENDPOINTS PARA CITAS (AGENDAMIENTO) ---

# Listar todas las citas (¡Esta es la que le hacía falta a tu frontend!)
@app.get("/citas/")
def obtener_citas(db: Session = Depends(get_db)):
    return db.query(models.Cita).all()

# Crear una cita con validaciones de choque y existencia
@app.post("/citas/")
def crear_cita(cita: CitaCreate, db: Session = Depends(get_db)):
    
    # Validar existencias
    if not db.query(models.Usuario).filter(models.Usuario.id == cita.usuario_id).first():
        raise HTTPException(status_code=404, detail="El usuario especificado no existe.")
        
    if not db.query(models.Prestador).filter(models.Prestador.id == cita.prestador_id).first():
        raise HTTPException(status_code=404, detail="El prestador (barbero) especificado no existe.")
        
    if not db.query(models.Servicio).filter(models.Servicio.id == cita.servicio_id).first():
        raise HTTPException(status_code=404, detail="El servicio especificado no existe.")
    
    # Formatear fecha
    fecha_busqueda = cita.fecha_hora
    if isinstance(fecha_busqueda, str):
        fecha_busqueda = fecha_busqueda.replace("T", " ")
    
    # Control de choques de horario
    cita_existente = db.query(models.Cita).filter(
        models.Cita.prestador_id == cita.prestador_id,
        models.Cita.fecha_hora == fecha_busqueda
    ).first()
    
    if cita_existente:
        raise HTTPException(
            status_code=400,
            detail="El prestador ya tiene una cita agendada para esta fecha y hora."
        )
    
    nuevo_cita = models.Cita(
        usuario_id=cita.usuario_id,
        prestador_id=cita.prestador_id,
        servicio_id=cita.servicio_id,
        fecha_hora=fecha_busqueda
    )
    
    db.add(nuevo_cita)
    db.commit()
    db.refresh(nuevo_cita)
    return nuevo_cita

# Cancelar una cita
@app.delete("/citas/{cita_id}")
def cancelar_cita(cita_id: int, db: Session = Depends(get_db)):
    cita = db.query(models.Cita).filter(models.Cita.id == cita_id).first()
    if not cita:
        raise HTTPException(status_code=404, detail="La cita no existe.")
    
    db.delete(cita)
    db.commit()
    return {"message": f"Cita con ID {cita_id} cancelada exitosamente."}

# Modificar / Reprogramar una cita
@app.put("/citas/{cita_id}")
def modificar_cita(cita_id: int, nueva_fecha_hora: str, db: Session = Depends(get_db)):
    cita = db.query(models.Cita).filter(models.Cita.id == cita_id).first()
    if not cita:
        raise HTTPException(status_code=404, detail="La cita no existe.")
    
    fecha_limpia = nueva_fecha_hora.replace("T", " ")
    
    horario_ocupado = db.query(models.Cita).filter(
        models.Cita.prestador_id == cita.prestador_id,
        models.Cita.fecha_hora == fecha_limpia,
        models.Cita.id != cita_id
    ).first()
    
    if horario_ocupado:
        raise HTTPException(
            status_code=400, 
            detail="El prestador ya tiene otra cita agendada en ese horario."
        )
    
    cita.fecha_hora = fecha_limpia
    db.commit()
    db.refresh(cita)
    return {"message": "Cita reprogramada con éxito.", "cita": cita}