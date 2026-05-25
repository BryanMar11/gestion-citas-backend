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

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    especialidad = Column(String(100), nullable=True)

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

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    prestador_id = Column(Integer, ForeignKey("prestadores.id", ondelete="CASCADE"), nullable=False)
    servicio_id = Column(Integer, ForeignKey("servicios.id", ondelete="RESTRICT"), nullable=False)
    fecha_hora = Column(DateTime, nullable=False)
    estado = Column(String(20), default="pendiente")

    usuario = relationship("Usuario", back_populates="citas")
    prestador = relationship("Prestador", back_populates="citas")
    servicio = relationship("Servicio", back_populates="citas")