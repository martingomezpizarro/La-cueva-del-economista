/* Revisión del catálogo de series.
   El árbol replica la jerarquía del visualizador del Trabajo Final:
   familia › subgrupo › sub-subgrupo › serie, y las series con apertura como carpeta
   con su «Total». Cada nodo se colapsa.

   Lo que el revisor cambia vive en REVISION y se guarda publicando una versión nueva
   de esta misma página. Nada se serializa desde el DOM: el documento se rearma desde
   los bloques de datos, que es lo único que cambia. */
(function () {
  "use strict";

  const leerJSON = (id) => JSON.parse(document.getElementById(id).textContent || "null");
  const ARBOL = leerJSON("arbol") || [];
  const VOCAB = leerJSON("vocabulario") || { magnitudes: {}, escalas: {}, monedas: {} };
  const FUENTES = leerJSON("fuentes") || [];
  let REVISION = leerJSON("revision") || {};

  const FREQ = { D: "Diaria", M: "Mensual", Q: "Trimestral", A: "Anual" };
  const EDITABLES = ["label", "desc", "fuente", "mag", "esc", "mon", "nota"];
  const ROTULO = {
    label: "Nombre de la serie", desc: "Descripción", fuente: "Fuente",
    mag: "Magnitud", esc: "Escala", mon: "Moneda", nota: "Nota del revisor"
  };

  let sucio = false;
  let abierta = null;
  let filtro = { q: "", estado: "", fuente: "" };

  const esc = (t) => String(t ?? "").replace(/[&<>"]/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  /* ── recorrido del árbol ─────────────────────────────────── */

  function* seriesDe(nodo) {
    for (const s of nodo.items || []) yield* conHijos(s);
    for (const sub of nodo.subs || []) yield* seriesDe(sub);
  }
  function* conHijos(s) {
    yield s;
    for (const h of s.hijos || []) yield* conHijos(h);
  }
  function todas() {
    const out = [];
    for (const fam of ARBOL) for (const s of seriesDe(fam)) out.push(s);
    return out;
  }

  /* ── estado de revisión ──────────────────────────────────── */

  const rev = (id) => REVISION[id] || null;
  const estadoDe = (id) => (rev(id) || {}).estado || "pendiente";

  function valor(serie, campo) {
    const r = rev(serie.id);
    return r && r.campos && campo in r.campos ? r.campos[campo] : (serie[campo] ?? "");
  }
  function cambiado(serie, campo) {
    const r = rev(serie.id);
    return !!(r && r.campos && campo in r.campos && r.campos[campo] !== (serie[campo] ?? ""));
  }

  function visible(serie) {
    if (filtro.estado && estadoDe(serie.id) !== filtro.estado) return false;
    if (filtro.fuente && (serie.fuente || "") !== filtro.fuente) return false;
    if (!filtro.q) return true;
    const q = filtro.q.toLowerCase();
    return (serie.label + " " + serie.id + " " + serie.desc + " " +
      (serie.datos || []).map((d) => d.base).join(" ")).toLowerCase().includes(q);
  }

  function conteo(lista) {
    const c = { total: 0, ok: 0, corregida: 0, problema: 0, pendiente: 0 };
    lista.forEach((s) => { c.total++; c[estadoDe(s.id)]++; });
    c.revisadas = c.ok + c.corregida + c.problema;
    return c;
  }

  /* ── render del árbol ────────────────────────────────────── */

  function filaSerie(s, clr, esTotal) {
    const est = estadoDe(s.id);
    const d = (s.datos || [])[0] || {};
    const freqs = (s.datos || []).map((x) => x.freq).join("+") || "—";
    const desc = valor(s, "desc");
    const marca = { pendiente: "sin revisar", ok: "revisada", corregida: "corregida", problema: "problema" }[est];
    return `<div class="serie e-${est}${esTotal ? " total" : ""}" data-id="${esc(s.id)}" role="button" tabindex="0">
      <span class="punto" style="background:${esc(clr)}"></span>
      <span class="lbl" title="${esc(valor(s, "label"))}">${esc(esTotal ? "Total" : valor(s, "label"))}</span>
      <span class="col" title="${esc(d.base || "")}">${esc(d.base || "—")}</span>
      <span class="col">${esc(d.ini || "—")}</span>
      <span class="col">${esc(d.fin || "—")}</span>
      <span class="col" title="${esc(FREQ[d.freq] || "")}">${esc(freqs)}</span>
      <span class="col">${esc(valor(s, "fuente") || "—")}</span>
      <span class="descripcion${desc ? "" : " falta"}">${esc(desc || "sin descripción")}</span>
      <span class="marca m-${est}">${marca}</span>
    </div>`;
  }

  function nodoSerie(s, clr) {
    if (s.hijos && s.hijos.length) {
      const visibles = [...conHijos(s)].filter(visible);
      if (!visibles.length) return "";
      const c = conteo([...conHijos(s)]);
      return `<div class="carpeta">
        <div class="carpeta-hd abierto"><span class="arr">▶</span>
          <span class="nom" style="color:${esc(clr)}">${esc(valor(s, "label"))}</span>
          <span class="pastilla">${c.revisadas}/${c.total}</span></div>
        <div class="carpeta-body abierto">
          ${visible(s) ? filaSerie(s, clr, true) + fichaSi(s, clr) : ""}
          ${s.hijos.map((h) => nodoSerie(h, clr)).join("")}
        </div></div>`;
    }
    return visible(s) ? filaSerie(s, clr, false) + fichaSi(s, clr) : "";
  }

  function fichaSi(s, clr) {
    return abierta === s.id ? ficha(s, clr) : "";
  }

  function nodoSub(sub, clr, nivel) {
    const lista = [...seriesDe(sub)];
    if (!lista.some(visible)) return "";
    const c = conteo(lista);
    const cuerpo = (sub.items || []).map((i) => nodoSerie(i, clr)).join("") +
      (sub.subs || []).map((x) => nodoSub(x, clr, nivel + 1)).join("");
    return `<div class="${nivel > 1 ? "sub2" : "sub"}">
      <div class="sub-hd abierto"><span class="arr">▶</span>
        <span class="nom">${esc(sub.sub)}</span>
        <span class="mini"><i style="width:${c.total ? Math.round(c.revisadas / c.total * 100) : 0}%"></i></span>
        <span class="pastilla">${c.revisadas}/${c.total}</span></div>
      <div class="sub-body abierto">${cuerpo}</div></div>`;
  }

  function pintar() {
    const app = document.getElementById("app");
    const global = conteo(todas());
    const pct = global.total ? Math.round(global.revisadas / global.total * 100) : 0;

    const grupos = ARBOL.map((fam) => {
      const lista = [...seriesDe(fam)];
      if (!lista.some(visible)) return "";
      const c = conteo(lista);
      return `<div class="grp">
        <div class="grp-hd abierto"><span class="arr">▶</span>
          <span class="nom" style="color:${esc(fam.clr)}">${esc(fam.grp)}</span>
          <span class="mini"><i style="width:${c.total ? Math.round(c.revisadas / c.total * 100) : 0}%"></i></span>
          <span class="pastilla">${c.revisadas}/${c.total} revisadas</span></div>
        <div class="grp-body abierto">
          <div class="encabezado-cols"><span></span><span>Serie</span><span>Base</span>
            <span>Origen</span><span>Final</span><span>Frec.</span><span>Fuente</span>
            <span>Descripción</span><span></span></div>
          ${(fam.subs || []).map((s) => nodoSub(s, fam.clr, 1)).join("")}
        </div></div>`;
    }).join("");

    app.innerHTML = `
      <header class="barra">
        <h1>Revisión del Catálogo</h1>
        <div class="progreso-global">
          <span class="barrita"><i style="width:${pct}%"></i></span>
          <span class="cifra">${global.revisadas} de ${global.total} · ${pct}%</span>
        </div>
        <div class="acciones">
          <button type="button" id="exportar">Copiar correcciones</button>
          <button type="button" id="guardar" class="primario" ${sucio ? "" : "disabled"}>
            ${sucio ? "Guardar" : "Guardado"}</button>
        </div>
      </header>
      <div class="filtros">
        <input id="q" type="search" placeholder="Buscar serie, id, archivo o descripción…"
               value="${esc(filtro.q)}" autocomplete="off">
        <select id="f-estado">
          <option value="">Todos los estados</option>
          <option value="pendiente">Sin revisar (${global.pendiente})</option>
          <option value="ok">Revisadas (${global.ok})</option>
          <option value="corregida">Corregidas (${global.corregida})</option>
          <option value="problema">Con problema (${global.problema})</option>
        </select>
        <select id="f-fuente"><option value="">Todas las fuentes</option>
          ${FUENTES.map((f) => `<option value="${esc(f)}">${esc(f)}</option>`).join("")}</select>
      </div>
      <div id="aviso"></div>
      <div class="arbol">${grupos || '<p class="vacio">Ninguna serie coincide con el filtro.</p>'}</div>`;

    document.getElementById("q").value = filtro.q;
    document.getElementById("f-estado").value = filtro.estado;
    document.getElementById("f-fuente").value = filtro.fuente;
    if (abierta) {
      const el = document.querySelector(`.serie[data-id="${CSS.escape(abierta)}"]`);
      if (el) el.classList.add("activa");
    }
  }

  /* ── ficha de edición ────────────────────────────────────── */

  function opciones(lista, elegido) {
    return ['<option value=""></option>'].concat(
      lista.map((v) => `<option value="${esc(v)}"${v === elegido ? " selected" : ""}>${esc(v)}</option>`)
    ).join("");
  }

  function campo(s, clave, tipo) {
    const v = valor(s, clave);
    const marca = cambiado(s, clave) ? " cambiado" : "";
    const original = cambiado(s, clave)
      ? `<span class="pista">antes: ${esc(s[clave] || "(vacío)")}</span>` : "";
    let control;
    if (tipo === "texto") {
      control = `<textarea data-campo="${clave}" rows="3">${esc(v)}</textarea>`;
    } else if (tipo === "magnitud") {
      control = `<select data-campo="mag">${opciones(Object.keys(VOCAB.magnitudes), v)}</select>`;
    } else if (tipo === "escala") {
      control = `<select data-campo="esc">${opciones(Object.keys(VOCAB.escalas), v)}</select>`;
    } else if (tipo === "moneda") {
      control = `<select data-campo="mon">${opciones(Object.keys(VOCAB.monedas), v)}</select>`;
    } else if (tipo === "fuente") {
      control = `<select data-campo="fuente">${opciones(FUENTES, v)}</select>`;
    } else {
      control = `<input data-campo="${clave}" value="${esc(v)}">`;
    }
    const ancho = (clave === "desc" || clave === "nota" || clave === "label") ? " ancho" : "";
    return `<div class="campo${ancho}${marca}"><label>${ROTULO[clave]}</label>${control}${original}</div>`;
  }

  function tablaDatos(s) {
    if (!(s.datos || []).length) {
      return '<p class="pista">Esta serie no apunta a ningún archivo: es un nodo agrupador.</p>';
    }
    const filas = s.datos.map((d) => `<tr>
      <td>${esc(FREQ[d.freq] || d.freq || "—")}</td>
      <td class="${d.existe ? "" : "falta"}">${esc(d.base || "—")}</td>
      <td>${esc(d.cv || "—")}</td>
      <td>${esc(d.ini || "—")}</td>
      <td>${esc(d.fin || "—")}</td>
      <td>${d.obs || 0}</td>
      <td>${esc(d.fuente || "—")}</td></tr>`).join("");
    return `<table class="datos-tabla"><thead><tr>
      <th>Frecuencia</th><th>Archivo</th><th>Columna</th><th>Origen</th>
      <th>Final</th><th>Obs.</th><th>Fuente</th></tr></thead><tbody>${filas}</tbody></table>`;
  }

  function ficha(s, clr) {
    const est = estadoDe(s.id);
    const ruta = s.id + (s.ext ? " · id en la fuente: " + s.ext : "") +
      (s.conf ? " · confianza: " + s.conf : "");
    return `<div class="ficha" data-ficha="${esc(s.id)}"><div class="ficha-caja">
      <h3 style="color:${esc(clr)}">${esc(valor(s, "label"))}</h3>
      <p class="ruta">${esc(ruta)}</p>
      <div class="campos">
        ${campo(s, "label")}
        ${campo(s, "desc", "texto")}
        ${campo(s, "fuente", "fuente")}
        ${campo(s, "mag", "magnitud")}
        ${campo(s, "esc", "escala")}
        ${campo(s, "mon", "moneda")}
        <div class="campo ancho"><label>Datos en disco (no editable: sale del archivo)</label>
          ${tablaDatos(s)}</div>
        ${campo(s, "nota", "texto")}
      </div>
      <div class="veredicto">
        <button type="button" data-e="ok" class="${est === "ok" ? "puesto" : ""}">Está bien</button>
        <button type="button" data-e="problema" class="${est === "problema" ? "puesto" : ""}">Tiene un problema</button>
        <button type="button" data-e="pendiente" class="${est === "pendiente" ? "puesto" : ""}">Dejar sin revisar</button>
        <button type="button" class="sig" data-sig="1">Siguiente sin revisar →</button>
      </div></div></div>`;
  }

  /* ── edición ─────────────────────────────────────────────── */

  function tocar(id, campo, valorNuevo) {
    const s = todas().find((x) => x.id === id);
    if (!s) return;
    const r = REVISION[id] || (REVISION[id] = { estado: "pendiente", campos: {} });
    r.campos = r.campos || {};
    if (valorNuevo === (s[campo] ?? "")) delete r.campos[campo];
    else r.campos[campo] = valorNuevo;
    const hayCambios = Object.keys(r.campos).length > 0;
    if (hayCambios && r.estado !== "problema") r.estado = "corregida";
    if (!hayCambios && r.estado === "corregida") r.estado = "ok";
    r.cuando = new Date().toISOString().slice(0, 10);
    sucio = true;
  }

  function marcar(id, estado) {
    const r = REVISION[id] || (REVISION[id] = { campos: {} });
    const tieneCambios = Object.keys(r.campos || {}).length > 0;
    r.estado = estado === "ok" && tieneCambios ? "corregida" : estado;
    r.cuando = new Date().toISOString().slice(0, 10);
    if (estado === "pendiente" && !tieneCambios) delete REVISION[id];
    sucio = true;
  }

  function siguientePendiente(desde) {
    const lista = todas().filter(visible);
    const i = lista.findIndex((s) => s.id === desde);
    for (let k = i + 1; k < lista.length; k++) {
      if (estadoDe(lista[k].id) === "pendiente") return lista[k].id;
    }
    return (lista.find((s) => estadoDe(s.id) === "pendiente") || {}).id || null;
  }

  /* ── guardado: se republica la página con el estado nuevo ─── */

  function documentoParaPublicar() {
    // Se clona el esqueleto y se le cambia SOLO el bloque de revisión. El contenedor
    // del render se vacía: la página se vuelve a dibujar sola al abrirse. Así no se
    // publica el DOM vivo, que arrastraría el estado de scroll, foco y colapsos.
    const clon = document.documentElement.cloneNode(true);
    const app = clon.querySelector("#app");
    if (app) app.innerHTML = "";
    clon.querySelector("#revision").textContent = JSON.stringify(REVISION);
    return "<!doctype html>\n" + clon.outerHTML;
  }

  function avisar(texto, clase) {
    const caja = document.getElementById("aviso");
    if (!caja) return;
    caja.innerHTML = `<p class="aviso ${clase}">${esc(texto)}</p>`;
    if (clase === "bueno") setTimeout(() => { caja.innerHTML = ""; }, 3000);
  }

  let guardando = false;
  async function guardar() {
    if (guardando || !sucio) return;
    guardando = true;
    const boton = document.getElementById("guardar");
    if (boton) { boton.textContent = "Guardando…"; boton.disabled = true; }
    try {
      const artifact = await window.claude?.use?.("artifact");
      if (!artifact) {
        avisar("Esta copia no puede guardar sola. Usá «Copiar correcciones» y pegámelas.", "malo");
        return;
      }
      await artifact.publish(documentoParaPublicar());
      sucio = false;
      avisar("Revisión guardada.", "bueno");
    } catch (e) {
      const conflicto = e && (e.code === "conflict" || /conflict/i.test(e.message || ""));
      avisar(conflicto
        ? "Alguien guardó antes que vos; la página se va a recargar con esa versión."
        : "No se pudo guardar. Copiá las correcciones para no perderlas.", "malo");
    } finally {
      guardando = false;
      pintar();
    }
  }

  function correccionesComoTexto() {
    const mapa = new Map(todas().map((s) => [s.id, s]));
    const filas = [["id", "estado", "campo", "antes", "ahora", "cuando"].join("\t")];
    Object.entries(REVISION).forEach(([id, r]) => {
      const s = mapa.get(id);
      const campos = Object.entries(r.campos || {});
      if (!campos.length) {
        filas.push([id, r.estado, "", "", "", r.cuando || ""].join("\t"));
        return;
      }
      campos.forEach(([c, v]) => filas.push([
        id, r.estado, c, String((s && s[c]) || "").replace(/\s+/g, " "),
        String(v).replace(/\s+/g, " "), r.cuando || ""
      ].join("\t")));
    });
    return filas.join("\n");
  }

  /* ── eventos ─────────────────────────────────────────────── */

  document.addEventListener("click", (ev) => {
    const cab = ev.target.closest(".grp-hd, .sub-hd, .carpeta-hd");
    if (cab) {
      cab.classList.toggle("abierto");
      const cuerpo = cab.nextElementSibling;
      if (cuerpo) cuerpo.classList.toggle("abierto");
      return;
    }
    const fila = ev.target.closest(".serie");
    if (fila) {
      abierta = abierta === fila.dataset.id ? null : fila.dataset.id;
      pintar();
      if (abierta) {
        const f = document.querySelector(`.ficha[data-ficha="${CSS.escape(abierta)}"]`);
        if (f) f.scrollIntoView({ block: "nearest", behavior: "smooth" });
      }
      return;
    }
    const veredicto = ev.target.closest(".veredicto button");
    if (veredicto && abierta) {
      if (veredicto.dataset.sig) {
        const sig = siguientePendiente(abierta);
        abierta = sig;
      } else {
        marcar(abierta, veredicto.dataset.e);
      }
      pintar();
      return;
    }
    if (ev.target.id === "guardar") { guardar(); return; }
    if (ev.target.id === "exportar") {
      const texto = correccionesComoTexto();
      const boton = ev.target;
      navigator.clipboard?.writeText(texto).then(
        () => { boton.textContent = "Copiado"; setTimeout(() => { boton.textContent = "Copiar correcciones"; }, 1800); },
        () => avisar("El navegador no dejó copiar. Guardá y pedime que lea la versión publicada.", "malo")
      );
    }
  });

  document.addEventListener("keydown", (ev) => {
    if (ev.target.closest(".serie") && (ev.key === "Enter" || ev.key === " ")) {
      ev.preventDefault();
      ev.target.closest(".serie").click();
    }
  });

  document.addEventListener("input", (ev) => {
    const t = ev.target;
    if (t.id === "q") { filtro.q = t.value; abierta = null; pintar(); return; }
    if (t.dataset && t.dataset.campo && abierta) {
      tocar(abierta, t.dataset.campo, t.value);
      const boton = document.getElementById("guardar");
      if (boton) { boton.disabled = false; boton.textContent = "Guardar"; }
      t.closest(".campo").classList.add("cambiado");
    }
  });

  document.addEventListener("change", (ev) => {
    const t = ev.target;
    if (t.id === "f-estado") { filtro.estado = t.value; abierta = null; pintar(); }
    if (t.id === "f-fuente") { filtro.fuente = t.value; abierta = null; pintar(); }
  });

  window.addEventListener("beforeunload", (ev) => {
    if (sucio) { ev.preventDefault(); ev.returnValue = ""; }
  });

  pintar();
})();
