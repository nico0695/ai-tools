# 03 — Análisis de scripts para `log-assist`

> Planificación, no implementación. Fuentes: `docs/scripts-idea/` (corpus medido, **verdad operativa**) y `docs/idea/` (concepto, **no verdad**).
> Convención de citas: `SI/<archivo>:<línea>` = `docs/scripts-idea/`, `ID/<archivo>:<línea>` = `docs/idea/`.
> Todo lo que no está en esas fuentes va marcado **[propuesta]**.

---

## TL;DR

1. **Una sola CLI `loga`** con subcomandos, en **Python ≥3.11**, lanzada con `uv run` en los 3 SO. Núcleo **stdlib-only** en v1 (sin Drain3, sin PyYAML); `uv` se usa como lanzador y proveedor de Python, no por las deps **[propuesta; ajusta ID/02-ARCHITECTURE.md:253-260]**.
2. El formato Dex Player es uniforme (178.415/178.415 líneas parsean, SI/01-LECTURA-BASE.md:10). Eso permite un **parser único + catálogo declarativo**; el descubrimiento con Drain3 queda para después.
3. Las trampas del corpus (reinicios por `Dex Player <ver>`, banner 53 vs sync 54 `=`, stack traces como ERROR, umbrales por plataforma, ruido que vale por ausencia) se codifican **una vez en el `profile`**, no en cada comando.
4. **Extensibilidad en 3 ejes**: patrones/bugs → archivos TOML en `catalog/` (sin código); consultas nuevas → plugin `loga_commands/<name>.py` con `SPEC` autodescubierto; formatos nuevos → `profiles/<name>/profile.toml` que normaliza a un `Event` común.
5. **Contrato de salida**: markdown compacto al agente + envelope JSON de una línea (`returned/total/truncated/next`), tope por caracteres, citas `path:line` 1-based sobre bytes `\n`, exit codes sin la semántica de `grep` (0 = ok aunque no haya matches).
6. **Persistencia**: `manifest.json` + `runs.ndjson` (bitácora) en la carpeta del análisis; resultados completos solo con `--save`. La paginación se resuelve re-ejecutando (determinístico), no con cursores a disco **[propuesta; difiere de ID/02-ARCHITECTURE.md:513]**.
7. **Set v1 (13 subcomandos)**: `doctor`, `scan`, `sessions`, `summary`, `grep`, `window`, `resources`, `cluster`, `gaps`, `check`, `compare`, `verify-citations`, `index`.
8. **Sin evals**, pero con `loga selftest` **opcional**: cada patrón trae `examples`/`counter_examples` que se validan solos; fixtures mínimos por firma, opcionales.
9. **Índice generado** desde `SPEC` + catálogo (`loga index`), más una skill `log-scripts` con tabla de ruteo síntoma → comando curada a mano.
10. Lo que más cambia el diseño y hay que preguntar: si `uv` se puede instalar en las PC Windows de QA, quién agrega casos (QA o Dev), si menuboard entra en v1 y cuánto pesan los logs reales.

---

## 1. Qué dice el corpus: invariantes y trampas a codificar

| # | Hecho / trampa | Consecuencia para los scripts | Cita |
|---|---|---|---|
| 1 | Línea = `YYYY-MM-DD HH:MM:SS.cc NIVEL message`, 2 decimales siempre, 5 niveles (`WARNING`, no `WARN`) | Un único `line_regex` en el profile; `parse_rate` debería ser ~1.0 y, si baja, avisar | SI/01-LECTURA-BASE.md:10,22,45 |
| 2 | Componente `[X]` con subcomponente opcional `[X] [Y]` | `Event.component` + `Event.sub`; los patrones filtran por componente antes de aplicar la regex | SI/01-LECTURA-BASE.md:30-33 |
| 3 | Las regex del corpus usan `(?<name>)` (sintaxis PCRE/JS) y en tablas escapan `\|` | Python necesita `(?P<name>)`: normalizar al cargar el catálogo; nunca copiar desde tablas markdown | SI/01-LECTURA-BASE.md:22, SI/README.md:81 |
| 4 | La identidad autoritativa es `Machine:` y no el nombre del archivo; `Platform`, versión, `Group:` y tags salen de líneas concretas | `scan` extrae la identidad del contenido; el nombre del archivo es solo una pista (rol `MASTER`, fecha) | SI/01-LECTURA-BASE.md:51-62 |
| 5 | Archivos `(1)` son **otras pantallas**, no duplicados | Prohibido deduplicar por nombre; agrupar por `Machine` | SI/01-LECTURA-BASE.md:144-151, SI/12-PENDIENTES.md:25 |
| 6 | Sin zona horaria; saltos hacia atrás en reinicios; hueco ≠ falla (puede ser política) | Orden por (`file`, `line`) y no por `ts`; comparaciones entre pantallas marcadas `clock: naive`; `gaps` cruza con estado de display | SI/01-LECTURA-BASE.md:78-81, SI/12-PENDIENTES.md:50, SI/10-PANTALLA-politicas-screenshots.md:30 |
| 7 | **Contar arranques con `^Dex Player [\d.]+$`**; banner 53 `=` vs bloque sync 54 `=` (inflación 404 %) | `boot_marker` en el profile; el delimitador `={54}` es de `cluster` | SI/01-LECTURA-BASE.md:105-119, SI/02-GENERAL-sesiones-reinicios.md:22-27 |
| 8 | Cada arranque abre sesión; los contadores se leen por sesión, no por archivo | `session_id` como columna de primera clase en todo `Event` | SI/02-GENERAL-sesiones-reinicios.md:29 |
| 9 | Stack traces (`^\s+at\s`) son el 20 % de ERROR y no son eventos; hay errores benignos que dependen del contexto (Dir failed al boot en Tizen, CPU 98 % los primeros 30 s) | `continuation` pliega las líneas al evento anterior; reglas `benign_if` con ventana relativa al boot | SI/01-LECTURA-BASE.md:128-138 |
| 10 | Telemetría: única línea `CPU/RAM`; cadencia 300 s webOS / 60 s Tizen; RAM 1.064–1.288 vs 648–885 Mb | Parámetros **por plataforma** en el profile; la cadencia sirve para detectar la plataforma y los huecos | SI/03-GENERAL-recursos.md:11,24-29, SI/11-CATALOGO.md:91-94 |
| 11 | Pantalla negra = cascada F7 de 5 líneas en ~100 ms que termina en `Clearing current playlist` tras ERROR; `Playlist stopped` es normal | Se necesita la primitiva `sequence within` en las firmas, no un match suelto | SI/README.md:18, SI/11-CATALOGO.md:34,73, SI/12-PENDIENTES.md:16 |
| 12 | Split-brain = más de un `[Master]` en `Members:`; el intervalo PLAY es la duración del medio (falso positivo); enum de estado abierto; `Playlist: undefined` existe | `cluster` parsea `Members:` de forma tolerante; nunca usa la tasa de PLAY | SI/README.md:20-22, SI/07-SYNC-cluster.md:27, SI/12-PENDIENTES.md:15,19-20 |
| 13 | `Heartbeat Sync failed` lo emite `[Server Manager]`: es el servidor, no el sync | La clasificación de dominio sale del componente, no de palabras del texto | SI/07-SYNC-cluster.md:14-18, SI/12-PENDIENTES.md:14 |
| 14 | El 60 % del volumen son 20 mensajes; "ocultar ≠ no contar"; `Webos Storage Manager` existe solo en webOS | El ruido se **oculta en la vista pero se cuenta**; las reglas de ausencia declaran `platforms` | SI/06-GENERAL-ruido.md:10,30, SI/09-STORAGE-archivos.md:16 |
| 15 | Los umbrales de producto no existen (RAM/CPU, pendiente de fuga, "reiterado", precedencia de patrones solapados); timeouts siempre de 50.000 ms; Android sin verificar | Los scripts **miden y comparan contra el rango observado**; sin umbral configurado no dan veredicto. Conteos por patrón no sumables. Plataforma desconocida degrada con aviso | SI/11-CATALOGO.md:95,106, SI/12-PENDIENTES.md:35-42,55 |

Notas de consistencia entre fuentes:
- ID/03-SKILLS-AGENTS-SCRIPTS.md:309 afirma que las líneas `1969-/1970-` son arranque normal. **No figura en el corpus** (SI/01-LECTURA-BASE.md:10). A validar.
- La doc concepto habla de `case`, `history/<id>/` y `logharness` (ID/02-ARCHITECTURE.md:1, ID/03-SKILLS-AGENTS-SCRIPTS.md:278). El pedido actual habla de "carpeta del análisis" y `log-assist`, así que hay que alinear la nomenclatura (ver §9).
- Los scripts de medición del corpus (`profile.py`, `flows.py`, etc., SI/12-PENDIENTES.md:96-100) **no están en el repo**. Son un buen punto de partida si el usuario los tiene.

---

## 2. Mapa de familias

Leyenda: **G** = general (cualquier log), **E** = específica de un subsistema. Prioridad: **MVP** / **después**. Los nombres de comando son **[propuesta]**.

| Familia | Pregunta que responde | Inputs | Output | G/E | Plataforma | Comando(s) | Prioridad |
|---|---|---|---|---|---|---|---|
| Lectura base / ingesta | ¿Qué archivos hay, de qué pantalla, qué rango, parsean? | carpeta o archivos | manifest: `file, machine, platform, player_ver, sync_ver, group, tags, first_ts, last_ts, lines, parse_rate, boots, levels` | G | detecta | `scan` | MVP |
| Sesiones / reinicios | ¿Cuántas veces arrancó? ¿Programado (countdown) o inesperado? ¿≥3 por día? ¿Uptime? | archivos, `--per day` | tabla de sesiones `session, start, end, dur, prev_countdown, kind, ref` | G | — | `sessions` | MVP |
| Recursos | ¿Escala la RAM? ¿CPU saturada fuera del pico de arranque? ¿Faltan muestras? | archivos, `--session` | stats por sesión `min/max/p50/slope_mb_h/samples/expected/gaps`, sin serie cruda salvo `--series` | G (parametrizada por plataforma) | umbrales y cadencia | `resources` | MVP |
| Contenido / playlists | ¿Qué playlist hay, cuándo cambió, hubo negro? | archivos | timeline `ts, playlist, version_ts, event, ref` | G | — | `playback` | después (el negro sale en v1 vía `check`) |
| Red / servidor | ¿Handshake OK por sesión? ¿Rachas de heartbeat fallido? ¿Timeouts? | archivos | `sessions × {handshake, hb_ok, hb_fail, max_fail_streak, timeouts}` | G | — | `network` | después (en v1 vía `check` + `gaps`) |
| Ruido | ¿Cuáles son las líneas que importan? | cualquier consulta | no es un comando: es una **etapa** (`--noise hide|group|show`) sobre `grep/summary/window` | G | reglas por plataforma | flag común | MVP (como etapa) |
| Resumen / formas | ¿Qué pasa en general? ¿Qué ERROR/WARNING hay y cuántos, incluso fuera del catálogo? | archivos, `--level` | `shape_id, level, component, count, sessions, first, last, example_ref`; marca `known: <pattern_id>` | G | — | `summary` | MVP (masking stdlib) · Drain3 después |
| Sync / cluster | ¿Quién es master? ¿Split-brain? ¿Miembros inactivos? ¿Misma playlist? | 1..N archivos | snapshots `ts, group, members, masters, inactive, playlists_distintas, ref` | E | — | `cluster` | MVP (caso nombrado por el usuario) |
| Templates / menuboard | ¿Carga el template? ¿Hay fetch de precios? | archivos | ciclos de template, fetches por bucket | E | — | `menuboard` | después (salvo que sea criterio de aceptación, ID/03-SKILLS-AGENTS-SCRIPTS.md:446-447) |
| Storage | ¿Faltan archivos? ¿JSON corrupto? ¿Descargas? | archivos | `missing/failed` agrupado por path enmascarado | E | webOS ≠ Tizen | `storage` | después (JSON corrupto entra en la firma F7) |
| Pantalla / políticas | ¿Apagada por política o por falla? ¿Screenshots? | archivos | timeline `ON/OFF`, screenshots por intervalo | E | — | `display` | después (v1: `gaps` consulta el estado de display) |
| Cross-log | ¿Qué diferencia hay entre pantallas o archivos? ¿Qué pasó en todos a la vez? | N archivos agrupados por `machine`/`group` | `compare`: matriz pantalla × métrica; `window`: merge por ts con `clock: naive` | G | — | `compare`, `window` | MVP |
| Ausencia / cadencia | ¿Qué debería pasar cada X y no pasó? | regla (`expect`, `every`/`per`, `scope`) o id del catálogo | `bucket, expected, observed, verdict, gap_refs` | G (primitiva) | reglas con `platforms` | `gaps` | MVP (ID/02-ARCHITECTURE.md:472) |
| Firmas / bugs conocidos | ¿Matchea algún patrón conocido? | catálogo de firmas aplicables al profile y plataforma | `signature, verdict(hit/miss/n.a.), count, first_ref, evidence_refs` | G + E | filtrado | `check` | MVP |
| Búsqueda / ventana | Dame las líneas X / el contexto de T | `--pattern ID` o `--regex`, `--at ts` o `--ref f:l` | líneas literales con `ref`, paginadas | G | — | `grep`, `window` | MVP |
| Verificación de citas | ¿Existen las `archivo:línea` del informe y coincide el extracto? | un `.md` | `ok/fail` por cita, exit ≠ 0 si falla alguna | G | — | `verify-citations` | MVP (ID/03-SKILLS-AGENTS-SCRIPTS.md:342) |
| Estado / índice | ¿Qué se corrió ya? ¿Qué comandos y patrones existen? | carpeta del análisis | `status` (derivado de manifest + runs) / `index` (catálogo de comandos) | G | — | `index` MVP · `status` después | mixto |
| Entorno | ¿Anda el runtime en esta máquina? | — | `OK/FALTA/OPCIONAL` | — | Windows sobre todo | `doctor` | MVP (ID/03-SKILLS-AGENTS-SCRIPTS.md:285) |

Dependencias entre familias **[propuesta]**: todo pasa por `scan → Event stream (profile) → noise stage → comando`. `sessions` alimenta a `resources`, `gaps`, `check` (ventanas relativas al boot) y `compare`. `cluster` reusa `compare` para el cruce entre miembros.

---

## 3. Runtime cross-OS

| Criterio | (a) Python stdlib-only | (b) Python + uv + PEP 723 con deps | (c) Node | (d) Go compilado | (e) bash + PowerShell |
|---|---|---|---|---|---|
| Fricción en Windows para QA | Media: hay que instalar Python (Store o python.org, marcar PATH). **Con `uv` como lanzador pasa a baja**: `uv` baja Python solo | Baja-media: 1 comando (`winget install astral-sh.uv`, ID/02-ARCHITECTURE.md:249); la primera corrida baja deps de PyPI (proxy corporativo) | Media: instalar Node; `node_modules` o bundle | **Mínima**: copiar un `.exe` (pero SmartScreen, antivirus, Gatekeeper en Mac) | Nula para instalar, alta para usar (ExecutionPolicy, PS 5.1 vs 7) |
| Determinismo | Alto (con `re.ASCII`, orden estable, sin locale) | Alto; Drain3 depende del orden de entrada pero es reproducible con config fija | Alto | Alto (RE2, sin backtracking) | Bajo: dos implementaciones divergen (ID/02-ARCHITECTURE.md:248) |
| Dependencias | 0 | drain3, pyyaml, orjson (ID/02-ARCHITECTURE.md:259) | npm | 0 en runtime, toolchain en build | 0 |
| Mantenimiento | 1 código, legible por Ops/Dev | 1 código + lock implícito de deps | 1 código; el ecosistema de log mining es pobre (ID/02-ARCHITECTURE.md:250) | 1 código + pipeline de build y release × 3 SO × arch | **Doble**, con divergencia garantizada |
| Extensión | Plugins `.py` + catálogo TOML (`tomllib`) sin build | Igual + YAML | Plugins JS + JSON/YAML; regex `(?<name>)` nativa, igual que el corpus | Catálogo sí; **consultas nuevas requieren recompilar y redistribuir** | Cada caso se escribe dos veces |
| Regex del corpus | Convertir `(?<n>)` → `(?P<n>)` al cargar | Igual | Directa | Go ≥1.22 acepta `(?<n>)`; sin lookbehind | Dialectos distintos |

**Recomendación: (a) dentro de (b).** Código **stdlib-only** con cabecera PEP 723 (`requires-python = ">=3.11"`, `dependencies = []`) y **`uv run` como forma canónica de invocación**. **[propuesta]**
- Por qué: el formato es uniforme y el vocabulario es chico (573 formas, SI/01-LECTURA-BASE.md:157), así que en v1 no hace falta Drain3. Además `tomllib` (3.11) cubre el catálogo sin PyYAML y el mismo código corre con un `python` pelado si `uv` está bloqueado: son dos caminos de arranque y ninguno se rompe (RNF de ID/02-ARCHITECTURE.md:263-265).
- Deps opcionales: cuando entre Drain3 (familia `summary` en su modo de descubrimiento), va como **import perezoso con fallback** al masking stdlib. `rg`/`duckdb` no se usan en v1.
- Go se reconsidera solo si aparecen logs de varios GB (ID/02-ARCHITECTURE.md:251). El corpus actual es de 178k líneas y cabe en segundos.

**Queda por validar con el usuario:** (1) si `winget`/el script de `uv` está permitido en las PC de QA y si hay proxy hacia PyPI y GitHub; (2) si alcanza con un Python preinstalado; (3) si Claude Code en Windows corre sobre Git Bash o PowerShell, y Codex sobre PowerShell (afecta el quoting, §4).

---

## 4. Forma de la CLI

**Una CLI única `loga` con subcomandos** (coincide con ID/03-SKILLS-AGENTS-SCRIPTS.md:277). Scripts sueltos descartados porque multiplican el parseo de args, el envelope, el encoding y la documentación, y son justamente las piezas que tienen que ser idénticas.

Layout **[propuesta]**:
```
harness/log-assist/scripts/
  loga.py                  # entrypoint PEP 723, delgado: arma sys.path y delega
  loga_core/               # io, profile loader, Event, noise, envelope, render, refs
  loga_commands/<name>.py  # un comando = un archivo con SPEC + run(ctx)
  profiles/dex-player/profile.toml, platforms/{webos,tizen}.toml
  catalog/patterns/<DOMAIN>.toml, catalog/signatures/<slug>.toml, catalog/noise.toml
  catalog/_templates/      # plantillas para quien agrega casos
  INDEX.md                 # generado por `loga index --write`
```
(El paquete no puede llamarse `loga/` junto a `loga.py` porque se pisan los imports.)

**Invocación canónica, idéntica en Claude y Codex, Unix y Windows:**
```
uv run harness/log-assist/scripts/loga.py <cmd> [args]      # desde la raíz del repo
python harness/log-assist/scripts/loga.py <cmd> [args]      # fallback sin uv
```

| Tema | Regla **[propuesta]** |
|---|---|
| Shebang | No depender de él. `#!/usr/bin/env -S uv run --script` (ID/02-ARCHITECTURE.md:256) no existe en Windows y `env -S` falla en coreutils viejos. Se deja como comodidad Unix |
| Paths en args | Relativos y con `/`; Python y `uv` los aceptan en PowerShell, cmd y Git Bash. Evitar paths absolutos `/c/...` porque Git Bash los reescribe (conversión MSYS) |
| Paths en salida | Siempre POSIX, relativos a la raíz del análisis (`logs/20260222-0 (1).log:1234`). Nunca `C:\` (el `:` del drive rompe el parseo de citas) |
| Nombres con espacios y `()` | Son la norma en el corpus (SI/01-LECTURA-BASE.md:70-72). El agente pasa **alias del manifest** (`--file F3`) o globs internos (`--files 'logs/*'`), así no hay que citar paths en el shell |
| Regex en args | `$`, `|` y comillas se interpretan distinto en bash y PowerShell. Preferir `--pattern SYS.BOOT` (id de catálogo); para regex ad-hoc usar comillas simples (literales en ambos) o `--regex-file` |
| Pipes y utilidades | La skill **no** usa `| head`, `2>&1`, `grep` ni `sed`: todo filtro es un flag (`--limit`, `--level`, `--since`). Así el comando es el mismo en PowerShell |
| Encoding de salida | `sys.stdout.reconfigure(encoding="utf-8", errors="replace", newline="\n")` al inicio: sin esto la consola cp1252 rompe con `ñ` o nombres de playlist y Windows convierte `\n` a `\r\n` |
| Encoding de entrada | Leer en **binario**, partir por `\n`, quitar `\r` final y decodificar `utf-8` con `errors="replace"` (y BOM). No usar el modo universal newlines porque partiría en `\r` sueltos y los números de línea dejarían de coincidir con editores y `rg` |
| Help | `loga <cmd> --help` corto; `loga index` es la ayuda para el agente (§7) |

---

## 5. Contrato de salida

**Formato por defecto al agente: markdown compacto + envelope JSON en la primera línea.** Sigue a ID/02-ARCHITECTURE.md:513-515 (tabla markdown al contexto, JSON solo para metadatos) y agrega un envelope fijo **[propuesta]**:

```
loga {"cmd":"sessions","ok":true,"returned":6,"total":6,"truncated":false,"profile":"dex-player","files":2,"warnings":[],"next":["loga resources --session S3"]}
| session | file | start | end | dur | kind | ref |
|---|---|---|---|---|---|---|
| S1 | F1 | 2026-02-22 06:01:10 | 2026-02-22 11:10:40 | 5h09m | first | logs/20260222-0.log:1 |
...
F1 = logs/20260222-0.log
```

| Aspecto | Decisión **[propuesta]** | Justificación |
|---|---|---|
| Formatos | `--format md` (default), `json` (un objeto: envelope + `items`), `ndjson` (envelope y luego un item por línea) | `md` ahorra tokens (ID/02-ARCHITECTURE.md:514); `json` para encadenar; `ndjson` para `--save` |
| Límite | Tope por **caracteres** (tokens no es determinístico sin tokenizer): default `--max-chars 12000` (~3–4k tokens), techo duro 60000 (bajo el tope de ~25k tokens de ID/03-SKILLS-AGENTS-SCRIPTS.md:330). `--limit` de filas con default por comando | Presupuestos alineados con los niveles de ID/02-ARCHITECTURE.md:482-486 |
| Truncado | Nunca silencioso: `truncated:true`, `total` real y `next` con el comando exacto para seguir (`--offset N`). Líneas largas cortadas a 300 caracteres con `…[+N chars]` | "Un agente que recibe 20 de 3.187 sin saberlo concluye algo falso" (ID/02-ARCHITECTURE.md:522-528) |
| Citas | `ref` = `<path POSIX relativo>:<línea 1-based>`. En tablas se usa el alias `F<n>` con leyenda al pie cuando hay >1 archivo; `verify-citations` acepta las dos formas | Exactitud y ahorro de tokens; el alias sale del manifest, que es estable |
| Ruido | Siempre informar lo oculto: `hidden: {NOISE.READ_OP: 17872}` en el envelope | "Ocultar ≠ no contar" (SI/06-GENERAL-ruido.md:30) |
| Veredictos | `hit / miss / not_applicable / insufficient_data`; sin umbral configurado → `measured` + rango observado, nunca "fuga" | SI/12-PENDIENTES.md:35-38 |
| Exit codes | `0` ok (incluye 0 resultados) · `2` uso/args · `3` input (archivo inexistente, profile no detectado) · `4` ok parcial (algún archivo con `parse_rate` < 0,95 o ilegible; igual devuelve salida) · `5` verificación fallida (`verify-citations`, `selftest`) · `1` bug interno con traza corta en stderr | Evitar la semántica de `grep` (1 = sin match), que los agentes leen como error |
| stderr | Solo diagnóstico humano; el agente decide con stdout + exit code | — |
| Determinismo | Orden estable (`file alias, line`), sin timestamps de ejecución en stdout, `re.ASCII`, sin dependencia de locale ni TZ del host, aliases por orden lexicográfico de path, `run_id` = hash(args + fingerprint de inputs) | Misma entrada, mismos bytes de salida: permite re-ejecutar en vez de cachear |

**¿Persistir las salidas crudas?** Recomendación **[propuesta]**:
- **Sí** a `<analysis>/.loga/manifest.json` (chico, estable, fuente de los aliases) y a `.loga/runs.ndjson` (append: `run_id, cmd, args, envelope, input_fingerprint`). Sirven de bitácora y de base para un `status` futuro.
- **Resultados completos solo con `--save`** (`.loga/runs/<run_id>.ndjson`). Como la salida es determinística, paginar = re-ejecutar con `--offset`. Esto evita el crecimiento de `.work/` que propone ID/02-ARCHITECTURE.md:513 y la invalidación de cursores si cambian los logs.
- Si los logs reales llegan a varios GB, se invierte: persistir siempre e indexar (pregunta §9).

---

## 6. Extensibilidad

### 6.1 Modelo en capas **[propuesta]**

```
profile (formato)  →  Event normalizado  →  catalog (patterns, noise, signatures)  →  commands (plugins)
```
`Event = {file, line, ts, cs, level, component, sub, text, session, continuation_of}`. **Ningún comando lee texto crudo**: consume `Event` y los ids del catálogo. Eso aísla los tres ejes.

### 6.2 Opciones evaluadas

| Eje | Opción | Pros | Contras | v1 |
|---|---|---|---|---|
| (a) Patrones / bugs conocidos | **Catálogo declarativo TOML** | Sin código; revisable en PR; regex en literal `'...'` sin escapes; `tomllib` stdlib | Techo expresivo: lo que no entra en las primitivas requiere código | ✅ |
| | YAML (como ID/03-SKILLS-AGENTS-SCRIPTS.md:457-478) | Familiar; multi-idioma cómodo | Necesita PyYAML; los escapes de regex en YAML son traicioneros (`\d` en comillas dobles) | alternativa si el usuario lo prefiere |
| | JSON | stdlib | Dobles backslashes en cada regex: ilegible para QA/Ops | ❌ |
| | Código Python por patrón | Máxima expresividad | Cada bug nuevo requiere un dev; difícil de auditar | solo como escape |
| (b) Consultas nuevas | **Plugin por carpeta** `loga_commands/*.py` con `SPEC` + `run(ctx)`, descubierto con `pkgutil` en orden alfabético | Agregar = crear un archivo; el índice se autogenera | Requiere Python | ✅ |
| | Entry points (`pyproject`) | Estándar | Requiere instalar el paquete; más fricción | ❌ v1 |
| (c) Formatos nuevos | **Registry de `profiles/<name>/profile.toml`** + overlays por plataforma | Otro player u otro formato = otro directorio; detección por sniff | Formatos no lineales (JSON logs, multiline complejo) necesitan `parser = "module:fn"` en Python | ✅ con escape a código |

### 6.3 Qué contiene cada pieza **[propuesta]**

**`profile.toml`**: `name`, `detect` (regex de sniff sobre las primeras N líneas + `min_parse_rate`), `line_regex`, `ts_format`, `levels`, `component_regex`, `continuation` (`^\s+at\s`), `session.boot_marker` (`^Dex Player (?P<version>[\d.]+)$`), `identity.*` (Machine, Platform, versiones, Group, tags), `platform_detect` (línea `Platform` y, si falta, cadencia de telemetría) y `encoding`. `platforms/webos.toml` y `tizen.toml` agregan `telemetry_every`, `ram_observed_range`, `benign` (p. ej. `Dir failed` al arranque en Tizen) y reglas de ausencia válidas solo ahí.

**`catalog/patterns/<DOMAIN>.toml`** (una entrada por patrón):

| Campo | Ejemplo / nota |
|---|---|
| `id` | `SYS.BOOT`, `SYNC.MEMBERS`, `NET.HB_FAIL` (dominios de SI/11-CATALOGO.md:11-20) |
| `component`, `level`, `regex` | la regex se aplica sobre `text` (SI/README.md:80) |
| `captures` | nombres y tipos (`int`, `float`, `str`) |
| `signal` | `critical | milestone | noise | context` (SI/11-CATALOGO.md:28-57) |
| `scope`, `platforms`, `profiles` | `general`/`specific`; `[webos]` |
| `noise` | `hide | group | never_hide` |
| `examples`, `counter_examples` | líneas enmascaradas: **son el test** |
| `source` | `SI/07-SYNC-cluster.md:27` |
| `since`, `status` | `draft | verified` |

**`catalog/signatures/<slug>.toml`** (bugs/casos conocidos) combina patrones con **primitivas cerradas**: `match`, `count >= N per <window>`, `sequence [A,B,C] within <ms>`, `absence expect X every <dur> | per <bucket>`, `streak X >= N`, `field_count(capture, value) > N` (split-brain), con `requires_all`, `not_if` (descartes), `platforms`, `severity`, `symptoms.es/en` (ID/03-SKILLS-AGENTS-SCRIPTS.md:472-474), `playbook` y `evidence` (qué `refs` devolver). Ejemplos v1: `black-screen-json-cascade` (F7), `restart-loop` (≥3 boots/día), `split-brain`, `cluster-no-master`, `server-heartbeat-outage` (F10), `missing-content`, `node-server-down`. Una firma que no entra en las primitivas declara `impl = "loga_commands.cluster:detect_x"`.

**`SPEC` de un comando**: `name, family, question, when_to_use, not_for, args, output_columns, typical_size, profiles, requires_patterns, next_hints, since, stability`.

### 6.4 Qué necesita quien agrega un caso **[propuesta]**

1. Copiar `catalog/_templates/signature.toml` (o `pattern.toml`, `command.py`, `profile.toml`).
2. Completar `examples` y `counter_examples` con líneas reales **enmascaradas** (`<IP>`, `<RUTA>`, SI/README.md:82).
3. Correr `loga selftest --only <id>` y `loga index --write`.
4. Checklist corto en `scripts/CONTRIBUTING.md`: una trampa, un ejemplo, qué **no** es el patrón (rama que invalida, ID/03-SKILLS-AGENTS-SCRIPTS.md:415-416).

### 6.5 No romper lo existente sin evals (todo **opcional**)

| Mecanismo | Qué atrapa | Costo |
|---|---|---|
| `loga selftest` (schema + compilación de regex + `examples` matchean y `counter_examples` no) | Regex rota, colisión banner/sync, `\|` copiado de tablas | Casi nulo; corre en <1 s |
| Unicidad de ids + detección de solapamientos (una línea de ejemplo matchea 2 patrones del mismo dominio → warning) | Doble conteo (SI/12-PENDIENTES.md:39) | Bajo |
| `loga index --check` (INDEX.md coincide con lo generado) | Índice desactualizado frente al código | Nulo |
| Fixtures mínimos por firma `fixtures/<slug>.log` (10–30 líneas) + salida esperada | Regresión de la lógica de primitivas | Medio; **opcional**, solo para firmas críticas |
| Golden de `scan` sobre un fixture por profile/plataforma | Cambios en parser/identidad | Medio; opcional |

---

## 7. Índice de scripts y skill asociada

**Catálogo generado + ruteo curado a mano** **[propuesta]**:
- `loga index` imprime (y `--write` guarda en `scripts/INDEX.md`) una entrada por comando desde `SPEC`, más el listado de patrones y firmas desde el catálogo. Nunca se edita a mano.
- La skill **`log-scripts`** (nombre tentativo) tiene un `SKILL.md` **estático y corto**: (1) la invocación canónica y las reglas de §4, (2) cómo leer el envelope y los exit codes, (3) la **tabla de ruteo síntoma → comando** (curada, derivada de SI/README.md:63-74), (4) "para la lista viva, correr `loga index`". Así la skill no se desactualiza al agregar comandos y el costo de contexto queda fijo, que es el mismo principio de ID/03-SKILLS-AGENTS-SCRIPTS.md:453-455.

Entrada del índice (≈6–10 líneas por comando):

| Campo | Contenido |
|---|---|
| `name` / `family` | `gaps` / ausencia |
| `question` | una oración: qué responde |
| `when_to_use` / `not_for` | disparadores y anti-usos (p. ej. "no usar tasa de PLAY para split-brain") |
| `args` clave | con defaults |
| `output` | columnas y `typical_size` |
| `applies_to` | profiles, plataformas, subsistema requerido |
| `example` | una invocación real, copiable en ambos shells |
| `next` | comandos típicos para profundizar |
| `stability` | `stable | experimental` |

Mapeo de ruteo inicial **[propuesta]**:

| Reporte | Secuencia |
|---|---|
| "Pantalla en negro" | `scan` → `check --signature black-screen-json-cascade` → `window --ref <hit>` |
| "Se reinicia sola" | `sessions --per day` → `resources` → `window --ref <fin de sesión>` |
| "No actualiza contenido" | `check` (heartbeat, missing-content) → `gaps --rule NET.HB` → `grep --pattern CNT.PLAYING` |
| "Descoordinadas" | `scan` (varios archivos) → `cluster` → `compare --by machine` |
| "Apagada" | `gaps` (cruza con display) → `grep --pattern POL.SCREEN_STATE` |
| No sé | `scan` → `summary --level ERROR,WARNING` → `check` |

---

## 8. Set mínimo v1

| # | Comando | Justificación |
|---|---|---|
| 1 | `doctor` | Primer contacto de QA en Windows: Python, `uv`, UTF-8 en consola, permisos de escritura. Evita tickets de "no anda" |
| 2 | `scan` | Manifest + identidad + `parse_rate` + aliases. Base de todo; lo primero que llama el agente (paso 2 de SI/01-LECTURA-BASE.md:91) |
| 3 | `sessions` | Reinicios bien contados (trampa #7), programado vs inesperado (F3/F4), por día. Caso nombrado por el usuario |
| 4 | `summary` | Panorama barato: formas por masking stdlib con `known: <id>`, ERROR sin stack traces, ruido contado. Reemplaza a Drain3 en v1 |
| 5 | `grep` | Búsqueda por id de catálogo o regex con envelope, etapa de ruido y citas. La salida de emergencia del agente |
| 6 | `window` | Contexto crudo alrededor de `ts` o `ref`, con merge multi-archivo. Profundización obligatoria antes de concluir |
| 7 | `resources` | Escalado de RAM/CPU por sesión con parámetros de plataforma, sin veredicto de fuga si no hay umbral |
| 8 | `cluster` | Split-brain / sin master / miembros inactivos / playlists distintas. Caso nombrado; parseo tolerante |
| 9 | `gaps` | Ausencia y cadencia (heartbeat 60 s, telemetría 300/60 s). La primitiva diferencial (ID/02-ARCHITECTURE.md:472) |
| 10 | `check` | Ejecuta las firmas aplicables. **Es el punto de extensión de bugs conocidos**: cubre negro, red y contenido faltante sin comandos dedicados |
| 11 | `compare` | Análisis cruzado: matriz pantalla × {versión, plataforma, boots, playlist+version_ts, hb_fail, masters} con `clock: naive` |
| 12 | `verify-citations` | Gate determinístico antes del informe (ID/03-SKILLS-AGENTS-SCRIPTS.md:342-350) |
| 13 | `index` | Autodescripción para la skill; `--check` para detectar drift |

Más `selftest`, **opcional** y para mantenedores, fuera de la ruta del agente.

**Después:** `playback`, `network`, `menuboard`, `storage`, `display` (hoy cubiertos parcialmente por `check`/`grep`), `status`, `timeline`, `diff` baseline/target, `cadence` libre, `trace`, `bisect`, `anomaly` (ID/03-SKILLS-AGENTS-SCRIPTS.md:323-328), Drain3 en `summary --discover`, `redact`, soporte de `.gz`/`.zip`, profile Android, gestión de caso (`new/close/archive`, ID/03-SKILLS-AGENTS-SCRIPTS.md:286-292).

---

## 9. Preguntas para el usuario

| # | Pregunta | Opciones | Recomendación | Qué cambia |
|---|---|---|---|---|
| 1 | ¿Se puede instalar `uv` en las PC Windows de QA (winget, ExecutionPolicy, proxy a GitHub y PyPI)? | a) sí · b) solo Python oficial · c) nada instalable | a, con b como fallback (núcleo stdlib) | Si es c: pasa a binario Go o a Python embebido portable, y se reevalúa §3 |
| 2 | ¿Quién agrega patrones y bugs conocidos? | a) Dev · b) Ops · c) QA | Diseñar para b: TOML + template + `selftest` | c empuja a más plantillas y validación; a permite más código |
| 3 | ¿TOML o YAML para el catálogo? | TOML (stdlib) · YAML (PyYAML, como la doc concepto) | TOML | Dependencias y legibilidad de regex |
| 4 | ¿Tamaño real de los logs a analizar? | a) como el corpus (≤50 MB por análisis) · b) varios GB o flota | a → re-ejecutar, sin índice | b obliga a persistir e indexar, a streaming paralelo y quizás a `rg`/Go |
| 5 | ¿Persistir resultados completos por defecto? | a) solo manifest + bitácora, `--save` opcional · b) todo siempre (ID/02-ARCHITECTURE.md:513) | a | Tamaño de la carpeta y paginación por cursor vs offset |
| 6 | ¿Menuboard / `menuboard-fetch-lock` entra en v1? | a) sí, criterio de aceptación · b) después | b, salvo que sea el criterio de aceptación (ID/03-SKILLS-AGENTS-SCRIPTS.md:446-447) | Suma `menuboard` + `absence` con `scope/key` por bucket en v1 |
| 7 | ¿Nomenclatura y layout de la carpeta del análisis? | `case`/`history/<id>` (doc concepto) · `analysis/<id>/logs` | Carpeta de análisis simple con `logs/` y `.loga/` | Paths de salida, citas, `status` |
| 8 | ¿Quién define umbrales (RAM, fuga, "reiterado", horario de tienda)? | a) producto ahora · b) v1 solo mide | b, con `thresholds.toml` vacío y opcional | Si es a, `resources`/`gaps` emiten veredictos |
| 9 | ¿Hay otros formatos en el horizonte (Android, logs de sistema, exports comprimidos)? | a) no por ahora · b) sí, lista concreta | Diseñar la interfaz de profile y shippear solo `dex-player` | Con b se valida la interfaz de profile con un segundo formato real antes de congelarla |
| 10 | ¿Shell real de los agentes en Windows? (Claude Code: Git Bash o PowerShell; Codex: PowerShell) | — | Asumir ambos y prohibir pipes/quoting complejos en la skill | Reglas de §4 y ejemplos del índice |
| 11 | ¿Formato por defecto al agente? | md + envelope · JSON compacto | md + envelope | Tokens vs facilidad de encadenar |
| 12 | ¿Existen todavía los scripts de medición del corpus (`profile.py`, `flows.py`, …)? | sí / no | Si existen, portar su lógica | Reduce el riesgo de `scan`/`sessions`/`resources` y aporta fixtures |
