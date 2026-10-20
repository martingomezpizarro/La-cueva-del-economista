# Publicar el sitio — cuevadeleconomista.martingomezpizarro.com.ar

**Desde 2026-10-20 el dominio publica la plataforma unificada del mockup**: Línea de Tiempo +
Mesa de Trabajo (Explorar, Tests, Transformaciones con Kalman, Modelado con especificador e
iteración, Laboratorio con gráficos) en una sola página, `sitio/index.html`.

- Se regenera con `python scripts/unificar_mockup.py` (une `docs/mockup/mesa-de-trabajo.html`
  y la Línea de Tiempo de `docs/mockup/cueva-mockup.html`; escribe también
  `docs/mockup/cueva-unificada.html`).
- `.github/workflows/pages.yml` publica **solo la carpeta `sitio/`** en cada push a `main` que
  la toque. Nunca la raíz del repo: ahí están el corpus del RAG con derechos, los CSV y la
  configuración local. Con «Deploy from a branch» GitHub Pages publica todo el repo de forma
  pública aunque el repo sea privado; por eso la fuente tiene que ser «GitHub Actions».
- Requisito único en GitHub: **Settings → Pages → Build and deployment → Source: «GitHub
  Actions»**, y en «Custom domain» el dominio de arriba (pasos 2 a 7 de abajo).

La versión estática de la plataforma real (`scripts/construir_sitio.py`, opción B de abajo)
queda como alternativa para cuando las pantallas nuevas existan en `web/`.

---

## Opción B: versión estática de la plataforma real (en pausa)

## Cómo se arma

- `scripts/construir_sitio.py` → `_sitio/` (gitignorado). Congela `GET /api/v1/historia`,
  cada `GET /api/v1/historia/eventos/{id}` y `GET /api/v1/explorador/datos` como JSON, copia
  `web/` y `vendor/` e inyecta `web/estatico/estatico.js` en cada página: ese script traduce
  los `fetch` de la API a los JSON congelados. Las pantallas no se enteran de que no hay server.
- `.github/workflows/pages.yml` lo corre en cada push a `main` y publica.
- Probarlo en local: `python scripts/construir_sitio.py && python -m http.server -d _sitio 8000`.
- Las rutas son absolutas (`/web/…`): el sitio tiene que servirse en la RAÍZ de un dominio.
  En `usuario.github.io/La-cueva-del-economista/` (sin dominio propio) se rompe.

## Las series del explorador

No están en el repo: el explorador las lee de la carpeta del Trabajo Final de tu máquina.
Sin ellas el sitio publica el explorador vacío (con un aviso). Para publicarlas, **en la
máquina que tiene los datos**:

```bash
python scripts/construir_sitio.py --exportar-datos-explorador
git add data/publico/explorador_datos.json
git commit -m "Publicar series del explorador"
git push
```

Hay que repetirlo cada vez que se actualicen las series. ⚠ Antes de la primera vez, mirar en
`cueva/fuentes/registro.json` que cada organismo permita republicar sus datos.

## Paso a paso: dominio propio con HTTPS

**1. Llevar el cambio a `main`.** El workflow publica desde `main`: mergeá el PR de la
rama `ccr-4640c34c-xvlvli`.

**2. Activar Pages.** En GitHub, repo → **Settings → Pages → Build and deployment →
Source: «GitHub Actions»**. Después, en **Actions**, corré el workflow «pages» a mano (botón
**Run workflow**) o esperá al próximo push a `main`. Cuando termine en verde, el sitio ya
responde en `https://martingomezpizarro.github.io/La-cueva-del-economista/`. Las rutas
absolutas se rompen ahí, así que desde esa URL todavía no se ve bien.

**3. (Recomendado) Verificar el dominio.** Así nadie más puede apuntar un repo suyo a tu
dominio. Entrá a tu **foto de perfil → Settings → Pages → Add a domain** y escribí
`martingomezpizarro.com.ar`. GitHub te da un registro **TXT** con un nombre como
`_github-pages-challenge-martingomezpizarro` y un valor. Cargalo en tu DNS (paso 4) y
volvé a apretar **Verify**. Verificar el dominio raíz cubre todos sus subdominios.

**4. Crear el registro en el DNS.** Entrá al panel donde administrás la zona de
`martingomezpizarro.com.ar`. Es el proveedor al que apuntan los DNS delegados en NIC
Argentina: puede ser Cloudflare, DonWeb, Hostinger, el hosting de tu sitio actual, etc.
Creá este registro:

| Tipo | Nombre / Host | Valor / Destino | TTL |
|---|---|---|---|
| `CNAME` | `cuevadeleconomista` | `martingomezpizarro.github.io` | automático (o 3600) |

- El valor va **sin** el nombre del repo y sin `https://`. Algunos paneles piden un punto
  final (`martingomezpizarro.github.io.`).
- En «Nombre» va solo `cuevadeleconomista`: el panel le agrega el dominio solo. Si pedís el
  nombre completo, queda `cuevadeleconomista.martingomezpizarro.com.ar`.
- **Cloudflare**: dejá el registro en **«DNS only» (nube gris)** por lo menos hasta que
  GitHub emita el certificado. Con la nube naranja, GitHub no puede validar ni emitir el HTTPS.
- Si ya existía otro registro para `cuevadeleconomista` (un `A`, otro `CNAME`), borralo:
  no puede haber dos.

Para comprobarlo, desde una terminal: `nslookup cuevadeleconomista.martingomezpizarro.com.ar`
tiene que mostrar `martingomezpizarro.github.io`. Puede tardar de minutos a unas horas.

**5. Decirle a GitHub el dominio.** Repo → **Settings → Pages → Custom domain** → escribí
`cuevadeleconomista.martingomezpizarro.com.ar` → **Save**. Esperá el «DNS check successful».
Con el workflow de Actions, esta configuración es la que manda: el archivo `CNAME` del build
no alcanza solo.

**6. Activar HTTPS.** En esa misma pantalla, tildá **Enforce HTTPS**. Si la casilla está
gris, GitHub todavía está pidiendo el certificado a Let's Encrypt. Suele tardar entre unos
minutos y una hora, y a veces hasta 24 h. Si después de un día sigue gris: borrá el
dominio, guardá, volvé a cargarlo y guardá de nuevo; eso dispara otra emisión.

**7. Listo.** Abrí `https://cuevadeleconomista.martingomezpizarro.com.ar`: la Mesa en `/` y
la Línea de Tiempo en `/tiempo/`. La renovación del certificado es automática.

### Si algo falla

| Síntoma | Causa probable |
|---|---|
| «DNS check unsuccessful» | El CNAME todavía no se propagó, o está con la nube naranja de Cloudflare |
| 404 de GitHub en el dominio | Falta el paso 5, o el workflow «pages» no corrió en verde |
| La página abre sin estilos | Se está viendo desde `github.io/La-cueva-del-economista/`, no desde el dominio |
| El explorador abre vacío | Faltan las series: ver «Las series del explorador» |
| `NET::ERR_CERT_COMMON_NAME_INVALID` | El certificado todavía no se emitió (paso 6) |
