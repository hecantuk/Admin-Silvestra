# ============================================================
#   "Si permanecen en mí y mis palabras permanecen en ustedes,
#    pidan lo que quieran y se les concederá."
#                                         — Juan 15:7
#
#   "Den gracias al Señor porque Él es bueno;
#    su gran amor perdura para siempre."
#                                         — Salmos 107:1
# ============================================================

"""
Corre UNA SOLA VEZ para crear la base de datos con los lotes reales.
    python app/init_db.py
"""
from sqlmodel import Session, create_engine, SQLModel
from models import Lote, Gasto, Usuario
from datetime import date
import bcrypt, os

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./silvestra.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, echo=True, connect_args=connect_args)
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

LOTES = [
    (24,1,"Paseo de los Nogales",2289.82,"Juan Bosco Martínez Guevara",1350),
    (24,2,"Paseo de los Nogales",2404.85,"José Humberto Valdez Elizondo",1450),
    (24,3,"Paseo de los Nogales",2088.25,"Zayury de la Garza / Erick Molina",1350),
    (24,4,"Paseo de los Sabinos",2248.33,"Raquel Elena Urquidi Garza",1350),
    (24,5,"Paseo de los Sabinos",2254.52,"Antonio de Jesús Rodríguez Caballero",1350),
    (24,6,"Paseo Silvestra",2340.63,None,1400),
    (24,7,"Paseo Silvestra",2008.35,"Alfonso Vazquez Limón",1350),
    (24,8,"Paseo Silvestra",2394.35,None,1400),
    (24,9,"Paseo Silvestra",2262.07,None,1350),
    (24,10,"Paseo Silvestra",2021.29,"CASA MUESTRA",1350),
    (24,11,"Paseo Silvestra",2281.63,"Ricardo Mendoza Barrera",1350),
    (24,12,"Paseo Silvestra",2284.59,"Marlon Abraham Bustillo Mendez",1350),
    (24,13,"Paseo del Encino",2297.98,"Myriam Marybel Torres Tellez",1350),
    (24,14,"Paseo del Encino",2472.82,None,1450),
    (24,15,"Paseo de los Robles",2428.38,"Alejandro Sepulveda López",1450),
    (24,16,"Paseo de los Robles",2207.52,"Alejandro Sepulveda López",1350),
    (24,17,"Paseo de los Nogales",2427.01,None,1450),
    (24,18,"Paseo de los Robles",2705.36,None,1500),
    (24,19,"Paseo de los Nogales",2102.92,"Ramiro Montero Cantú",1350),
    (24,20,"Paseo de los Sabinos",2199.38,"Elena de Canales",1350),
    (24,21,"Paseo de los Sabinos",2455.94,"Wendy Marysol Soltero Rodríguez",1450),
    (24,22,"Paseo de los Sabinos",2402.72,"Carlos Alberto Dávila Rosete",1450),
    (24,31,"Paseo de los Olmos",2734.88,"Rodolfo Martínez Martínez",1500),
    (24,32,"Paseo de los Sabinos",2628.71,"Adrián Tamez Leal",1500),
    (29,2,"Paseo de las Aves",3302.97,"Rocío Griselda Vega Campos",1500),
    (29,10,"Paseo de las Aves",2043.28,"Edgard Yair Pérez Martínez",1350),
    (29,12,"Paseo de las Aves",2450.89,"Orlando Javier Silva Alanis",1450),
    (29,13,"Paseo de las Golondrinas",2227.9,"Armando Rubio Cano",1350),
    (29,14,"Paseo de las Aves",2051.75,"Francisco Javier Coronado Cavazos",1350),
    (29,15,"Paseo de las Golondrinas",3172.85,"Ma Concepción Alonso Molina",1500),
    (29,20,"Paseo de las Golondrinas",2005.18,"Anayancy Carranco Chavez",1350),
    (29,21,"Paseo de las Aves",2025.33,"Rodolfo Maldonado Morales",1350),
    (29,22,"Paseo de las Aves",2000.14,"Manuel Fernando Ortiz Loera",1350),
    (30,2,"Paseo Silvestra",2722.13,"Roberto Soto Palma",1500),
    (30,3,"Paseo Silvestra",2292.4,"Francisco Zertuche / Amelia Villarreal",1350),
    (30,4,"Paseo de los Colibríes",1748.93,"Enrique Javier González Báez",1350),
    (30,8,"Paseo de los Colibríes",1727.55,"Arturo Abraham de León Quintanilla",1350),
    (30,9,"Paseo Silvestra",2013.02,"Martín Silvestre Escobedo Ortega",1350),
    (30,10,"Paseo de los Codornices",1953.73,"Oscar Lara Sánchez",1350),
    (30,17,"Paseo de los Codornices",2088.47,"Noé Valdés Gaona",1350),
    (34,1,"Paseo Silvestra",2489.26,"Francisco Javier González Nieto",1450),
    (34,4,"Paseo de las Aves",2014.42,"Edna Selene Calleros Luna",1350),
    (34,5,"Paseo de las Aves",1928.19,"Fernando Tellez Meza",1350),
    (34,6,"Paseo de las Aves",1823.26,"Ghassan Kahwati Jamal",1350),
    (34,7,"Paseo de las Aves",2051.69,"Juan Carlos Cuervo Kleen",1350),
    (34,8,"Paseo de las Aves",2005.5,"Adrián Mauricio Cuervo Kleen",1350),
    (34,9,"Paseo de las Aves",1952.95,"Mariano Gerardo Morales González",1350),
    (34,12,"Paseo Silvestra",2696.54,"Guadalupe Janneth García Rivera",1500),
    (34,13,"Paseo Silvestra",2195.14,"Heriberto Ojeda Yuste",1350),
    (34,14,"Paseo Silvestra",2275.39,"Saul Sifuentes",1350),
    (34,15,"Paseo de las Garzas",2181.96,"Saul Sifuentes",1350),
    (34,22,"Paseo Silvestra",1619.51,"Armando Silva Leal",1350),
    (34,24,"Paseo de las Garzas",2143.41,"José Alfredo Muñiz Manrique",1350),
    (34,25,"Paseo de las Garzas",1960.34,"Héctor Melende / Alejandra Vázquez",1350),
    (35,2,"Rincón de las Palomas",1566.26,"Adolfo Salazar Herrera",1350),
    (37,1,"Rincón de las Palomas",2284.82,"Enrique Alberto Lozano Cavazos",1350),
    (37,10,"Paseo de las Aves",2127.2,"José Ignacio Rodríguez Rodríguez",1350),
    (37,11,"Paseo de las Aves",2075.45,"Esteban Quintanilla López",1350),
    (37,12,"Paseo de las Aves",1934.55,"Wesley Alexander Rios Grant",1350),
    (37,13,"Paseo de las Aves",2005.9,"César Humberto García Martínez",1350),
    (37,14,"Paseo de las Aves",2487.66,"Enrique Alberto Lozano Cavazos",1400),
    (37,16,"Paseo de las Aves",2008.57,"Víctor Rafael Vega Martínez",1350),
    (38,1,"Paseo de las Aves",2392.11,"David Efrén Ortiz Quintero",1400),
    (38,8,"Paseo de las Aves",1934.34,"Juan Francisco Camacho Cortes",1350),
    (38,10,"Paseo de las Aves",1934.51,"Héctor Eden Ramos Ramos",1350),
    (38,14,"Paseo de las Aves",1931.94,"David Díaz Aedo",1350),
    (38,17,"Paseo de las Aves",2131.34,"Juan Gabriel Macias Villarreal",1350),
    (38,18,"Paseo Silvestra",1810.69,"Oscar Alberto García Rodríguez",1350),
    (38,19,"Paseo Silvestra",2393.18,"Patricia Santacruz González",1400),
]

GASTOS_MAYO = [
    ("2026-05-03","Sueldo vigilante turno A","Jorge Ramos García","Seguridad",8500,"REC-001"),
    ("2026-05-03","Sueldo vigilante turno B","Luis M. Torres","Seguridad",7200,"REC-002"),
    ("2026-05-05","Poda y jardinería","Viveros San Ángel","Mantenimiento",6800,"A-0211"),
    ("2026-05-08","Mantenimiento portón","Automatizaciones Reyes","Mantenimiento",2400,"B-0045"),
    ("2026-05-10","Electricidad área común","CFE","Servicios",1850,"CFE-MAY"),
    ("2026-05-12","Fumigación general","Control de Plagas NL","Mantenimiento",3200,"A-0098"),
    ("2026-05-15","Honorarios administradora","Administradora Silvestra","Administración",5000,"A-001"),
    ("2026-05-15","Agua cisternas","Pipas El Oasis","Servicios",2100,"PIP-012"),
    ("2026-05-18","Reparación barda perimetral","Const. Ramírez","Mantenimiento",4800,"A-0230"),
    ("2026-05-20","Material limpieza","Walmart","Administración",980,"TKT-445"),
    ("2026-05-22","Internet caseta","Telmex","Servicios",470,"TEL-MAY"),
    ("2026-05-25","Señalización vialidad","Señales y Más","Mantenimiento",1300,"A-0319"),
]

def init():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        # Limpiar tablas
        for model in [Lote, Gasto, Usuario]:
            session.exec(model.__table__.delete())
        session.commit()

        # Insertar lotes
        for row in LOTES:
            mza, num, paseo, m2, propietario, cuota = row
            session.add(Lote(
                manzana=mza, numero=num, paseo=paseo,
                m2=m2, propietario=propietario, cuota_cof=cuota,
            ))

        # Insertar gastos mayo
        for row in GASTOS_MAYO:
            fecha_s, concepto, proveedor, tipo, importe, factura = row
            y, m, d = fecha_s.split("-")
            session.add(Gasto(
                fecha=date(int(y), int(m), int(d)),
                concepto=concepto, proveedor=proveedor,
                tipo=tipo, importe=importe, factura=factura,
            ))

        # Usuario admin
        session.add(Usuario(
            email="administradora@silvestra.mx",
            hashed_password=hash_password("silvestra2024"),
            rol="admin",
        ))

        session.commit()
        print("✅ Base de datos inicializada con", len(LOTES), "lotes y", len(GASTOS_MAYO), "gastos")

if __name__ == "__main__":
    init()
