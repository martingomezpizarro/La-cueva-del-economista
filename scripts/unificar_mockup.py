"""Une los dos mockups en un solo HTML: docs/mockup/cueva-unificada.html.

- Mesa de Trabajo (Explorar, Análisis, Laboratorio): docs/mockup/mesa-de-trabajo.html, tal cual.
- Línea de Tiempo: el módulo 1 de docs/mockup/cueva-mockup.html, embebido en un iframe
  (srcdoc) para que su CSS y su JS no choquen con los de la Mesa.

Los originales no se tocan. Volver a correr cuando cambie cualquiera de los dos.
También escribe sitio/index.html: la página pública del dominio (ver .github/workflows/pages.yml).
Uso: python scripts/unificar_mockup.py
"""
import base64
import re
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
@media (max-width:760px){
  .app{height:auto;min-height:100vh;overflow:visible}
  .main,.module.on{display:flex;flex-direction:column}
  .main{overflow:visible}
  .rail,.rail-r{flex:0 0 auto!important;width:100%!important;max-height:none;border-left:none!important;border-right:none!important;border-bottom:1px solid var(--line)}
  .rail .scroll,.rail-r .scroll{max-height:300px}
  .stage{min-height:78vh;order:-1}
}
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
mesa = re.sub(r"<title>[^<]*</title>", "<title>La Cueva del Economista</title>", mesa, count=1)

salida = RAIZ / "cueva-unificada.html"
salida.write_text(mesa, encoding="utf-8")
print(salida, round(len(mesa.encode("utf-8")) / 1024), "KB")

# --- Sitio público: sitio/index.html es lo que sirve cuevadeleconomista.martingomezpizarro.com.ar ---
# Se publica SOLO la carpeta sitio/ (workflow .github/workflows/pages.yml), nunca la raíz del repo.
AVISO = """
<style>
.aviso-sitio{position:fixed;left:calc(14px + env(safe-area-inset-left,0px));bottom:calc(14px + env(safe-area-inset-bottom,0px));z-index:40;max-width:min(460px,calc(100vw - 100px));
  display:flex;gap:10px;align-items:flex-start;padding:9px 12px;border-radius:10px;background:var(--surface);color:var(--ink-2);border:1px solid var(--line);box-shadow:var(--shadow);font-size:12px;line-height:1.45}
.aviso-sitio b{color:var(--ink)}
.aviso-sitio button{all:unset;cursor:pointer;color:var(--ink-dim);font-size:14px;line-height:1;padding:0 2px}
.aviso-sitio button:focus-visible{outline:2px solid var(--accent)}
html body.en-tiempo > div#aviso-sitio.aviso-sitio.aviso-sitio{display:flex!important}
</style>
<div class="aviso-sitio" id="aviso-sitio" role="note"><span><b>Vista previa de la plataforma, en construcción.</b> Todas las series son datos reales (BCRA, INDEC, FMI, Maddison y otras fuentes académicas); cada una indica su fuente.</span><button type="button" aria-label="Cerrar aviso" onclick="this.parentNode.remove()">✕</button></div>
"""
sitio = Path(__file__).resolve().parents[1] / "sitio"
sitio.mkdir(exist_ok=True)
pagina = mesa.replace("</body>", AVISO + "</body>", 1) if "</body>" in mesa else mesa + AVISO
(sitio / "index.html").write_text(pagina, encoding="utf-8")
(sitio / "CNAME").write_text("cuevadeleconomista.martingomezpizarro.com.ar\n", encoding="utf-8")
(sitio / ".nojekyll").write_text("", encoding="utf-8")
print(sitio / "index.html", round(len(pagina.encode("utf-8")) / 1024), "KB")
