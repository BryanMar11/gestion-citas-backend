from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from database import engine, Base, get_db
import models

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