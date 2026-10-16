/* Cuadro de series — filtrado, orden y ficha desplegable.
   DATOS viene embebido arriba: una entrada por serie × frecuencia. */
(function () {
  "use strict";

  var CLAVE = "cueva.cuadro.filtros";
  var FILTROS = [
    { campo: "fam", etiqueta: "Familia" },
    { campo: "fuente", etiqueta: "Fuente" },
    { campo: "frec", etiqueta: "Frecuencia" },
    { campo: "mag", etiqueta: "Magnitud" },
    { campo: "mon", etiqueta: "Moneda" },
    { campo: "est", etiqueta: "Estado" }
  ];
  var FRECUENCIA = { D: "Diaria", M: "Mensual", Q: "Trimestral", A: "Anual" };

  var estado = { q: "", orden: null, dir: "asc", abierta: null, sel: {} };

  var $q = document.getElementById("q");
  var $filtros = document.getElementById("filtros");
  var $cuerpo = document.getElementById("cuerpo");
  var $conteo = document.getElementById("conteo");
  var $vacio = document.getElementById("vacio");

  function esc(t) {
    return String(t == null ? "" : t).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  function guardar() {
    try {
      localStorage.setItem(CLAVE, JSON.stringify({ q: estado.q, sel: estado.sel }));
    } catch (e) { /* modo privado o storage bloqueado: seguimos sin recordar */ }
  }

  function recordar() {
    try {
      var guardado = JSON.parse(localStorage.getItem(CLAVE) || "{}");
      if (guardado.q) { estado.q = guardado.q; $q.value = guardado.q; }
      if (guardado.sel) { estado.sel = guardado.sel; }
    } catch (e) { /* sin memoria previa: arrancamos limpios */ }
  }

  function valores(campo) {
    var vistos = {};
    DATOS.forEach(function (d) { if (d[campo]) vistos[d[campo]] = true; });
    return Object.keys(vistos).sort(function (a, b) { return a.localeCompare(b, "es"); });
  }

  function construirFiltros() {
    FILTROS.forEach(function (f) {
      var lab = document.createElement("label");
      var span = document.createElement("span");
      span.textContent = f.etiqueta;
      var sel = document.createElement("select");
      sel.dataset.campo = f.campo;
      var todas = document.createElement("option");
      todas.value = "";
      todas.textContent = "Todas";
      sel.appendChild(todas);
      valores(f.campo).forEach(function (v) {
        var o = document.createElement("option");
        o.value = v;
        o.textContent = f.campo === "frec" ? (FRECUENCIA[v] || v) : v;
        sel.appendChild(o);
      });
      if (estado.sel[f.campo]) { sel.value = estado.sel[f.campo]; }
      sel.addEventListener("change", function () {
        estado.sel[f.campo] = sel.value;
        estado.abierta = null;
        guardar();
        pintar();
      });
      lab.appendChild(span);
      lab.appendChild(sel);
      $filtros.appendChild(lab);
    });
  }

  function filtradas() {
    var q = estado.q.trim().toLowerCase();
    var filas = DATOS.filter(function (d) {
      for (var campo in estado.sel) {
        if (estado.sel[campo] && d[campo] !== estado.sel[campo]) { return false; }
      }
      if (!q) { return true; }
      return (d.serie + " " + d.id + " " + d.base + " " + d.desc + " " + d.sub)
        .toLowerCase().indexOf(q) !== -1;
    });
    if (estado.orden) {
      var c = estado.orden, signo = estado.dir === "asc" ? 1 : -1;
      filas = filas.slice().sort(function (a, b) {
        var x = a[c] == null ? "" : a[c], y = b[c] == null ? "" : b[c];
        // Las vacías van siempre al final, ordene como ordene.
        if (x === "" && y !== "") { return 1; }
        if (y === "" && x !== "") { return -1; }
        return signo * String(x).localeCompare(String(y), "es", { numeric: true });
      });
    }
    return filas;
  }

  function fila(d, i) {
    return '<tr class="n-' + d.niv + '" data-i="' + i + '">' +
      '<td class="serie">' + esc(d.serie) + '<span class="id">' + esc(d.id) + '</span></td>' +
      '<td class="base" title="' + esc(d.base) + '">' + esc(d.base) + '</td>' +
      '<td class="fecha">' + esc(d.ini || "—") + '</td>' +
      '<td class="fecha">' + esc(d.fin || "—") + '</td>' +
      '<td class="frec" title="' + esc(FRECUENCIA[d.frec] || d.frec) + '">' + esc(d.frec) + '</td>' +
      '<td>' + esc(d.fuente) + '</td>' +
      '<td class="desc">' + esc(d.desc) + '</td>' +
      '<td>' + esc(d.mag) + '</td>' +
      '<td>' + esc(d.esc) + '</td>' +
      '<td class="mon">' + esc(d.mon || "—") + '</td>' +
      '</tr>';
  }

  function dato(rotulo, valor) {
    if (!valor && valor !== 0) { return ""; }
    return "<div><dt>" + esc(rotulo) + "</dt><dd>" + esc(valor) + "</dd></div>";
  }

  function ficha(d) {
    var unidad = [d.uni, d.baseidx, d.prec].filter(Boolean).join(" · ");
    return '<tr class="ficha"><td colspan="10"><div class="ficha-caja">' +
      "<h3>" + esc(d.serie) + "</h3>" +
      '<p class="ficha-ruta">' + esc(d.fam) + " › " + esc(d.sub) + "</p>" +
      '<p class="ficha-desc' + (d.desc ? "" : " falta") + '">' +
        esc(d.desc || "Esta serie todavía no tiene descripción escrita.") + "</p>" +
      '<dl class="ficha-grid">' +
        dato("Estado", d.est) +
        dato("Confianza", d.conf) +
        dato("Identificador", d.id) +
        dato("Archivo", d.base) +
        dato("Columna de fecha", d.cf) +
        dato("Columna de valor", d.cv) +
        dato("Observaciones", d.obs) +
        dato("Cobertura", d.ini ? d.ini + " → " + d.fin : "sin datos leídos") +
        dato("Frecuencia", FRECUENCIA[d.frec] || d.frec) +
        dato("Unidad declarada", unidad) +
        dato("Magnitud", d.mag) +
        dato("Escala", d.esc) +
        dato("Moneda", d.mon) +
        dato("Fuente", d.fuente) +
        dato("Id en la fuente", d.ext) +
      "</dl></div></td></tr>";
  }

  function pintar() {
    var filas = filtradas();
    var html = [];
    filas.forEach(function (d, i) {
      html.push(fila(d, i));
      if (estado.abierta === d.id + "|" + d.frec + "|" + d.base) { html.push(ficha(d)); }
    });
    $cuerpo.innerHTML = html.join("");
    $vacio.hidden = filas.length > 0;
    var total = DATOS.length;
    $conteo.textContent = filas.length === total
      ? total + " entradas"
      : filas.length + " de " + total;
    estado.ultimas = filas;
  }

  function alternarFicha(d) {
    var llave = d.id + "|" + d.frec + "|" + d.base;
    estado.abierta = estado.abierta === llave ? null : llave;
    pintar();
  }

  /* ── eventos ────────────────────────────────────────────── */

  $q.addEventListener("input", function () {
    estado.q = $q.value;
    estado.abierta = null;
    guardar();
    pintar();
  });

  $cuerpo.addEventListener("click", function (ev) {
    var tr = ev.target.closest("tr[data-i]");
    if (!tr) { return; }
    alternarFicha(estado.ultimas[Number(tr.dataset.i)]);
  });

  document.querySelectorAll("th.orden").forEach(function (th) {
    th.addEventListener("click", function () {
      var col = th.dataset.col;
      if (estado.orden === col) {
        estado.dir = estado.dir === "asc" ? "desc" : "asc";
      } else {
        estado.orden = col;
        estado.dir = "asc";
      }
      document.querySelectorAll("th[data-dir]").forEach(function (o) {
        o.removeAttribute("data-dir");
      });
      th.dataset.dir = estado.dir;
      estado.abierta = null;
      pintar();
    });
  });

  document.getElementById("limpiar").addEventListener("click", function () {
    estado.q = "";
    estado.sel = {};
    estado.orden = null;
    estado.abierta = null;
    $q.value = "";
    document.querySelectorAll(".filtros select").forEach(function (s) { s.value = ""; });
    document.querySelectorAll("th[data-dir]").forEach(function (o) {
      o.removeAttribute("data-dir");
    });
    guardar();
    pintar();
  });

  document.getElementById("copiar").addEventListener("click", function (ev) {
    var cols = ["serie", "id", "base", "ini", "fin", "frec", "fuente", "desc", "mag", "esc", "mon"];
    var rotulos = ["Serie", "Id", "Base", "Origen", "Final", "Frecuencia", "Fuente",
                   "Descripcion", "Magnitud", "Escala", "Moneda"];
    var lineas = [rotulos.join("\t")];
    (estado.ultimas || []).forEach(function (d) {
      lineas.push(cols.map(function (c) {
        return String(d[c] == null ? "" : d[c]).replace(/[\t\n\r]+/g, " ");
      }).join("\t"));
    });
    var boton = ev.currentTarget;
    var texto = lineas.join("\n");
    var listo = function () {
      boton.textContent = "Copiado";
      setTimeout(function () { boton.textContent = "Copiar filtrado"; }, 1600);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(texto).then(listo, function () {
        boton.textContent = "No se pudo copiar";
        setTimeout(function () { boton.textContent = "Copiar filtrado"; }, 2200);
      });
    } else {
      boton.textContent = "No se pudo copiar";
      setTimeout(function () { boton.textContent = "Copiar filtrado"; }, 2200);
    }
  });

  recordar();
  construirFiltros();
  pintar();
})();
