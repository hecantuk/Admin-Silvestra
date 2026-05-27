from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from sqlmodel import Session, select, create_engine, SQLModel
from typing import Optional, List
from datetime import date
import os, io

from models import (Lote, Pago, Gasto, Usuario,
                    Proveedor, MovimientoBancario,
                    LecturaAgua, GastoReal, ProrrateoPorLote)

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./silvestra.db")
# Railway usa postgres://, SQLAlchemy necesita postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)

def get_session():
    with Session(engine) as session:
        yield session

app = FastAPI(title="Silvestra Admin API", version="1.0.0")

# Servir el frontend
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)


# ─── ROOT ───────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def root():
    index = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index):
        return FileResponse(index)
    return HTMLResponse("<h2>Copia tu index.html en la carpeta /static/</h2>")


# ─── LOTES ──────────────────────────────────────────────────
@app.get("/api/lotes")
def get_lotes(manzana: Optional[int] = None):
    with Session(engine) as s:
        q = select(Lote)
        if manzana:
            q = q.where(Lote.manzana == manzana)
        return s.exec(q).all()

@app.get("/api/lotes/{lote_id}")
def get_lote(lote_id: int):
    with Session(engine) as s:
        lote = s.get(Lote, lote_id)
        if not lote:
            raise HTTPException(404, "Lote no encontrado")
        return lote

@app.put("/api/lotes/{lote_id}")
def update_lote(lote_id: int, data: dict):
    with Session(engine) as s:
        lote = s.get(Lote, lote_id)
        if not lote:
            raise HTTPException(404, "Lote no encontrado")
        for k, v in data.items():
            setattr(lote, k, v)
        s.add(lote)
        s.commit()
        s.refresh(lote)
        return lote


# ─── PAGOS ──────────────────────────────────────────────────
@app.get("/api/pagos")
def get_pagos(estado: Optional[str] = None, mes: Optional[str] = None):
    with Session(engine) as s:
        q = select(Pago)
        if estado:
            q = q.where(Pago.estado == estado)
        if mes:
            q = q.where(Pago.mes_aplicado == mes)
        return s.exec(q).all()

@app.post("/api/pagos")
def create_pago(pago: Pago):
    with Session(engine) as s:
        s.add(pago)
        s.commit()
        s.refresh(pago)
        return pago

@app.put("/api/pagos/{pago_id}/aprobar")
def aprobar_pago(pago_id: int):
    with Session(engine) as s:
        pago = s.get(Pago, pago_id)
        if not pago:
            raise HTTPException(404, "Pago no encontrado")
        pago.estado = "aprobado"
        s.add(pago)
        s.commit()
        return {"ok": True, "id": pago_id}


# ─── GASTOS ──────────────────────────────────────────────────
@app.get("/api/gastos")
def get_gastos(mes: Optional[str] = None):
    with Session(engine) as s:
        q = select(Gasto)
        if mes:
            q = q.where(Gasto.fecha.like(f"{mes}%"))
        return s.exec(q).all()

@app.post("/api/gastos")
def create_gasto(gasto: Gasto):
    with Session(engine) as s:
        s.add(gasto)
        s.commit()
        s.refresh(gasto)
        return gasto


# ─── REPORTE / SALDOS ────────────────────────────────────────
@app.get("/api/reporte/saldos")
def reporte_saldos(mes: str = "2026-05"):
    """Concentrado de cobranza: saldo de cada lote para el mes dado."""
    with Session(engine) as s:
        lotes = s.exec(select(Lote).where(Lote.propietario != None)).all()
        resultado = []
        for lote in lotes:
            pagos = s.exec(
                select(Pago).where(
                    Pago.lote_id == lote.id,
                    Pago.estado == "aprobado",
                    Pago.mes_aplicado == mes,
                )
            ).all()
            pagado = sum(p.importe for p in pagos)
            saldo = lote.cuota_cof - pagado
            resultado.append({
                "lote_id": lote.id,
                "manzana": lote.manzana,
                "numero": lote.numero,
                "propietario": lote.propietario,
                "cuota": lote.cuota_cof,
                "pagado": pagado,
                "saldo": saldo,
                "estado": "corriente" if saldo <= 0 else ("abonando" if pagado > 0 else "moroso"),
            })
        total = len(resultado)
        corriente = sum(1 for r in resultado if r["estado"] == "corriente")
        morosos = sum(1 for r in resultado if r["estado"] == "moroso")
        return {
            "mes": mes,
            "total_lotes": total,
            "corriente": corriente,
            "morosos": morosos,
            "abonando": total - corriente - morosos,
            "pct_corriente": round(corriente / total * 100, 1) if total else 0,
            "pct_morosos": round(morosos / total * 100, 1) if total else 0,
            "detalle": resultado,
        }


# ─── STATS DASHBOARD ─────────────────────────────────────────
@app.get("/api/stats")
def get_stats(mes: str = "2026-05"):
    with Session(engine) as s:
        lotes = s.exec(select(Lote).where(Lote.propietario != None)).all()
        pagos_mes = s.exec(
            select(Pago).where(Pago.mes_aplicado == mes, Pago.estado == "aprobado")
        ).all()
        total_cuotas = sum(l.cuota_cof for l in lotes)
        total_cobrado = sum(p.importe for p in pagos_mes)
        return {
            "lotes_vendidos": len(lotes),
            "total_cuotas_mes": total_cuotas,
            "total_cobrado": total_cobrado,
            "pendiente": total_cuotas - total_cobrado,
            "pct_cobrado": round(total_cobrado / total_cuotas * 100, 1) if total_cuotas else 0,
        }


M2_TOTALES = 299174.17
CONCEPTOS = [
    "LUZ","REDES DE AGUA","CUOTAS DE SEGUROS","RESIDENTFY","INTERNET",
    "MAQ Y EQ","MATERIALES","MTTO FRACCIONAMIENTO","MTTO INFRAESTRUCTURA",
    "GASOLINA","SEGURIDAD","ISR RETENIDO","IVA RETENIDO",
    "COMISION BANCO","IVA GASTOS","NOMINA",
]


# ─── PROVEEDORES ─────────────────────────────────────────────
@app.get("/api/proveedores")
def get_proveedores():
    with Session(engine) as s:
        return s.exec(select(Proveedor)).all()

@app.post("/api/proveedores")
def create_proveedor(p: Proveedor):
    with Session(engine) as s:
        s.add(p); s.commit(); s.refresh(p)
        return p

@app.put("/api/proveedores/{pid}")
def update_proveedor(pid: int, data: dict):
    with Session(engine) as s:
        p = s.get(Proveedor, pid)
        if not p: raise HTTPException(404, "Proveedor no encontrado")
        for k, v in data.items(): setattr(p, k, v)
        s.add(p); s.commit(); s.refresh(p)
        return p

@app.delete("/api/proveedores/{pid}")
def delete_proveedor(pid: int):
    with Session(engine) as s:
        p = s.get(Proveedor, pid)
        if not p: raise HTTPException(404)
        s.delete(p); s.commit()
        return {"ok": True}


# ─── MÓDULO 1: BANCO ─────────────────────────────────────────
@app.get("/api/banco/movimientos")
def get_movimientos(mes: Optional[str] = None):
    with Session(engine) as s:
        q = select(MovimientoBancario)
        if mes:
            q = q.where(MovimientoBancario.fecha.like(f"{mes}%"))
        movs = s.exec(q.order_by(MovimientoBancario.fecha.desc())).all()
        total_abonos = sum(m.abono for m in movs)
        total_cargos = sum(m.cargo for m in movs)
        return {"movimientos": movs, "total_abonos": total_abonos, "total_cargos": total_cargos}

@app.post("/api/banco/importar")
async def importar_banco(file: UploadFile = File(...)):
    import openpyxl
    content = await file.read()
    wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    # Detectar fila de encabezado buscando palabras clave
    header_row = 0
    for i, row in enumerate(rows[:10]):
        vals = [str(v).lower() if v else "" for v in row]
        if any("fecha" in v for v in vals) and any("descripci" in v for v in vals):
            header_row = i
            break
    headers = [str(v).lower().strip() if v else "" for v in rows[header_row]]
    col = {}
    for i, h in enumerate(headers):
        if "fecha" in h: col["fecha"] = i
        elif "descripci" in h: col["desc"] = i
        elif "cargo" in h or "retiro" in h or "debito" in h: col["cargo"] = i
        elif "abono" in h or "deposito" in h or "credito" in h: col["abono"] = i
        elif "referen" in h or "folio" in h: col["ref"] = i

    importados = 0
    with Session(engine) as s:
        proveedores = s.exec(select(Proveedor)).all()
        lotes = s.exec(select(Lote).where(Lote.propietario != None)).all()
        for row in rows[header_row + 1:]:
            if not row or not row[col.get("fecha", 0)]: continue
            raw_fecha = row[col.get("fecha", 0)]
            if hasattr(raw_fecha, "date"):
                fecha = raw_fecha.date()
            else:
                try: fecha = date.fromisoformat(str(raw_fecha)[:10])
                except: continue
            desc = str(row[col.get("desc", 1)] or "")
            cargo = float(row[col.get("cargo", 2)] or 0)
            abono = float(row[col.get("abono", 3)] or 0)
            ref = str(row[col.get("ref", 4)] or "") if "ref" in col else None
            # Clasificar
            tipo = "sin_clasificar"
            lote_id = None
            prov_id = None
            desc_lower = desc.lower()
            for lote in lotes:
                if lote.propietario:
                    apellido = lote.propietario.split()[-1].lower()
                    if len(apellido) > 3 and apellido in desc_lower:
                        tipo = "ingreso_colono"; lote_id = lote.id; break
            if tipo == "sin_clasificar":
                for prov in proveedores:
                    if prov.nombre.split()[0].lower() in desc_lower:
                        tipo = "pago_proveedor"; prov_id = prov.id; break
            mov = MovimientoBancario(
                fecha=fecha, descripcion=desc, cargo=cargo, abono=abono,
                referencia=ref, tipo=tipo, lote_id=lote_id, proveedor_id=prov_id,
            )
            s.add(mov)
            importados += 1
        s.commit()
    return {"importados": importados}

@app.put("/api/banco/movimientos/{mid}")
def update_movimiento(mid: int, data: dict):
    with Session(engine) as s:
        m = s.get(MovimientoBancario, mid)
        if not m: raise HTTPException(404)
        for k, v in data.items(): setattr(m, k, v)
        s.add(m); s.commit(); s.refresh(m)
        return m

@app.delete("/api/banco/movimientos/{mid}")
def delete_movimiento(mid: int):
    with Session(engine) as s:
        m = s.get(MovimientoBancario, mid)
        if not m: raise HTTPException(404)
        s.delete(m); s.commit()
        return {"ok": True}


# ─── MÓDULO 2: DIOT ──────────────────────────────────────────
@app.get("/api/diot")
def get_diot(mes: Optional[str] = None):
    with Session(engine) as s:
        q = select(MovimientoBancario).where(MovimientoBancario.tipo == "pago_proveedor")
        if mes:
            q = q.where(MovimientoBancario.fecha.like(f"{mes}%"))
        movs = s.exec(q).all()
        provs = {p.id: p for p in s.exec(select(Proveedor)).all()}
        rows = []
        for m in movs:
            p = provs.get(m.proveedor_id)
            rows.append({
                "id": m.id,
                "fecha": str(m.fecha),
                "proveedor": p.nombre if p else m.descripcion,
                "rfc": p.rfc if p else None,
                "tipo_persona": p.tipo_persona if p else None,
                "importe": m.cargo,
                "iva_ret": m.iva_ret,
                "isr_ret": m.isr_ret,
            })
        return {"mes": mes, "filas": rows,
                "total_importe": sum(r["importe"] for r in rows),
                "total_iva_ret": sum(r["iva_ret"] for r in rows),
                "total_isr_ret": sum(r["isr_ret"] for r in rows)}


# ─── MÓDULO 3: AGUA ──────────────────────────────────────────
@app.get("/api/agua/lecturas")
def get_lecturas(mes: Optional[str] = None):
    with Session(engine) as s:
        q = select(LecturaAgua)
        if mes: q = q.where(LecturaAgua.mes == mes)
        lecturas = s.exec(q).all()
        lotes = {l.id: l for l in s.exec(select(Lote).where(Lote.propietario != None)).all()}
        result = []
        for lec in lecturas:
            lote = lotes.get(lec.lote_id)
            result.append({**lec.dict(),
                           "propietario": lote.propietario if lote else None,
                           "manzana": lote.manzana if lote else None,
                           "numero": lote.numero if lote else None})
        return result

@app.post("/api/agua/lecturas")
def create_lectura(lec: LecturaAgua):
    lec.consumo_m3 = lec.lectura_actual - lec.lectura_anterior
    lec.importe = round(lec.consumo_m3 * lec.tarifa_por_m3, 2)
    with Session(engine) as s:
        s.add(lec); s.commit(); s.refresh(lec)
        return lec

@app.put("/api/agua/lecturas/{lid}")
def update_lectura(lid: int, data: dict):
    with Session(engine) as s:
        lec = s.get(LecturaAgua, lid)
        if not lec: raise HTTPException(404)
        for k, v in data.items(): setattr(lec, k, v)
        lec.consumo_m3 = lec.lectura_actual - lec.lectura_anterior
        lec.importe = round(lec.consumo_m3 * lec.tarifa_por_m3, 2)
        s.add(lec); s.commit(); s.refresh(lec)
        return lec

@app.delete("/api/agua/lecturas/{lid}")
def delete_lectura(lid: int):
    with Session(engine) as s:
        lec = s.get(LecturaAgua, lid)
        if not lec: raise HTTPException(404)
        s.delete(lec); s.commit()
        return {"ok": True}

@app.get("/api/agua/reporte")
def reporte_agua(mes: str = "2026-05"):
    with Session(engine) as s:
        lecturas = s.exec(select(LecturaAgua).where(LecturaAgua.mes == mes)).all()
        mes_anterior = mes[:5] + str(int(mes[5:]) - 1).zfill(2) if int(mes[5:]) > 1 else str(int(mes[:4]) - 1) + "-12"
        lects_ant = {l.lote_id: l for l in s.exec(select(LecturaAgua).where(LecturaAgua.mes == mes_anterior)).all()}
        lotes = {l.id: l for l in s.exec(select(Lote)).all()}
        result = []
        for lec in lecturas:
            lote = lotes.get(lec.lote_id)
            ant = lects_ant.get(lec.lote_id)
            result.append({
                "lote_id": lec.lote_id,
                "propietario": lote.propietario if lote else None,
                "manzana": lote.manzana if lote else None,
                "numero": lote.numero if lote else None,
                "consumo_actual": lec.consumo_m3,
                "consumo_anterior": ant.consumo_m3 if ant else None,
                "variacion": round(lec.consumo_m3 - ant.consumo_m3, 2) if ant else None,
                "importe": lec.importe,
            })
        return {"mes": mes, "lecturas": result,
                "total_consumo": sum(r["consumo_actual"] for r in result),
                "total_importe": sum(r["importe"] for r in result)}


# ─── MÓDULO 4: PRORRATEO ─────────────────────────────────────
@app.get("/api/prorrateo/conceptos")
def get_conceptos():
    return CONCEPTOS

@app.get("/api/prorrateo/gastos-reales")
def get_gastos_reales(mes: Optional[str] = None):
    with Session(engine) as s:
        q = select(GastoReal)
        if mes: q = q.where(GastoReal.mes == mes)
        return s.exec(q).all()

@app.post("/api/prorrateo/gastos-reales")
def upsert_gasto_real(gr: GastoReal):
    with Session(engine) as s:
        existing = s.exec(
            select(GastoReal).where(GastoReal.mes == gr.mes, GastoReal.concepto == gr.concepto)
        ).first()
        if existing:
            existing.importe = gr.importe
            existing.notas = gr.notas
            s.add(existing); s.commit(); s.refresh(existing)
            return existing
        s.add(gr); s.commit(); s.refresh(gr)
        return gr

@app.post("/api/prorrateo/calcular/{mes}")
def calcular_prorrateo(mes: str):
    with Session(engine) as s:
        gastos = s.exec(select(GastoReal).where(GastoReal.mes == mes)).all()
        if not gastos:
            raise HTTPException(400, "No hay gastos reales para este mes")
        lotes = s.exec(select(Lote)).all()
        # Borrar prorrateo anterior del mes
        s.exec(ProrrateoPorLote.__table__.delete().where(ProrrateoPorLote.mes == mes))
        s.commit()
        registros = 0
        for gasto in gastos:
            costo_m2 = gasto.importe / M2_TOTALES
            for lote in lotes:
                importe = round(costo_m2 * lote.m2, 4)
                es_campestre = lote.propietario is None
                s.add(ProrrateoPorLote(
                    lote_id=lote.id, mes=mes,
                    concepto=gasto.concepto,
                    importe_prorrateado=importe,
                    es_campestre=es_campestre,
                ))
                registros += 1
        s.commit()
        # Resumen
        todos = s.exec(select(ProrrateoPorLote).where(ProrrateoPorLote.mes == mes)).all()
        total_asociados = sum(p.importe_prorrateado for p in todos if not p.es_campestre)
        total_campestre = sum(p.importe_prorrateado for p in todos if p.es_campestre)
        return {"mes": mes, "registros": registros,
                "total_asociados": round(total_asociados, 2),
                "total_campestre": round(total_campestre, 2),
                "total_general": round(total_asociados + total_campestre, 2)}

@app.get("/api/prorrateo/resumen/{mes}")
def resumen_prorrateo(mes: str):
    with Session(engine) as s:
        rows = s.exec(select(ProrrateoPorLote).where(ProrrateoPorLote.mes == mes)).all()
        if not rows:
            return {"mes": mes, "calculado": False}
        gastos = {g.concepto: g.importe for g in s.exec(select(GastoReal).where(GastoReal.mes == mes)).all()}
        por_concepto = {}
        for r in rows:
            if r.concepto not in por_concepto:
                por_concepto[r.concepto] = {"concepto": r.concepto,
                                             "gasto_total": gastos.get(r.concepto, 0),
                                             "asociados": 0, "campestre": 0}
            if r.es_campestre: por_concepto[r.concepto]["campestre"] += r.importe_prorrateado
            else: por_concepto[r.concepto]["asociados"] += r.importe_prorrateado
        conceptos_list = list(por_concepto.values())
        for c in conceptos_list:
            c["asociados"] = round(c["asociados"], 2)
            c["campestre"] = round(c["campestre"], 2)
        return {"mes": mes, "calculado": True,
                "conceptos": conceptos_list,
                "total_asociados": round(sum(c["asociados"] for c in conceptos_list), 2),
                "total_campestre": round(sum(c["campestre"] for c in conceptos_list), 2)}

@app.get("/api/prorrateo/por-lote/{mes}")
def prorrateo_por_lote(mes: str, solo_campestre: bool = False):
    with Session(engine) as s:
        q = select(ProrrateoPorLote).where(ProrrateoPorLote.mes == mes)
        if solo_campestre: q = q.where(ProrrateoPorLote.es_campestre == True)
        rows = s.exec(q).all()
        lotes = {l.id: l for l in s.exec(select(Lote)).all()}
        por_lote = {}
        for r in rows:
            if r.lote_id not in por_lote:
                lote = lotes.get(r.lote_id)
                por_lote[r.lote_id] = {"lote_id": r.lote_id,
                                        "manzana": lote.manzana if lote else None,
                                        "numero": lote.numero if lote else None,
                                        "propietario": lote.propietario if lote else None,
                                        "m2": lote.m2 if lote else None,
                                        "es_campestre": r.es_campestre,
                                        "total": 0, "detalle": {}}
            por_lote[r.lote_id]["total"] = round(por_lote[r.lote_id]["total"] + r.importe_prorrateado, 2)
            por_lote[r.lote_id]["detalle"][r.concepto] = r.importe_prorrateado
        return sorted(por_lote.values(), key=lambda x: (x["es_campestre"], x["manzana"] or 0, x["numero"] or 0))


# ─── MÓDULO 5: ESTADOS FINANCIEROS ───────────────────────────
@app.get("/api/financiero/resumen/{mes}")
def resumen_financiero(mes: str):
    with Session(engine) as s:
        lotes_vendidos = s.exec(select(Lote).where(Lote.propietario != None)).all()
        pagos_mes = s.exec(
            select(Pago).where(Pago.mes_aplicado == mes, Pago.estado == "aprobado")
        ).all()
        gastos_mes = s.exec(
            select(Gasto).where(Gasto.fecha.like(f"{mes}%"))
        ).all()
        gastos_reales = s.exec(select(GastoReal).where(GastoReal.mes == mes)).all()
        prorrateo = s.exec(select(ProrrateoPorLote).where(ProrrateoPorLote.mes == mes)).all()
        # Deuda acumulada Dicka: suma de todo el prorrateo campestre histórico
        deuda_dicka = sum(p.importe_prorrateado for p in s.exec(select(ProrrateoPorLote).where(ProrrateoPorLote.es_campestre == True)).all())
        total_ingresos = sum(p.importe for p in pagos_mes)
        total_gastos = sum(g.importe for g in gastos_mes)
        total_gastos_real = sum(g.importe for g in gastos_reales)
        total_cuotas = sum(l.cuota_cof for l in lotes_vendidos)
        total_cobrado = total_ingresos
        cartera_vencida = total_cuotas - total_cobrado
        gastos_por_concepto = {}
        for g in gastos_mes:
            gastos_por_concepto[g.tipo] = gastos_por_concepto.get(g.tipo, 0) + g.importe
        return {
            "mes": mes,
            "ingresos": {"total": total_ingresos, "cuotas_esperadas": total_cuotas,
                         "pct_cobrado": round(total_ingresos / total_cuotas * 100, 1) if total_cuotas else 0},
            "gastos": {"total": total_gastos, "total_real": total_gastos_real,
                       "por_concepto": gastos_por_concepto},
            "balance": total_ingresos - total_gastos,
            "cartera": {"total_adeudado": cartera_vencida,
                        "lotes_morosos": sum(1 for l in lotes_vendidos if not any(p.lote_id == l.id for p in pagos_mes))},
            "dicka": {"deuda_acumulada": round(deuda_dicka, 2),
                      "mes_actual": round(sum(p.importe_prorrateado for p in prorrateo if p.es_campestre), 2)},
        }
