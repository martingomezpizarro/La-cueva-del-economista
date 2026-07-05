"""biblioteca — la bibliografía que SUBE el usuario (colección "usuario").

Checklist de seguridad (docs/PROPUESTA_ARQUITECTURA.md §5.3): extensión en lista blanca,
tamaño acotado, verificación de firma mágica (un .pdf debe SER un PDF), nombre de archivo
REGENERADO (el nombre que manda el usuario jamás se usa para construir rutas), y todo lo
subido se indexa en una colección separada con provenance — nunca se mezcla con el corpus
curado sin marca de origen.

Los archivos viven en <datos>/biblioteca/ (CUEVA_DATA; ignorado por git).
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from pathlib import Path

from cueva import config

from . import ingesta, recuperar

EXTENSIONES = {".pdf", ".md", ".txt"}
MAX_BYTES = 30 * 1024 * 1024  # 30 MB


class ArchivoInvalido(ValueError):
    pass


def ruta_biblioteca() -> Path:
    return config.ruta_datos() / "biblioteca"


def _slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "_", s).strip("_").lower()
    return s[:60] or "documento"


def validar(nombre_original: str, contenido: bytes) -> str:
    """Aplica el checklist y devuelve la extensión validada. Lanza ArchivoInvalido."""
    ext = Path(nombre_original or "").suffix.lower()
    if ext not in EXTENSIONES:
        raise ArchivoInvalido(
            f"Extensión no permitida: {ext or '(sin extensión)'}. Aceptadas: {', '.join(sorted(EXTENSIONES))}"
        )
    if not contenido:
        raise ArchivoInvalido("Archivo vacío.")
    if len(contenido) > MAX_BYTES:
        raise ArchivoInvalido(f"Archivo demasiado grande ({len(contenido) // (1 << 20)} MB; máximo 30 MB).")
    if ext == ".pdf" and not contenido.startswith(b"%PDF"):
        raise ArchivoInvalido("El archivo dice ser PDF pero no tiene firma de PDF.")
    return ext


def guardar_e_indexar(nombre_original: str, contenido: bytes) -> dict:
    """Valida, guarda con nombre regenerado e indexa incrementalmente (colección 'usuario')."""
    ext = validar(nombre_original, contenido)
    hash8 = hashlib.sha256(contenido).hexdigest()[:8]
    nombre = f"{_slug(Path(nombre_original).stem)}-{hash8}{ext}"

    carpeta = ruta_biblioteca()
    carpeta.mkdir(parents=True, exist_ok=True)
    destino = carpeta / nombre
    destino.write_bytes(contenido)

    try:
        meta = ingesta.ingestar([destino], coleccion="usuario", incremental=True, verboso=False)
    except Exception:
        destino.unlink(missing_ok=True)  # un archivo que no se pudo indexar no queda a medias
        raise
    recuperar.limpiar_cache()

    n_frag = _fragmentos_de(destino)
    return {
        "ok": True,
        "archivo": nombre,
        "titulo": Path(nombre_original).stem,
        "fragmentos": n_frag,
        "coleccion": "usuario",
        "indice_total": meta.get("n"),
    }


def _fragmentos_de(destino: Path) -> int:
    manifest = ingesta._leer_manifest(config.ruta_indice())
    info = manifest.get("archivos", {}).get(ingesta._clave(destino), {})
    return int(info.get("n_fragmentos", 0))


def listar() -> list[dict]:
    """Archivos subidos por el usuario, con su estado en el índice."""
    carpeta = ruta_biblioteca()
    if not carpeta.exists():
        return []
    manifest = ingesta._leer_manifest(config.ruta_indice()).get("archivos", {})
    out = []
    for f in sorted(carpeta.iterdir()):
        if f.suffix.lower() not in EXTENSIONES:
            continue
        info = manifest.get(ingesta._clave(f), {})
        out.append(
            {
                "archivo": f.name,
                "bytes": f.stat().st_size,
                "fragmentos": int(info.get("n_fragmentos", 0)),
                "indexado": bool(info),
            }
        )
    return out
