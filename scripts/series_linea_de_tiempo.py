"""Arma las series troncales ANUALES de la Línea de Tiempo con datos reales → data/historia/series_troncales.json.

Insumos (carpeta pasada como argumento; ninguno se versiona salvo el resultado):
- gmd/*.dta: archivos limpios del Global Macro Database (Müller et al. 2025, licencia MIT), bajados de
  raw.githubusercontent.com/KMueller-Lab/Global-Macro-Database/refs/heads/main/data/clean/...
  (MOXLAD, Bruegel, IMF_FPP, IMF_WEO).
- maddison_arg.json: Maddison Project Database 2023, Argentina (dataverse.nl/api/access/datafile/421302).
- apertura_fh.txt: Fouquin y Hugot (CEPII 2016), (X+M)/PBI, vía owid/owid-datasets.
- toi.json, eph_puntual.json, eph_continua.json: API de Series de Tiempo de datos.gob.ar
  (82.1_ITI_2004_A_27, distribución 42.2 y 42.3_EPH_PUNTUATAL_0_M_30).
- 0027_inflacion_mensual.csv: BCRA, API v4.0, variable 27 (data/series/bcra/).
Uso: python scripts/series_linea_de_tiempo.py <carpeta_insumos> [<csv_inflacion_bcra>]
"""

import json
import sys
from pathlib import Path

import pandas as pd

INS = Path(sys.argv[1])
BCRA = sys.argv[2] if len(sys.argv) > 2 else "data/series/bcra/0027_inflacion_mensual.csv"
G = str(INS / "gmd") + "/"


def g(f, c):
    d = pd.read_stata(G + f, convert_categoricals=False)
    d = d[d.ISO3 == "ARG"][["year", c]].dropna()
    return pd.Series(d[c].values, index=d.year.astype(int).values).astype(float)


# Maddison 2023 (transcripto de dataverse.nl/api/access/datafile/421302)
mad = json.load(open(INS / "maddison_arg.json"))
pbipc = pd.Series({int(k): v[0] for k, v in mad.items() if v[0] is not None})
pop = pd.Series({int(k): v[1] / 1000 for k, v in mad.items() if v[1] is not None})
weo_pc = g("IMF_WEO.dta", "IMF_WEO_rGDP_pc")
weo_pop = g("IMF_WEO.dta", "IMF_WEO_pop")
for y in (2023, 2024):
    pbipc[y] = pbipc[y - 1] * weo_pc[y] / weo_pc[y - 1]
    pop[y] = pop[y - 1] * weo_pop[y] / weo_pop[y - 1]
# Inflación: MOxLAD 1901-1944, BCRA promedio anual 1945-2025
mx = g("MOXLAD.dta", "MOXLAD_infl").loc[1901:1944]
m = pd.read_csv(BCRA, parse_dates=["fecha"])
m["idx"] = (1 + m.valor / 100).cumprod()
a = m.groupby(m.fecha.dt.year).idx.agg(["mean", "count"])
av = (a["mean"] / a["mean"].shift() - 1) * 100
av = av[(a["count"] == 12) & (a["count"].shift() >= 11)].loc[1945:2025]
infl = pd.concat([mx, av])
# TCR: Bruegel REER invertido (sube = depreciación) 1960-2023, empalmado con ITCRM BCRA 2024
# ITCRM del BCRA (prom. anual de la serie mensual, datos.gob.ar 116.3_TCRMA_0_M_36) 1997-2024;
# antes de 1997, Bruegel REER invertido y empalmado en 1997. Bruegel NO se usa después de 1997:
# deflacta con el IPC del INDEC 2007-2015 y exagera la depreciación real.
itcrm = pd.Series(
    [
        83.75025817803014,
        81.97334805401645,
        72.96250279888913,
        72.88708819788384,
        69.46971215638216,
        168.39631770636043,
        151.7525587914753,
        158.49326261716465,
        161.54317210177396,
        165.58573667277824,
        160.4107453455091,
        145.75221139607243,
        143.88918433975104,
        130.22921248440505,
        121.69199565705496,
        104.20284962744047,
        100.36943337998065,
        105.68923820329378,
        82.72434883654638,
        94.19025580944684,
        88.29354127026187,
        109.39674182530786,
        121.3531304845489,
        118.21846769852677,
        114.09256220425614,
        95.1633226377997,
        96.94527390598483,
        95.11722089919029,
    ],
    index=range(1997, 2025),
)
itcrm = itcrm / itcrm[1997] * 100
reer = g("Bruegel.dta", "BRUEGEL_REER")
br = 1 / reer
br = br / br[1997] * 100
tcr = pd.concat([br.loc[1960:1996], itcrm])
# Deuda y resultado fiscal: FMI Public Finances in Modern History (Mauro et al.) + WEO 2023-2024
deuda = g("IMF_FPP.dta", "IMF_FPP_govdebt_GDP")
fis = g("IMF_FPP.dta", "IMF_FPP_govdef_GDP")
for y in (2023, 2024):
    deuda[y] = g("IMF_WEO.dta", "IMF_WEO_govdebt_GDP")[y]
    fis[y] = g("IMF_WEO.dta", "IMF_WEO_govdef_GDP")[y]
# Apertura: Fouquin & Hugot (CEPII), (X+M)/PBI
ap = {}
for tok in open(INS / "apertura_fh.txt").read().split():
    y, v = tok.split(":")
    ap[int(y)] = float(v)
ap = pd.Series(ap)
# TOI INDEC base 2004
toi = pd.Series(json.load(open(INS / "toi.json")), dtype=float)
toi.index = toi.index.astype(int)
# Desempleo: EPH puntual (prom. ondas) 1982-2002, EPH continua (prom. trimestres) 2003-2025
eph = json.load(open(INS / "eph_puntual.json"))
s = pd.Series(eph)
s.index = pd.to_datetime(s.index)
des = (s.groupby(s.index.year).mean() * 100).loc[1982:2002]
cont = pd.Series(json.load(open(INS / "eph_continua.json")), dtype=float) * 100
cont.index = cont.index.astype(int)
des = pd.concat([des, cont])
out = {}


def put(k, s, dec):
    s = s.dropna().sort_index()
    out[k] = [[int(y), round(float(v), dec)] for y, v in s.items() if y >= 1875]


put("pbipc", pbipc, 0)
put("poblacion", pop, 2)
put("infl", infl, 1)
put("tcr", tcr, 1)
put("deuda", deuda, 1)
put("fiscal", fis, 1)
put("apertura", ap, 1)
put("toi", toi, 1)
put("desempleo", des, 1)
Path("data/historia").mkdir(parents=True, exist_ok=True)
json.dump(out, open("data/historia/series_troncales.json", "w"), separators=(",", ":"))
