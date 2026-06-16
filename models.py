# ============================================================
#   "El Señor es mi pastor; nada me faltará."
#                                         — Salmos 23:1
#
#   "Encomienda al Señor tus obras y tus planes
#    se cumplirán."
#                                         — Proverbios 16:3
#
#   "Porque yo sé los planes que tengo para ustedes,
#    planes de bienestar y no de calamidad,
#    para darles un futuro y una esperanza."
#                                         — Jeremías 29:11
# ============================================================

from typing import Optional
from datetime import date, datetime
from sqlmodel import SQLModel, Field


class Lote(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    manzana: int
    numero: int
    paseo: str
    m2: float
    propietario: Optional[str] = None
    cuota_cof: float = 1350.0
    email: Optional[str] = None
    telefono: Optional[str] = None
    fecha_escrituracion: Optional[date] = None
    activo: bool = True


class Pago(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    lote_id: int = Field(foreign_key="lote.id")
    fecha_pago: date
    importe: float
    mes_aplicado: str          # "2026-05"
    concepto: str = "COF"
    referencia: Optional[str] = None
    estado: str = "por_aprobar"   # por_aprobar | aprobado | rechazado
    notas: Optional[str] = None
    creado_en: datetime = Field(default_factory=datetime.utcnow)


class Gasto(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    fecha: date
    concepto: str
    proveedor: str
    tipo: str   # Mantenimiento | Seguridad | Administración | Servicios | Otro
    importe: float
    factura: Optional[str] = None
    notas: Optional[str] = None


class Usuario(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True)
    hashed_password: str
    rol: str = "residente"   # admin | residente | visor
    lote_id: Optional[int] = Field(default=None, foreign_key="lote.id")
    activo: bool = True
    debe_cambiar_password: bool = False


class Proveedor(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    rfc: Optional[str] = None
    tipo_persona: str = "moral"   # moral | fisica


class MovimientoBancario(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    fecha: date
    descripcion: str
    cargo: float = 0.0
    abono: float = 0.0
    referencia: Optional[str] = None
    tipo: str = "sin_clasificar"  # ingreso_colono | pago_proveedor | sin_clasificar
    lote_id: Optional[int] = Field(default=None, foreign_key="lote.id")
    proveedor_id: Optional[int] = Field(default=None, foreign_key="proveedor.id")
    tiene_iva_ret: bool = False
    tiene_isr_ret: bool = False
    iva_ret: float = 0.0
    isr_ret: float = 0.0
    importado_en: datetime = Field(default_factory=datetime.utcnow)


class LecturaAgua(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    lote_id: int = Field(foreign_key="lote.id")
    mes: str                  # "2026-05"
    lectura_anterior: float = 0.0
    lectura_actual: float = 0.0
    consumo_m3: float = 0.0
    tarifa_por_m3: float = 15.0
    importe: float = 0.0


class GastoReal(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    mes: str                  # "2026-05"
    concepto: str             # uno de los 16 conceptos del presupuesto
    importe: float = 0.0
    notas: Optional[str] = None


class ProrrateoPorLote(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    lote_id: int = Field(foreign_key="lote.id")
    mes: str
    concepto: str
    importe_prorrateado: float = 0.0
    es_campestre: bool = False   # True si el lote es de Dicka (sin propietario)


class Config(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    clave: str = Field(unique=True)
    valor: str = ""


class Descuento(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    lote_id: int = Field(foreign_key="lote.id")
    tipo: str = "descuento"      # "descuento" | "condonacion"
    concepto: str = "COF"        # COF | COV
    importe: float
    anio: Optional[int] = None
    notas: Optional[str] = None
    fecha: date = Field(default_factory=date.today)
    creado_en: datetime = Field(default_factory=datetime.utcnow)


class CuotaAnual(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    anio: int
    min_m2: float
    max_m2: Optional[float] = None
    importe: float


class GastoArchivo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    gasto_id: int = Field(foreign_key="gasto.id")
    nombre: str
    tipo_mime: str = "application/octet-stream"
    contenido_b64: str
    subido_en: datetime = Field(default_factory=datetime.utcnow)
