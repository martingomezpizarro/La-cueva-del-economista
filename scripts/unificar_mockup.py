"""Une los dos mockups en un solo HTML: docs/mockup/cueva-unificada.html.

- Mesa de Trabajo (Explorar, Análisis, Laboratorio): docs/mockup/mesa-de-trabajo.html, tal cual.
- Línea de Tiempo: el módulo 1 de docs/mockup/cueva-mockup.html, embebido en un iframe
  (srcdoc) para que su CSS y su JS no choquen con los de la Mesa.

Los originales no se tocan. Volver a correr cuando cambie cualquiera de los dos.
Uso: python scripts/unificar_mockup.py
"""
import base64
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1] / "docs" / "mockup"
mesa = (RAIZ / "mesa-de-trabajo.html").read_text(encoding="utf-8")
tl = (RAIZ / "cueva-mockup.html").read_text(encoding="utf-8")

# --- Línea de Tiempo: sin su topbar, sin su Mesa vieja, sin su copiloto flotante ---
tl = tl.replace("</style>", """
.topbar{display:none!important}
#mod-mesa{display:none!important}
.ia-fab,.ia-panel{display:none!important}
.app{height:100vh}
</style>""", 1)
tl_b64 = base64.b64encode(tl.encode("utf-8")).decode("ascii")

# --- Selector de módulos real en la topbar de la Mesa ---
viejo = '<nav class="modswitch" aria-label="Módulos"><span>Línea de Tiempo</span><span aria-current="true">Mesa de Trabajo</span></nav>'
nuevo = ('<nav class="modswitch" aria-label="Módulos">'
         '<button type="button" data-mod="tiempo" aria-current="false">Línea de Tiempo</button>'
         '<button type="button" data-mod="mesa" aria-current="true">Mesa de Trabajo</button></nav>')
assert viejo in mesa, "No encontré el modswitch de la Mesa: revisar el mockup"
mesa = mesa.replace(viejo, nuevo, 1)

css = """
<style>
.modswitch button{all:unset;cursor:pointer;padding:5px 13px;border-radius:7px;font-size:13px;font-weight:500;color:var(--ink-dim)}
.modswitch button:hover{color:var(--ink)}
.modswitch button:focus-visible{outline:2px solid var(--accent);outline-offset:1px}
.modswitch button[aria-current="true"]{background:var(--surface);color:var(--ink);box-shadow:var(--shadow);font-weight:600}
@media (max-width:640px){.modswitch button{padding:5px 9px}}
#mod-tiempo{display:none}
#mod-tiempo iframe{display:block;width:100%;border:0;background:var(--ground)}
body.en-tiempo{overflow:hidden}
body.en-tiempo #mod-tiempo{display:block}
body.en-tiempo .topbar .modo{display:none}
body.en-tiempo > :not(.topbar):not(#mod-tiempo):not(script):not(style){display:none!important}
</style>
"""
mesa = mesa.replace("</head>", css + "</head>", 1) if "</head>" in mesa else mesa.replace("<header class=\"topbar\">", css + "<header class=\"topbar\">", 1)

bloque = f"""
<section id="mod-tiempo" aria-label="Línea de Tiempo"><iframe id="tl-frame" title="Línea de Tiempo"></iframe></section>
<script type="application/octet-stream" id="tl-src">{tl_b64}</script>
<script>
(function(){{
  const fr=document.getElementById('tl-frame'), top=document.querySelector('.topbar');
  let cargado=false;
  function alto(){{fr.style.height=(innerHeight-top.offsetHeight)+'px'}}
  function temaAlFrame(){{
    const d=fr.contentDocument; if(!d) return;
    const t=document.documentElement.dataset.theme;
    if(t) d.documentElement.setAttribute('data-theme',t); else d.documentElement.removeAttribute('data-theme');
    const w=fr.contentWindow; try{{ if(w.drawTimeline) w.drawTimeline(); }}catch(e){{}}
  }}
  function cargar(){{
    if(cargado) return; cargado=true;
    const bin=atob(document.getElementById('tl-src').textContent.trim());
    const bytes=Uint8Array.from(bin,c=>c.charCodeAt(0));
    fr.addEventListener('load',temaAlFrame);
    fr.srcdoc=new TextDecoder('utf-8').decode(bytes);
  }}
  function ir(mod){{
    document.querySelectorAll('.modswitch button[data-mod]').forEach(b=>b.setAttribute('aria-current',b.dataset.mod===mod));
    document.body.classList.toggle('en-tiempo',mod==='tiempo');
    if(mod==='tiempo'){{cargar();alto();setTimeout(temaAlFrame,0);window.scrollTo({{top:0}})}}
    else if(typeof pintarVista==='function'){{pintarVista()}}
  }}
  document.querySelector('.modswitch').addEventListener('click',e=>{{const b=e.target.closest('button[data-mod]');if(b)ir(b.dataset.mod)}});
  addEventListener('resize',()=>{{if(document.body.classList.contains('en-tiempo'))alto()}});
  document.getElementById('tema').addEventListener('click',()=>setTimeout(temaAlFrame,0));
}})();
</script>
"""
mesa = mesa.replace("</body>", bloque + "</body>", 1) if "</body>" in mesa else mesa + bloque
import re
mesa = re.sub(r"<title>[^<]*</title>", "<title>La Cueva del Economista</title>", mesa, count=1)

salida = RAIZ / "cueva-unificada.html"
salida.write_text(mesa, encoding="utf-8")
print(salida, round(len(mesa.encode("utf-8")) / 1024), "KB")
