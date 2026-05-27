# 🌲 Silvestra — Sistema de Administración de Colonos

App web para la Asociación de Colonos Silvestra-Canoas AC.

## Stack técnico
- **Backend**: Python + FastAPI
- **Base de datos**: SQLite (fácil, sin instalación extra)
- **Frontend**: HTML/JS incluido (el que ya tienes)
- **Puerto**: http://localhost:8000

---

## Instrucciones para Claude Code

### 1. Instalar dependencias

```bash
pip install fastapi uvicorn sqlmodel python-multipart jinja2 openpyxl
```

### 2. Inicializar la base de datos con los lotes reales

```bash
python app/init_db.py
```

### 3. Correr el servidor

```bash
uvicorn app.main:app --reload --port 8000
```

### 4. Abrir en el navegador

```
http://localhost:8000
```

---

## Estructura del proyecto

```
silvestra-claudecode/
├── app/
│   ├── main.py          ← servidor FastAPI principal
│   ├── models.py        ← tablas de base de datos
│   ├── routes/
│   │   ├── lotes.py     ← CRUD lotes
│   │   ├── pagos.py     ← registro de pagos
│   │   ├── gastos.py    ← gastos y proveedores
│   │   └── reportes.py  ← concentrado y exportación
│   └── init_db.py       ← carga datos iniciales del Excel
├── static/
│   └── index.html       ← el frontend (única fuente, servido por main.py)
├── requirements.txt
└── README.md
```

---

## Prompts sugeridos en Claude Code

Una vez abierto el proyecto, puedes decirle a Claude Code:

- *"Agrega importación de Excel para cargar los pagos bancarios directamente"*
- *"Crea un endpoint que genere el estado de cuenta de cada colono en PDF"*
- *"Agrega envío de estados de cuenta por email con smtplib"*
- *"Implementa autenticación JWT para admin y residentes"*
- *"Agrega exportación del concentrado de cobranza a Excel con openpyxl"*
