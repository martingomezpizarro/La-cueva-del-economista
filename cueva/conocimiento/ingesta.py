"""ingesta — carga de conocimiento a La Cueva-LM (incremental, con manifiesto).

Acepta PDFs (teoría), código Python (.py), notebooks (.ipynb) y docs (.md/.txt).
Construye el índice en <repo>/indice/ (o CUEVA_INDICE):

  - TF-IDF (siempre): por palabra clave, liviano. SIN pickle (tfidf.json + tfidf_matriz.npz).
  - Embeddings multilingües (si está sentence-transformers): preguntás en español y
    recupera bibliografía en inglés. Modelo: multilingual-e5-small.

Manifiesto (`manifest.json`): hash SHA-256 + nº de fragmentos por archivo ingerido.
Gracias a él la ingesta es INCREMENTAL: los archivos sin cambios conservan sus fragmentos
y embeddings; solo se procesa lo nuevo/modificado y se descarta lo borrado del disco.
El TF-IDF se reconstruye completo (es barato); los embeddings solo se calculan para lo nuevo.

Colecciones (provenance): cada fragmento lleva `coleccion` ("corpus" = bibliografía curada;
"usuario" = subida por el usuario). La recuperación puede filtrar/priorizar por colección y
las citas marcan el origen — un PDF subido jamás se confunde con el corpus curado.

Uso (CLI en scripts/ingestar.py):
    python scripts/ingestar.py knowledge-base/corpus            # incremental
    python scripts/ingestar.py --completo knowledge-base/corpus # desde cero
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from cueva import config

MODELO_EMB = "intfloat/multilingual-e5-small"

EXT_CODIGO = {".py", ".r", ".jl", ".sql"}
EXT_TEXTO = {".md", ".txt", ".rst"}
EXT_OK = {".pdf", ".ipynb"} | EXT_CODIGO | EXT_TEXTO


def cargar_unidades(path):
    """Devuelve (texto, ref, tipo) por unidad lógica del archivo."""
    p = Path(path)
    ext = p.suffix.lower()
    if ext == ".pdf":
        import fitz  # pymupdf (import perezoso: los tests de texto no lo necesitan)

        doc = fitz.open(path)
        for i in range(doc.page_count):
            yield doc[i].get_text(), f"p.{i + 1}", "prosa"
    elif ext == ".ipynb":
        nb = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
        for j, cell in enumerate(nb.get("cells", []), 1):
            src = "".join(cell.get("source", []))
            if src.strip():
                tipo = "codigo" if cell.get("cell_type") == "code" else "prosa"
                yield src, f"celda {j}", tipo
    elif ext in EXT_CODIGO or ext in EXT_TEXTO:
        tipo = "codigo" if ext in EXT_CODIGO else "prosa"
        lineas = p.read_text(encoding="utf-8", errors="ignore").splitlines()
        bloque = 55
        for ini in range(0, len(lineas), bloque):
            seg = "\n".join(lineas[ini : ini + bloque])
            if seg.strip():
                yield seg, f"líneas {ini + 1}-{min(ini + bloque, len(lineas))}", tipo


def trocear(texto, ref, fuente, tipo, max_chars=1000, overlap=150):
    import re

    if tipo == "prosa":
        texto = re.sub(r"\s+", " ", texto).strip()  # prosa: colapsar espacios
    else:
        texto = texto.strip()  # código: preservar formato
        max_chars = 1500
    if len(texto) < 40:
        return []
    out, ini = [], 0
    while ini < len(texto):
        frag = texto[ini : ini + max_chars]
        if len(frag) > 40:
            out.append({"fuente": fuente, "ref": ref, "tipo": tipo, "texto": frag})
        ini += max_chars - overlap
    return out


def expandir_archivos(entradas: list[str | Path]) -> list[Path]:
    """Si una entrada es carpeta, incluye todos sus archivos soportados (recursivo)."""
    archivos: list[Path] = []
    for a in entradas:
        p = Path(a)
        if p.is_dir():
            archivos += sorted(f for f in p.rglob("*") if f.suffix.lower() in EXT_OK)
        else:
            archivos.append(p)
    return archivos


def _hash_archivo(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def _clave(p: Path) -> str:
    """Identificador estable del archivo en el manifiesto (relativo al repo si se puede)."""
    p = Path(p).resolve()
    try:
        return p.relative_to(config.ROOT).as_posix()
    except ValueError:
        return p.as_posix()


def _leer_manifest(indice: Path) -> dict:
    f = indice / "manifest.json"
    if not f.exists():
        return {}
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _fragmentar_archivo(p: Path, coleccion: str) -> list[dict]:
    nombre = p.stem.strip()
    frags = []
    for texto, ref, tipo in cargar_unidades(p):
        frags.extend(trocear(texto, ref, nombre, tipo))
    clave = _clave(p)
    for fr in frags:
        fr["archivo"] = clave
        fr["coleccion"] = coleccion
    return frags


def construir_tfidf(textos: list[str], indice: Path) -> None:
    """TF-IDF sin pickle: vocabulario+idf en JSON, matriz dispersa en .npz."""
    import numpy as np
    from scipy import sparse
    from sklearn.feature_extraction.text import TfidfVectorizer

    vec = TfidfVectorizer(sublinear_tf=True, ngram_range=(1, 2), min_df=2, max_df=0.6)
    try:
        matriz = vec.fit_transform(textos)
    except ValueError:  # índice muy chico: min_df/max_df vacían el vocabulario
        vec = TfidfVectorizer(sublinear_tf=True, ngram_range=(1, 2))
        matriz = vec.fit_transform(textos)
    vocabulario = {t: int(i) for t, i in vec.vocabulary_.items()}
    (indice / "tfidf.json").write_text(
        json.dumps(
            {"vocabulario": vocabulario, "idf": np.asarray(vec.idf_).tolist(), "ngram_max": 2},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    sparse.save_npz(indice / "tfidf_matriz.npz", matriz.tocsr())


def _embeber(textos: list[str], verboso: bool):
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        if verboso:
            print("  ℹ️  sentence-transformers no instalado → solo TF-IDF.")
        return None
    if verboso:
        print(f"  🌐 Embeddings multilingües de {len(textos)} fragmentos ({MODELO_EMB})…")
    modelo = SentenceTransformer(MODELO_EMB)
    # e5 requiere el prefijo 'passage:' en los documentos
    return modelo.encode(
        [f"passage: {t}" for t in textos],
        normalize_embeddings=True,
        show_progress_bar=verboso,
        batch_size=64,
    ).astype("float32")


def ingestar(
    entradas: list[str | Path],
    *,
    coleccion: str = "corpus",
    embeddings: bool = True,
    incremental: bool = True,
    verboso: bool = True,
) -> dict:
    """Ingesta archivos/carpetas al índice. Devuelve el meta resultante.

    Incremental (default): reusa fragmentos y embeddings de los archivos cuyo hash no
    cambió; procesa solo lo nuevo/modificado; descarta lo que ya no existe en disco.
    Con `incremental=False` el índice se reconstruye desde cero con las entradas dadas.
    """
    import numpy as np

    indice = config.ruta_indice()
    indice.mkdir(parents=True, exist_ok=True)

    manifest = _leer_manifest(indice) if incremental else {}
    previos = manifest.get("archivos", {})
    frag_path = indice / "fragmentos.jsonl"

    # índice previo (solo sirve si tiene el campo `archivo`, i.e. formato v2)
    frags_previos: list[dict] = []
    if incremental and previos and frag_path.exists():
        frags_previos = [
            json.loads(line) for line in frag_path.read_text(encoding="utf-8").splitlines() if line.strip()
        ]
        if frags_previos and "archivo" not in frags_previos[0]:
            if verboso:
                print("  ℹ️  índice en formato viejo (sin manifiesto) → reconstrucción completa.")
            frags_previos, previos = [], {}

    emb_path = indice / "embeddings.npy"
    emb_previos = None
    if frags_previos and emb_path.exists():
        emb_previos = np.load(emb_path)
        if len(emb_previos) != len(frags_previos):  # índice inconsistente → rehacer
            frags_previos, previos, emb_previos = [], {}, None

    # clasificar entradas: nuevas/cambiadas vs sin cambios
    archivos = expandir_archivos(entradas)
    hashes = {_clave(p): _hash_archivo(p) for p in archivos}
    procesar = [p for p in archivos if previos.get(_clave(p), {}).get("hash") != hashes[_clave(p)]]
    claves_procesar = {_clave(p) for p in procesar}

    # conservar fragmentos de archivos sin cambios QUE SIGAN EXISTIENDO en disco
    def _vigente(fr: dict) -> bool:
        if fr["archivo"] in claves_procesar:
            return False
        info = previos.get(fr["archivo"])
        if info is None:
            return False
        ruta = config.ROOT / fr["archivo"]
        return ruta.exists() or Path(fr["archivo"]).exists()

    conservados_idx = [i for i, fr in enumerate(frags_previos) if _vigente(fr)]
    conservados = [frags_previos[i] for i in conservados_idx]

    # procesar lo nuevo/cambiado
    nuevos: list[dict] = []
    for p in procesar:
        frs = _fragmentar_archivo(p, coleccion)
        nuevos.extend(frs)
        if verboso:
            print(f"  📄 {p.stem}: {len(frs)} fragmentos")
    if verboso and conservados:
        print(f"  ♻️  {len(conservados)} fragmentos reutilizados (archivos sin cambios)")

    registros = conservados + nuevos
    if not registros:
        raise SystemExit("No se extrajo contenido. ¿PDF escaneado (OCR) o tipo no soportado?")
    for i, r in enumerate(registros):
        r["id"] = i

    frag_path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in registros), encoding="utf-8")
    construir_tfidf([r["texto"] for r in registros], indice)

    # embeddings: reusar los de fragmentos conservados; calcular solo los nuevos
    meta = {"n": len(registros), "modelo_emb": None}
    if embeddings:
        emb_conservados = (
            emb_previos[conservados_idx]
            if emb_previos is not None and manifest.get("modelo_emb") == MODELO_EMB
            else None
        )
        pendientes = registros if emb_conservados is None else nuevos
        vecs_nuevos = _embeber([r["texto"] for r in pendientes], verboso) if pendientes else None
        if pendientes and vecs_nuevos is None:
            # no hay sentence-transformers: el índice queda coherente SOLO con TF-IDF
            if emb_path.exists():
                emb_path.unlink()
        else:
            partes = []
            if emb_conservados is not None:
                partes.append(emb_conservados)
            if vecs_nuevos is not None:
                partes.append(vecs_nuevos)
            if partes:
                np.save(emb_path, np.vstack(partes) if len(partes) > 1 else partes[0])
                meta["modelo_emb"] = MODELO_EMB

    # manifiesto y meta
    archivos_manifest = {k: v for k, v in previos.items() if any(r["archivo"] == k for r in registros)}
    conteo: dict[str, int] = {}
    for r in registros:
        conteo[r["archivo"]] = conteo.get(r["archivo"], 0) + 1
    for p in procesar:
        k = _clave(p)
        archivos_manifest[k] = {
            "hash": hashes[k],
            "n_fragmentos": conteo.get(k, 0),
            "coleccion": coleccion,
        }
    colecciones: dict[str, int] = {}
    for r in registros:
        colecciones[r.get("coleccion", "corpus")] = colecciones.get(r.get("coleccion", "corpus"), 0) + 1
    meta["colecciones"] = colecciones
    (indice / "meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    (indice / "manifest.json").write_text(
        json.dumps(
            {"archivos": archivos_manifest, "modelo_emb": meta["modelo_emb"]}, ensure_ascii=False, indent=1
        ),
        encoding="utf-8",
    )

    if verboso:
        print(f"✅ {len(registros)} fragmentos indexados ({len(nuevos)} nuevos) → {indice}")
        print(
            f"   Recuperación: {'embeddings multilingües + TF-IDF' if meta['modelo_emb'] else 'TF-IDF'}"
            f" · colecciones: {colecciones}"
        )
    return meta
