"""
Generador de backlog con Gemini (fase 1).

Uso:
    python generar_backlog.py necesidad.txt
    python generar_backlog.py            (te pide escribir la necesidad)

Requiere:
    pip install google-genai
    Variable de entorno GEMINI_API_KEY con tu clave de Google AI Studio.

Salida:
    salidas/backlog_<fecha>.json   -> borrador para que lo revises
    backlog.db (SQLite)            -> historial de todo lo generado (base para la fase 2)
"""
import json
import os
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

from google import genai
from google.genai import types

BASE = Path(__file__).parent
# Revisa en AI Studio qué modelos Flash tienes gratis y cámbialo si hace falta.
MODELO = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-lite")

FORMATO_SALIDA = """
Responde SOLO con un JSON válido (sin texto extra ni bloques de código) con esta estructura:
{
  "epic": {
    "title": "...",
    "description": "...",
    "business_value": "..."
  },
  "features": [
    {
      "title": "...",
      "description": "...",
      "user_stories": [
        {
          "title": "...",
          "as_a": "...",
          "i_want": "...",
          "so_that": "...",
          "acceptance_criteria": [
            {"given": "...", "when": "...", "then": "..."}
          ],
          "story_points": 3,
          "tasks": [
            {"title": "...", "description": "..."}
          ]
        }
      ]
    }
  ]
}
"""


def construir_instrucciones() -> str:
    normas = (BASE / "normas.md").read_text(encoding="utf-8")
    return (
        "Eres un analista de requerimientos senior. A partir de una necesidad, "
        "creas la jerarquía Épica > Features > Historias de usuario > Tasks "
        "para Azure DevOps o Jira. Debes cumplir estrictamente estas normas:\n\n"
        + normas
        + "\n\nSi la necesidad es ambigua, haz suposiciones razonables y "
        "agrégalas en la descripción de la épica bajo 'Supuestos:'.\n"
        + FORMATO_SALIDA
    )


def generar(necesidad: str) -> dict:
    clave = os.environ.get("GEMINI_API_KEY")
    if not clave:
        sys.exit("Falta la variable de entorno GEMINI_API_KEY (mira las instrucciones).")

    client = genai.Client(api_key=clave)
    respuesta = client.models.generate_content(
        model=MODELO,
        contents="NECESIDAD:\n" + necesidad,
        config=types.GenerateContentConfig(
            system_instruction=construir_instrucciones(),
            response_mime_type="application/json",
            temperature=0.3,
        ),
    )
    texto = (respuesta.text or "").strip()
    texto = re.sub(r"^```(?:json)?|```$", "", texto, flags=re.MULTILINE).strip()
    try:
        return json.loads(texto)
    except json.JSONDecodeError as e:
        sys.exit(f"El modelo no devolvió un JSON válido ({e}). Intenta de nuevo.\n\n{texto[:500]}")


def validar(data: dict) -> list:
    """Revisiones básicas contra las normas. Devuelve una lista de avisos."""
    avisos = []
    if "epic" not in data:
        avisos.append("Falta la épica.")
    for f in data.get("features", []):
        if not f.get("user_stories"):
            avisos.append(f"Feature sin historias: {f.get('title')}")
        for hu in f.get("user_stories", []):
            t = hu.get("title")
            if not all(hu.get(k) for k in ("as_a", "i_want", "so_that")):
                avisos.append(f"HU sin formato Como/Quiero/Para: {t}")
            n = len(hu.get("acceptance_criteria", []))
            if not 2 <= n <= 6:
                avisos.append(f"HU con {n} criterios (norma: 2 a 6): {t}")
            if len(hu.get("tasks", [])) < 2:
                avisos.append(f"HU con menos de 2 tasks: {t}")
    return avisos


def guardar_json(data: dict) -> Path:
    carpeta = BASE / "salidas"
    carpeta.mkdir(exist_ok=True)
    ruta = carpeta / f"backlog_{datetime.now():%Y%m%d_%H%M%S}.json"
    ruta.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return ruta


def guardar_db(data: dict, necesidad: str) -> None:
    """Guarda cada ítem para poder analizarlo en la fase 2."""
    con = sqlite3.connect(BASE / "backlog.db")
    con.execute(
        """CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT, tipo TEXT, titulo TEXT, padre_id INTEGER,
            estado TEXT, modelo TEXT, fecha TEXT, fuente TEXT, contenido TEXT)"""
    )
    run_id = datetime.now().strftime("%Y%m%d%H%M%S")
    fecha = datetime.now().isoformat(timespec="seconds")

    def sin(obj: dict, clave: str) -> dict:
        return {k: v for k, v in obj.items() if k != clave}

    def ins(tipo, titulo, padre, contenido):
        cur = con.execute(
            "INSERT INTO items (run_id,tipo,titulo,padre_id,estado,modelo,fecha,fuente,contenido)"
            " VALUES (?,?,?,?,?,?,?,?,?)",
            (run_id, tipo, titulo, padre, "generado", MODELO, fecha, necesidad,
             json.dumps(contenido, ensure_ascii=False)),
        )
        return cur.lastrowid

    epica = data.get("epic", {})
    epic_id = ins("Epic", epica.get("title"), None, epica)
    for f in data.get("features", []):
        fid = ins("Feature", f.get("title"), epic_id, sin(f, "user_stories"))
        for hu in f.get("user_stories", []):
            hid = ins("User Story", hu.get("title"), fid, sin(hu, "tasks"))
            for t in hu.get("tasks", []):
                ins("Task", t.get("title"), hid, t)
    con.commit()
    con.close()


def main():
    if len(sys.argv) > 1:
        necesidad = Path(sys.argv[1]).read_text(encoding="utf-8").strip()
    else:
        print("Escribe la necesidad (termina con una línea vacía):")
        lineas = []
        while (linea := input()) != "":
            lineas.append(linea)
        necesidad = "\n".join(lineas).strip()
    if not necesidad:
        sys.exit("No hay necesidad para procesar.")

    print(f"Generando con {MODELO}...")
    data = generar(necesidad)

    for aviso in validar(data):
        print("AVISO:", aviso)

    ruta = guardar_json(data)
    guardar_db(data, necesidad)

    n_f = len(data.get("features", []))
    n_hu = sum(len(f.get("user_stories", [])) for f in data.get("features", []))
    n_t = sum(len(h.get("tasks", [])) for f in data.get("features", []) for h in f.get("user_stories", []))
    print(f"Listo: 1 épica, {n_f} features, {n_hu} historias, {n_t} tasks.")
    print(f"Revisa el borrador en: {ruta}")


if __name__ == "__main__":
    main()
