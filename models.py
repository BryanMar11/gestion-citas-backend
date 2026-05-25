from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    telefono = Column(String(20), nullable=True)
    email = Column(String(100), unique=True, index=True, nullable=False)

    citas = relationship("Cita", back_populates="usuario")

class Prestador(Base):
    __tablename__ = "prestadores"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    especialidad = Column(String(100), nullable=True)
    email = Column(String(100), unique=True, nullable=False)
    
    # 👇 AGREGA ESTA LÍNEA PARA QUE ENCUENTRE LA PROPIEDAD
    citas = relationship("Cita", back_populates="prestador")

class Servicio(Base):
    __tablename__ = "servicios"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre_servicio = Column(String(100), nullable=False)
    precio = Column(Numeric(precision=10, scale=2), nullable=False)
    duracion_minutos = Column(Integer, nullable=False)

    citas = relationship("Cita", back_populates="servicio")

class Cita(Base):
    __tablename__ = "citas"

    id = Column(Integer, primary_key=True, index=True)
    fecha_hora = Column(DateTime, nullable=False)
    
    # 1. Las llaves foráneas (Fíjate que tengan el ForeignKey apuntando a la tabla correcta)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    prestador_id = Column(Integer, ForeignKey("prestadores.id"), nullable=False) # <-- ASEGÚRATE DE QUE ESTA LÍNEA ESTÉ ASÍ
    servicio_id = Column(Integer, ForeignKey("servicios.id"), nullable=False)

    # 2. Las relaciones (Para que se entiendan bidireccionalmente con la otra tabla)
    usuario = relationship("Usuario", back_populates="citas")
    prestador = relationship("Prestador", back_populates="citas") # <-- Y QUE ESTA COINCIDA CON LA DE PRESTADORES
    servicio = relationship("Servicio", back_populates="citas")