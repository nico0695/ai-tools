# 09 · Diseño de los 10 scripts de consulta (S3)

Insumos: `docs/log-format.md`, `docs/scripts-idea/`, y las mediciones de `temp/05` a `temp/08`
sobre los dos corpus (335.515 líneas, 24 archivos, webOS + Tizen).

Regla transversal (C-45 / D-12): **los scripts miden y comparan contra el rango observado en el
corpus que están analizando. Ninguno emite veredicto contra un umbral fijo.** Cuando un flag de
umbral existe, es opcional, y la salida dice que se usó.

Todos heredan el contrato de `loga_core.cli`: envelope JSON en la primera línea, `--format`,
`--max-chars`, `--limit/--offset`, `--save`, exit codes 0/2/3/4/5/1, citas `archivo:línea` con
alias `F1…`, sin pipes.

Argumentos comunes: `--analysis <id>` (resuelve `analyses/<id>/logs/`) o `--path <dir|file>`,
más `--file F1` para acotar a un archivo por alias.

---

## 1. `loga_scan` — qué archivos hay

**Responde**: qué archivos, de qué pantalla y plataforma, qué rango cubren, si parsean.
**Args**: `--analysis <id>` · `--refresh` (reescribe el manifest).
**Salida**: una fila por archivo — alias, nombre, `Machine:`, plataforma, versión, primera/última
línea, líneas, `parse_rate`, arranques. Más un bloque de cobertura: pantallas distintas, grupos,
huecos entre archivos. Escribe `record/runs/manifest.json`.

**Trampas que codifica**
- Identidad por `Machine:`, nunca por nombre de archivo (regla 9).
- `Machine:` puede valer `<IP> <MAC>`: se marca `identity: ambiguous`, no se usa como nombre.
- Nunca deduplica: dos archivos con el mismo tamaño y rango son pantallas distintas hasta que la
  identidad diga lo contrario (`20260223-0.log` y su `(1)`, 5.472 líneas cada uno).
- `parse_rate < 1.0` → exit 4 y las primeras líneas no parseadas en la salida.
- Dos archivos del corpus no tienen bloque de estado: la identidad sale solo del handshake.

## 2. `loga_summary` — qué hay en el log

**Responde**: qué mensajes hay por nivel, componente y forma; cuánto es ruido; qué ERROR hay.
**Args**: `--level`, `--component`, `--top N` (default 20), `--errors-only`, `--include-noise`.
**Salida**: conteo por nivel (efectivo, con la nota si difiere del de línea) · top-N formas
normalizadas con conteo y % · top componentes · lista de formas ERROR distintas con una cita.

**Trampas que codifica**
- Ruido derivado por frecuencia, jamás por lista blanca (reglas 5 y 11). Lo oculto se cuenta y el
  envelope dice cuánto.
- Normalización de formas: números, IPs, rutas, comillas y JSON a `<N>`, `<IP>`, `<PATH>`, `<S>`, `<JSON>`.
- Los frames `^\s+at\s` se pliegan al evento anterior y no cuentan como formas ERROR (regla 10).
- Frames truncados byte-idénticos cuentan como uno: 253 frames iguales son un error, no 253.

## 3. `loga_grep` — líneas que matchean

**Responde**: qué líneas matchean un patrón del catálogo o una regex.
**Args**: `--pattern <id-del-catálogo>` | `--regex <re>` · `--level` · `--component` ·
`--before N --after N` · `--fold-traces/--no-fold-traces`.
**Salida**: líneas con cita y excerpt verbatim, paginadas.

**Trampas que codifica**
- La regex se aplica al **mensaje**, no a la línea cruda (regla 3). Un `--regex` que empiece con `^`
  y no matchee nada dispara un warning explicando esto.
- Excerpts byte a byte, con los espacios dobles y finales (regla 14).
- Corte de display a 300 con `…[+N chars]`, nunca corta el matcheo.

## 4. `loga_window` — contexto alrededor de un punto

**Responde**: qué pasó alrededor de un timestamp o de `archivo:línea`.
**Args**: `--at <archivo:línea>` | `--time <YYYY-MM-DD HH:MM:SS>` · `--before N --after N`
(default 20/20) · `--merge` (intercala varios archivos).
**Salida**: las líneas del rango con cita; en modo merge, una columna de alias por archivo.

**Trampas que codifica**
- Orden por `(archivo, línea)` (regla 7). En merge, el orden temporal se ofrece pero se marca como
  suposición: los relojes no tienen zona horaria.
- Si el rango cruza la ventana de época, se marca y no se calculan deltas de reloj (regla 6).

## 5. `loga_sessions` — arranques y uptime

**Responde**: cuántas veces arrancó, si fue programado o inesperado, cuánto duró cada sesión.
**Args**: `--reason-window N` (default **12** líneas).
**Salida**: una fila por sesión — n, cita del arranque, razón y su cita, clasificación
(`scheduled | commanded | unexpected | unknown`), primera y última línea, duración.

**Trampas que codifica**
- Cuenta por `^Dex Player [\d.]+$` sobre el mensaje; si usa `={53}` lo divide por 2 (reglas 3 y 6).
- **La ventana de razón es de 12 líneas, no 5**: en el corpus dos razones estaban a 8 y 9 líneas.
  Busca hacia atrás hasta el `={53}` anterior y una línea más.
- **El countdown `Device will reboot in N minutes` NO clasifica nada**: el mínimo observado es 909
  minutos y los reinicios programados cortaron con 1.439 y 1.437. Solo vale la línea explícita
  `System will reboot. Reason:`.
- `All tasks were finished` aparece en 3 de 4 reinicios con razón: se reporta como señal de apoyo,
  nunca como criterio.
- Un arranque en la línea 2 del archivo es `unknown`, no `unexpected`: no hay sesión previa.
  En el corpus son 12 de 23.

## 6. `loga_resources` — RAM y CPU

**Responde**: cómo se movieron RAM y CPU por sesión, y si faltan muestras.
**Args**: `--per-session` · `--samples` (serie completa) · `--baseline <ram-min:ram-max>` (opcional).
**Salida**: por sesión — n muestras, min/max/media de CPU y RAM, tendencia (pendiente de la
regresión), cadencia medida y muestras faltantes. Comparación contra el rango del propio corpus.

**Trampas que codifica**
- Cadencia **medida**, no asumida: 60 s en Tizen y 300 s en webOS, pero se deriva de los deltas.
- Sin umbral de producto (regla 12). El piso de 648 Mb de la doc falla en un corpus (12,6 % debajo)
  y es exacto en el otro: por eso solo se compara contra lo observado, y `--baseline` es opcional.
- **La primera muestra tras un arranque es un outlier estructural**: en los 5 Tizen del corpus B es
  el máximo del archivo (98-99 %) y la segunda cae a 27-33 %. Se reporta aparte, no se promedia.
- Existe una segunda fuente, `CPU usage: … Used RAM: … Mb` sin componente, dentro del bloque de
  estado. Se cuenta aparte y se dice.
- Las muestras de la ventana de época no entran en los deltas.

## 7. `loga_gaps` — qué debería ocurrir y no ocurrió

**Responde**: qué señal periódica se interrumpió, cuándo y por cuánto.
**Args**: `--signal heartbeat|telemetry|policy|screenshot|any` · `--min-gap <s>` (opcional; por
defecto **3 × la cadencia mediana observada** de esa señal) · `--include-reboots`.
**Salida**: una fila por hueco — señal, desde/hasta con cita, duración, cuántas muestras faltaron,
y si coincide con un arranque.

**Trampas que codifica**
- La línea base es la cadencia **medida** de cada señal, no un número fijo. En el corpus el hueco
  máximo típico por archivo es de 21 a 63 s, del orden del heartbeat: un umbral en el minuto genera
  ruido puro.
- **Corrección de reloj vs. hueco real**: 4 de los 6 saltos hacia atrás del corpus son la línea
  siguiente a `[System Manager] Server time offset: <N> milliseconds`, y el salto es exactamente ese
  offset. Se detectan y se reportan como `clock-correction`, no como anomalía.
- Un hueco que contiene un arranque se marca `reboot`, y por defecto no se lista.
- Un hueco puede ser la pantalla apagada por política horaria: nunca se afirma que sea una falla.

## 8. `loga_check` — firmas de bugs conocidos

**Responde**: qué firmas del catálogo matchean, con qué evidencia.
**Args**: `--signature <id>` · `--domain <dom>` · `--all`.
**Salida**: por firma — `hit | miss | insufficient_data`, evidencia con citas, y qué le faltó
cuando es `insufficient_data`.

**Trampas que codifica**
- `insufficient_data` es un resultado de primera clase: si el corpus no tiene la señal que la firma
  necesita, no es `miss`.
- `not_if` para descartes explícitos.
- Toda firma exige la secuencia completa, no la proximidad. La heurística "hay un ERROR cerca de
  `Clearing current playlist`" da falso positivo en `20260223-0.log:4112`.

## 9. `loga_compare` — matriz pantalla × métrica

**Responde**: en qué coinciden y en qué difieren las pantallas del análisis.
**Args**: `--screens A,B` · `--metrics <lista>` · `--group <sync-group>`.
**Salida**: matriz con una fila por métrica y una columna por pantalla, cada celda con su cita, más
una sección de divergencias.

Métricas v1: versión del player · plataforma · arranques · primera/última línea · líneas ERROR
(sin frames) · heartbeat recibidos/fallidos · playlist actual · rol de sync · contenido faltante.

**Trampas que codifica**
- Las columnas son **pantallas**, no archivos: dos archivos de la misma pantalla se agregan
  (`20260219-0.log` + `20260222-0.log` son una sola columna).
- Cualquier comparación temporal entre pantallas se marca como suposición (regla 7).
- Una celda sin dato es `—` con el motivo, nunca un cero.

## 10. `loga_cluster` — salud del grupo sync

**Responde**: quién es el master, quién está, y si el grupo está bien formado.
**Args**: `--snapshots` (lista todos) · `--at <archivo:línea>`.
**Salida**: por snapshot — cita, grupo, miembros, cantidad de `[Master]`, veredicto
(`healthy | split-brain | no-group | no-master | unknown`), y las filas del bloque cuando existen.

**Trampas que codifica**
- **Cuenta los `[Master]` de la línea `Members:`**, no los `(MASTER)` de las filas: la línea existe
  en los 13 archivos con grupo, y la tabla falta en 13 de 35 bloques.
- Distingue **`no-group`** (`Group: undefined - Members: ` vacío) de **`no-master`** (grupo poblado,
  cero masters). El corpus solo tiene el primero.
- **IP propia**: webOS no escribe `Hostname:`. Se infiere como `Members:` menos
  `New member discovered:`, que nunca lista la IP propia. Verificado en 11 de 14 archivos y contra
  los 3 Tizen que sí traen `Hostname:`. Si la diferencia no da un candidato único, se declara
  `own_ip: unknown`.
- Tolera archivos sin ninguna línea `Members:` (2 de 14): reporta `unknown`, no error.
- El intervalo entre comandos PLAY es la duración del medio, no una cadencia: no se usa como señal.

---

## `catalog.toml`

Un solo archivo en v1 (~30 patrones + 6 firmas). Se parte por dominio cuando supere ~150 patrones.

```toml
[[patterns]]
id = "NET.HB.FAIL"
domain = "NET"
component = "Server Manager"
level = "ERROR"
regex = "^Heartbeat Sync failed\\. Status: (?P<cause>.+)$"
platforms = []            # vacío = cualquiera
noise = false
examples = ["Heartbeat Sync failed. Status: Error: Network Error"]
counterexamples = ["Heartbeat received from server"]

[[signatures]]
id = "BLACK-SCREEN-JSON"
symptom = "la pantalla quedó en negro tras un cambio de playlist"
platforms = ["webos"]
rule = "sequence"
within_ms = 100
steps = ["CNT.JSON.FAIL", "CNT.LOAD.FAIL", "CNT.PLAY.FAIL", "CNT.CLEAR"]
not_if = ["the only preceding ERROR is NET.HB.FAIL"]
evidence = "20260222-0.log:38-42"
```

### Las 6 firmas, con su estado real en el corpus

| id | Ejemplo real | Nota |
|---|---|---|
| `BLACK-SCREEN-JSON` | ✅ 5 casos | duración medida 20-30 ms; dos textos de causa (`Unexpected end of JSON input`, `Unexpected token t in JSON at position N`) |
| `BLACK-SCREEN-IO` | ✅ 6 casos | **no documentada**. Dos grafías del componente conviven (`[WebOS Storage]` y `[Webos Storage Manager]`) y la causa lleva un `]` huérfano: `IO_ERROR]: Failed to read data` |
| `REBOOT-LOOP` | ✅ 1 caso | 4 arranques en 4 min 44 s, ninguno con razón |
| `SYNC-SPLIT-BRAIN` | ✅ 5 snapshots | 2 y 3 masters |
| `SYNC-NO-GROUP` | ✅ 1 caso | `Group: undefined - Members: ` vacío |
| `SYNC-NO-MASTER` | ❌ sin ejemplo | grupo poblado con 0 masters. Se carga la firma y `loga_check` devuelve `insufficient_data` mientras no haya corpus que la ejercite |
| `HEARTBEAT-OUTAGE` | ✅ 2 magnitudes | 98 fallas / 1 h 37 min, y 2 fallas simultáneas en 3 pantallas |
| `MISSING-CONTENT` | ✅ 7 archivos | **3 formas de mensaje**, una repite el fragmento dos veces en la misma línea |

Son 8 firmas, no 6: la pantalla negra son dos y el "sin master" del plan son dos casos distintos.
