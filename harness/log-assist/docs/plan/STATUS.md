# log-assist — Status de implementación

Leyenda: ⬜ pendiente · 🟡 en curso · ✅ hecho · ⛔ bloqueado
Regla: se actualiza al empezar y al terminar cada stage. Una línea por hecho, sin narrativa.

## Stages

| Stage | Objetivo | Depende de | Estado | Fecha | Notas |
|---|---|---|---|---|---|
| S1 | Base y contratos | — | ✅ | 2026-09-13 | 24 archivos. Suma `docs/log-format.md` (no estaba en el plan) |
| S2 | Core y scripts de estado | S1 | ✅ | 2026-09-13 | `loga_core` (6 módulos) + los 6 scripts de estado, verificados en Mac. **Windows diferido a S5** por decisión del usuario (pendiente 7) |
| S3 | Scripts de consulta | S2 | ✅ | 2026-09-13 | 10 scripts + `catalog.toml` (16 patrones, 8 firmas), verificados contra los 2 corpus (335.515 líneas) y el fixture. Windows pendiente (7) |
| S4 | Orquestador, skills, agentes, init | S2 | ✅ | 2026-09-13 | 11 archivos. Runtime 112 líneas (tope 150), 8 skills, 2 adapters. Coherencia cruzada verificada; corrida de punta a punta en S5 |
| S5 | Guía y README | S3, S4 | ✅ | 2026-09-13 | `README.md` (96) y `docs/USER_GUIDE.md` (319). **Solo documentación** por decisión del usuario: las pruebas manuales salen del stage y quedan abajo como paquete aparte |

## Decisiones tomadas durante la implementación

| Fecha | Stage | Decisión | Motivo |
|---|---|---|---|
| 2026-09-13 | S1 | `CLAUDE.md` importa `AGENTS.md` con `@AGENTS.md` y agrega solo su sección de plataforma; `AGENTS.md` = bloque común + sección Codex | Una sola fuente de verdad para el bloque común, sin lectura extra antes del worker-bypass. Efecto lateral asumido: Claude también lee la sección Codex, así que la sección Claude declara explícitamente que aquella no aplica |
| 2026-09-13 | S1 | Los headings de `SUMMARY.md`, `record/*.md` y `reports/*.md` quedan **siempre en inglés**; solo la prosa sigue `language` | `## Digest` y `## Discarded` son anclajes que leen el orquestador y `loga_verify_citations`; si se traducen, el parseo depende del idioma. Refina C-69 |
| 2026-09-13 | S1 | Las fechas de `state.toml` son **string ISO** (`"YYYY-MM-DD"`), no el tipo `date` nativo de TOML | Desvío consciente del snippet de §5.2 del plan. Permite que `templates/state.toml` sea TOML válido con placeholders visibles; `loga_progress` valida por regex. Aplica a `created`, `updated`, `decisions[].date` |
| 2026-09-13 | S1 | `loga.config.toml` suma `version` (versión del harness) a los 4 campos de §9 | `loga_doctor` lo necesita para detectar drift entre el clon y el repo |
| 2026-09-13 | S1 | `analyses_root` no es configurable: lo fija el contrato de persistencia | Evita una segunda fuente de verdad sobre el layout |
| 2026-09-13 | S1 | Allowlist de `.claude/settings.json` por prefijo `python* scripts/loga_` (las 3 formas de invocación) + escritura en `analyses/**` | C-56 pide allowlist mínima; el prefijo cubre los 16 scripts sin enumerarlos y sin abrir `Bash(python3:*)` entero |
| 2026-09-13 | S1 | Corpus de ejemplo registrado (ver Referencias) | El usuario aportó un caso real de 10 archivos para diseñar el fixture y para la aceptación de S5 |
| 2026-09-13 | S1 | **`docs/scripts-idea/` deja de ser fuente única del formato.** Se crea `docs/log-format.md` como referencia verificada y normativa para el parser | Verificación por conteo sobre 157.100 líneas: 18 divergencias. `scripts-idea/` se midió sobre 9 webOS + 5 Tizen; el corpus nuevo es 100 % Tizen. Parte de las divergencias es alcance de plataforma y parte son cifras no reproducibles. `scripts-idea/` queda como referencia amplia y única fuente sobre webOS |
| 2026-09-13 | S1 | Las trampas de §8.4 del plan se dividen en **invariantes** (se codifican en `loga_core`) y **observaciones de corpus** (se miden, nunca se asumen) | Las trampas #2 (stack traces = 20 % de ERROR) y #4 (umbrales por plataforma) quedaron falsificadas. Respalda C-45 / D-12: la v1 solo mide contra el rango observado |
| 2026-09-13 | S1 | Tres trampas nuevas, no previstas en el plan: ventana de época en el arranque, componentes de hasta 4 corchetes con vocabulario abierto, y DEBUG como nivel de producción | Verificadas con cita. Entran a `docs/log-format.md` §7 como reglas del parser |
| 2026-09-13 | S1 | **El nivel se lee por posición** (campo 4), nunca por texto. El status anidado se identifica **por contenido en cualquier posición** entre los hasta 4 grupos `[]`; el resto forman la ruta del componente | Decisión del usuario. `[MENUBOARD_TPL] [INFO] [OffsetsManager]` tiene el nivel en el medio y `[Node] [Sync] [SyncShouldPlay]` no tiene ninguno: ninguna regla posicional los cubre a los dos |
| 2026-09-13 | S1 | **Ningún script lleva lista blanca de componentes.** El ruido se deriva por frecuencia sobre el corpus analizado | Decisión del usuario: los nombres de componente varían por pantalla, template y cliente. `[MENUBOARD_TPL]` es el nombre de un template, no el del componente |
| 2026-09-13 | S1 | Cuando hay status anidado, **tiene prioridad** sobre el nivel de línea para filtrar y contar | Decisión del usuario. Consecuencia asumida: los conteos pueden no coincidir con un `grep` directo, así que todo script que reporte por nivel declara que usa el nivel efectivo y muestra el crudo cuando difieren |
| 2026-09-13 | S1 | El fixture es **miniatura fiel**: solo fenómenos verificados, cero inventados. Los casos fabricados van a fixtures hermanos con nombre que lo declara | Un fixture que enseña un fenómeno nunca observado hace que el parser aprenda mal |
| 2026-09-13 | S1 | Nombres de documentos nuevos en `docs/`: kebab-case, todo minúscula | Decisión del usuario |
| 2026-09-13 | S1 | Se agregan dos archivos que el plan no preveía: `scripts/fixtures/generate_sample.py` (el fixture se genera determinísticamente para poder ampliarlo en S3) y `scripts/fixtures/README.md` (declara que es sintético, qué ejercita, qué deliberadamente no tiene y que las proporciones no son fieles) | Ofrecidos al usuario; si prefiere solo el `.log`, se sacan |

## Referencias operativas

| Qué | Dónde | Para qué |
|---|---|---|
| Corpus de ejemplo mínimo | `~/Downloads/Logs-3057-ARROYO SECO 2 MBV 01/` (7 archivos, 2026-09-04..2026-09-10) y `~/Downloads/Logs-3057-ARROYO SECO 2 MBV 01 (1)/` (3 archivos, 2026-08-20..2026-08-22) | Diseño del fixture sintético (S1), validación del parser (S2/S3) y candidato de aceptación (S5). **Fuera del repo**: tiene nombres de cliente reales, no se commitea (D-17) |
| Corpus amplio | `/Users/nicolasschmidt/Documents/SIA/log_analyzer/logs_examples` | Validación de los 10 scripts de consulta (S3) y aceptación (S5) |

## Decisiones de S2

| Fecha | Stage | Decisión | Motivo |
|---|---|---|---|
| 2026-09-13 | S2 | `loga_new` copia `templates/state.toml` y sustituye **solo** `id`, `created` y `updated`. El orquestador escribe `title` y el resto | Resuelve la contradicción con C-46: ningún script serializa TOML, copia un archivo. Los comentarios del template quedan dentro del archivo mientras la IA lo edita, con los valores permitidos a la vista |
| 2026-09-13 | S2 | `loga_progress` trata un placeholder `<...>` que sobrevivió en un campo obligatorio como **error de validación**, no como campo vacío | Si no, un `state.toml` a medio llenar pasa silenciosamente. Verificado: detecta el `title` sin completar |
| 2026-09-13 | S2 | `loga_new` **no** crea los `record/*.md` | `loga_progress` deriva el progreso de qué archivos existen: un archivo vacío se leería como paso hecho. Consecuencia asumida: el progreso deriva de la existencia, no de la calidad del contenido |
| 2026-09-13 | S2 | `loga_verify_citations` verifica que la línea exista **y** que el excerpt coincida. Un excerpt coincide si es igual a la línea, si la línea empieza con el texto citado (quitando el marcador de truncado) o si el texto aparece en la línea | Decisión del usuario. El caso peligroso es la cita que apunta a una línea real con un texto reescrito. Verificado: exit 5 con excerpt inventado y con línea fuera de rango |
| 2026-09-13 | S2 | `loga_index` lee el `SPEC` de cada script con `ast`, sin importarlo | Listar el catálogo no debe ejecutar código |
| 2026-09-13 | S2 | `loga_doctor` reporta los artefactos de S4 (runtime, adapters, copias de skills) como `missing` con la leyenda "expected at stage S4" y devuelve exit 4 | Distingue "todavía no toca" de "roto" sin inventar un estado nuevo |
| 2026-09-13 | S2 | El nivel efectivo se implementa en `loga_core.parser`: `effective_level`, `level_differs` y `level_note()`, que genera la advertencia obligatoria cuando el nivel anidado difiere del de línea | Cumple la obligación que quedó en `docs/log-format.md` §2.4 |

## S3 — progreso por tandas (retomable)

Diseño validado: `temp/09-s3-script-design.md`. Evidencia: `temp/07` y `temp/08`.
Si la sesión se corta, retomar por la primera tanda que no esté ✅.

| Tanda | Contenido | Estado |
|---|---|---|
| 3.0 | `loga_core`: `logset.py`, `normalize.py`, `target.py`, extensiones al parser (plegado de frames, cadencia, saltos de reloj, `stamp`) | ✅ |
| 3.1 | `loga_scan`, `loga_summary`, `loga_grep`, `loga_window` | ✅ verificados contra los 14 archivos de `logs_examples` |
| 3.2 | `loga_sessions`, `loga_resources`, `loga_gaps` | ✅ |
| 3.3 | `catalog.toml` (8 firmas), `loga_check`, `loga_compare`, `loga_cluster` | ✅ |
| 3.4 | Verificación de los 10 contra los dos corpus y contra el fixture | ✅ los 16 scripts respetan el contrato en los 3 corpus; 2 s para 178.000 líneas |

Corpus de verificación (fuera del repo, no se commitea):
`~/Downloads/Logs-3057-ARROYO SECO 2 MBV 01{, (1)}/` y
`/Users/nicolasschmidt/Documents/SIA/log_analyzer/logs_examples/`.
El perfilador auxiliar que se usó en el análisis ya no hace falta: `loga_scan` y `loga_summary`
responden lo mismo.

## Decisiones de S3

| Fecha | Stage | Decisión | Motivo |
|---|---|---|---|
| 2026-09-13 | S3 | La señal `heartbeat` de `loga_gaps` es **solo la recepción exitosa**, no el intento. Se agrega `heartbeat-attempt` para medir cadencia | Encontrado probando: durante el outage de 1 h 37 min el player sigue emitiendo `Heartbeat Sync failed` cada 60 s, así que los intentos no tienen hueco. La ausencia solo se ve en las recepciones. Las rachas de falla son eventos y van a `loga_check`, no a `loga_gaps` |
| 2026-09-13 | S3 | Una señal periódica se define por su **línea de finalización**, no por la de inicio | Generaliza lo anterior: `Screenshot Uploaded` ocurre 6,5 s después de `Screenshot API called`; contar las dos parte la cadencia a la mitad |
| 2026-09-13 | S3 | `loga_gaps` trabaja **por pantalla**, no por archivo | El hueco más grande de los corpus (31,6 h) está entre dos archivos de la misma pantalla |
| 2026-09-13 | S3 | Se agrega `scripts/verify.py`, fuera del plan | Smoke test del **contrato de salida**, no un eval: no compara contra resultados esperados ni juzga ninguna respuesta. Chequea exit code, envelope JSON con sus 7 claves, nombre del script y stderr vacío. Es lo que atrapó los 8 bugs de S3 y convierte los 18 comandos de la verificación en Windows en uno. Un archivo, sin dependencias, se borra sin tocar nada |
| 2026-09-13 | S3 | **8 firmas en `catalog.toml`, no 6.** La pantalla negra se parte en `BLACK-SCREEN-JSON` y `BLACK-SCREEN-IO`; el "sin master" del plan se parte en `SYNC-NO-GROUP` y `SYNC-NO-MASTER` | Decisión del usuario. Son cascadas con componentes y textos distintos. `SYNC-NO-MASTER` no tiene ejemplo en ningún corpus: se carga igual y `loga_check` devuelve `insufficient_data` |
| 2026-09-13 | S3 | `loga_gaps` deriva su línea base como **3 × la cadencia mediana medida** de cada señal, con `--min-gap` opcional | Decisión del usuario. Cumple C-45 y se adapta solo a webOS 300 s vs Tizen 60 s, donde un umbral fijo fallaría |
| 2026-09-13 | S3 | `loga_sessions` busca la razón del reinicio en **12 líneas**, no 5, y hacia atrás hasta el `={53}` anterior | Medido: dos de las cuatro razones del corpus estaban a 8 y 9 líneas del banner |
| 2026-09-13 | S3 | **El countdown `Device will reboot in N minutes` no clasifica reinicios.** Solo vale `System will reboot. Reason:` | Corrige `scripts-idea/02 §2.3`. El mínimo observado en el corpus es 909 minutos y los reinicios programados cortaron con 1.439 y 1.437 |
| 2026-09-13 | S3 | `loga_gaps` distingue `clock-correction` de hueco real | 4 de los 6 saltos hacia atrás del corpus son la línea siguiente a `Server time offset: <N> milliseconds`, y el salto es exactamente ese offset |
| 2026-09-13 | S3 | `loga_cluster` infiere la IP propia como `Members:` menos `New member discovered:` | webOS no escribe `Hostname:`. Verificado en 11 de 14 archivos y contra los 3 Tizen que sí lo traen. Sin candidato único devuelve `own_ip: unknown` |
| 2026-09-13 | S3 | Las columnas de `loga_compare` son **pantallas, no archivos** | Dos archivos pueden ser la misma pantalla en días distintos (`20260219-0.log` + `20260222-0.log`) |
| 2026-09-13 | S3 | `catalog.toml` queda en **un solo archivo** en la v1 (~30 patrones + 8 firmas). Se parte por dominio al superar ~150 patrones | Resuelve el pendiente 2 |
| 2026-09-13 | S3 | `docs/log-format.md` se reescribe separando **invariantes** (verificadas en los dos corpus, 335.515 líneas), **hechos por plataforma** y **mediciones de corpus** | El reporte del corpus B mostró que la primera versión presentaba como formato varias cosas que eran de un solo corpus: "ASCII only", el techo de 325, la profundidad de 3 corchetes y el caso benigno de los archivos `(1)` |

## Bugs encontrados y corregidos durante S3

Ninguno se habría visto sin correr contra los corpus reales. Se registran porque son reglas, no accidentes.

| # | Síntoma | Causa | Corrección |
|---|---|---|---|
| 1 | `loga_check` daba `insufficient_data` en 5 de 8 firmas | Los patrones del catálogo están anclados al texto **después del componente** (`^Fail parsing JSON`), y yo matcheaba contra el mensaje completo, que incluye `[WebOS Storage] ` | `loga_core.parser.search()` prueba el texto y, como fallback, el mensaje. Documentado en `log-format.md` §2.3 |
| 2 | `loga_gaps` no detectaba el outage de 1 h 37 min | La señal mezclaba `Heartbeat received` con `Heartbeat Sync failed`, y durante el corte el player sigue emitiendo fallas cada 60 s: no hay hueco en los intentos | La señal es la **recepción exitosa**. Se agrega `heartbeat-attempt` para medir cadencia. Mismo criterio en `screenshot`: la señal es `Screenshot Uploaded`, no la llamada a la API, que ocurre 6,5 s antes |
| 3 | `loga_gaps` devolvía 5.946 huecos | La señal `policy` matcheaba dos líneas del mismo tick, así que la mediana de los deltas era 0 y todo delta contaba | La señal matchea una sola línea; además se colapsan ocurrencias a menos de 30 s y se avisa cuando una señal no es lo bastante periódica |
| 4 | El hueco real de 31,6 h no aparecía | `loga_gaps` analizaba por archivo, y el hueco está **entre** dos archivos de la misma pantalla | `loga_gaps` trabaja por pantalla, con los archivos en orden temporal. Nuevo tipo de hueco: `between-files` |
| 5 | Las cadencias salían con `mode_share` del 10 % | `cadence()` reordena por número de línea, y al unir varios archivos los números reinician | `cadence_of(timestamps)` para streams ya ordenados por tiempo |
| 6 | Una misma pantalla se partía en dos | `screen_key` elegía "el primer identificador disponible": un archivo sin bloque de estado no trae `Machine ID:` y caía al nombre, mientras el resto agrupaba por id | `by_screen()` reconcilia: dos archivos son la misma pantalla si comparten **cualquier** señal fuerte (id, nombre no ambiguo, IP propia). Sin identidad, quedan separados — nunca se fusionan por conjetura |
| 7 | Tablas markdown rotas | Los nombres de grupo sync contienen `\|` | `cli.md_cell()` escapa todo texto de log que entra en una tabla |
| 8 | `SYNC-NO-MASTER` devolvía `miss`, no `insufficient_data` como decía el diseño | El diseño confundía "nunca se vio un ejemplo" con "no se puede evaluar acá" | Se deja `miss`: hay líneas `Members:` pobladas, así que la condición **sí** se evaluó. `insufficient_data` queda para cuando no hay ninguna línea `Members:` |

## S4 — progreso por tandas (retomable)

Si la sesión se corta, retomar por la primera tanda que no esté ✅.

| Tanda | Contenido | Estado |
|---|---|---|
| 4.0 | `orchestrator/LOGA-RUNTIME.md` + `.claude/agents/loga-worker.md` + `.codex/agents/loga-worker.toml` | ✅ 112 líneas; `loga_doctor` da `ok` en los 3 |
| 4.1 | Skills de worker: `loga-inventory`, `loga-analyze`, `loga-explorer`, `loga-challenger`, `loga-report` | ✅ |
| 4.2 | `loga-scripts` (referencia), `loga-intake`, `loga-init` | ✅ |
| 4.3 | Cierre: `loga_doctor` en verde, coherencia cruzada skills ↔ contratos ↔ templates | ✅ 0 problemas: nombres, anatomía, ≤8 pasos, templates, scripts y rutas citadas existen |

## Decisiones de S4

| Fecha | Stage | Decisión | Motivo |
|---|---|---|---|
| 2026-09-13 | S4 | `loga-intake` es **autocontenida**: no depende de `grill-me` ni de nada fuera de `harness/log-assist/` | Decisión del usuario. El harness tiene que funcionar en un clon que no tenga `ai-tools`. De `grill-me` se traslada el patrón (settled vs open, read-back de lo ya decidido, park-no-drop), no el archivo |
| 2026-09-13 | S4 | Al adaptar `grill-me` se **cae** su formato `❓/➡️`, su política de idioma y su "writes nothing to disk"; se **invierte** su "facts vs decisions" | Diseño validado con el usuario. El formato de preguntas ya lo fija `loga-user-interaction-contract`; el idioma sale de `language` (C-69); `loga-intake` sí escribe `record/intake.md`. La inversión: en el intake el gate 1 prohíbe mirar los logs, así que la prioridad es preguntar **lo que ningún log contesta** (qué se vio, qué cambió alrededor) |
| 2026-09-13 | S4 | En `loga-intake` la recomendación por pregunta es **condicional**, no obligatoria como en `grill-me` | "¿Qué viste en la pantalla?" no admite recomendación: ofrecerla contamina la respuesta con las palabras del asistente. Recomendación donde hay opciones; pregunta abierta donde las palabras del usuario son el dato |
| 2026-09-13 | S4 | `loga-init` hace **todo desde la skill**, sin script nuevo | Decisión del usuario. Mantiene el set de 16 scripts de §8.3. Consecuencia asumida: el copiado de las skills a `.claude/skills/` y `.agents/skills/` lo hace la IA, y el drift lo detecta `loga_doctor` |
| 2026-09-13 | S4 | `LOGA-RUNTIME.md` **referencia** los contratos `_shared`, no los repite | Decisión del usuario. Una sola fuente de verdad. Costo asumido: el orquestador lee ~2 archivos al arrancar en vez de 1 |
| 2026-09-13 | S4 | S4 cierra por **coherencia**, no por corrida | Decisión del usuario. La corrida de punta a punta del "done" de §11 se hace en S5 con logs reales, junto con la aceptación |

| 2026-09-13 | S4 | El presupuesto de fragmentos de `loga-explorer` **no se inventa**: lee por `loga_window`, que ya está acotado por `--max-chars` (8000 por defecto, techo 40000) | El plan dice "fragmentos acotados" sin dar un número. En vez de inventar un límite de líneas, se reutiliza el que ya fijó C-65. Un fragmento que no entra son dos fragmentos, cada uno registrado en la tabla |
| 2026-09-13 | S4 | `loga-init` copia solo `skills/loga-*/SKILL.md`; `skills/_shared/` **no** se copia | Es exactamente lo que compara `loga_doctor` para detectar drift. Las skills referencian `_shared` por ruta desde la raíz del clon, así que la copia no lo necesita |
| 2026-09-13 | S4 | El adapter de Claude precarga 6 skills: las 5 de worker más `loga-scripts` | `loga-init` y `loga-intake` corren en la sesión principal: precargarlas en el worker invitaría a un worker a orquestar |
| 2026-09-13 | S4 | Estado final esperado de `loga_doctor` en S4: 9 `ok`, 1 `partial`, 1 `missing` | Las dos filas que no están en verde son `config` y `skill copies`, y son justo las que arregla `loga-init`. En verde recién después de correrlo |

## Decisiones de S5

| Fecha | Stage | Decisión | Motivo |
|---|---|---|---|
| 2026-09-13 | S5 | S5 se reduce a **documentación**. Las pruebas manuales salen del stage | Decisión del usuario. Son de naturaleza distinta: la doc la escribo solo, las pruebas requieren logs reales, una Windows y una sesión acompañada |
| 2026-09-13 | S5 | El paquete de pruebas manuales queda **dentro de `STATUS.md`**, no en un doc aparte | Decisión del usuario (se ofreció `docs/plan/acceptance.md` y lo descartó). Consecuencia asumida: `STATUS.md` sigue largo, pero todo el estado vive en un solo archivo |
| 2026-09-13 | S5 | El recorrido de la guía usa el **fixture sintético**, con salidas reales pegadas | Decisión del usuario. Los comandos son reproducibles por cualquiera y no tocan datos de cliente. La parte conversacional se describe y se declara descrita, no transcripta |
| 2026-09-13 | S5 | README corto (qué es, qué no hace, quickstart, mapa) + guía completa | Decisión del usuario. El README cambia poco; la guía cambia con cada aprendizaje |
| 2026-09-13 | S5 | Los dos documentos **declaran explícitamente lo no verificado**: flujo de punta a punta, Windows y el adapter de Codex | La guía describe un flujo tal como lo definen los contratos, no tal como se comportó. Presentarlo como probado sería la única afirmación sin evidencia de todo el harness |
| 2026-09-13 | S5 | Se agregan `docs/architecture.md` (122) y `docs/README.md` (41), fuera del plan | Pedido del usuario: que otra persona entienda el harness en detalle. Cubren los dos huecos que quedaban: cómo funciona por dentro (hoy solo se deduce leyendo el plan, que es un documento de proceso) y qué documento manda sobre cuál. Deliberadamente **no** repiten el flujo de uso, el formato de log ni las reglas de cada skill |
| 2026-09-13 | S5 | Nada commiteado todavía | Decisión del usuario: el commit queda para cuando termine todo, incluida la aceptación |

## Extensión post-S5 — `inbox/` e importación de logs

Pedido del usuario del 2026-09-13, después de cerrar los 5 stages y antes del commit.

| Fecha | Decisión | Motivo |
|---|---|---|
| 2026-09-13 | La carpeta se llama **`inbox/`**, no `logs_archive/` | Se descartó "archive" porque comunica que los archivos se quedan, y la carpeta se vacía en cada importación. El nombre enseñaría el modelo mental equivocado |
| 2026-09-13 | El import corre **después del intake**, no antes. **El gate 1 no se toca** | Decisión del usuario. Triagear con `loga_scan` es consultar logs, así que hacerlo antes obligaba a re-enunciar una de las dos reglas duras. Beneficio lateral: el slug del id sale del síntoma (`black-screen`), no del nombre del archivo |
| 2026-09-13 | `loga-import` es worker y **devuelve un plan de movimiento; el orquestador lo aplica** | `logs/` está fuera del write scope de cualquier worker. Devolver un plan en vez de ampliar el scope mantiene intacta una regla vertebral. Queda documentado en `architecture.md` como el patrón a usar cuando una skill parezca necesitar más permisos |
| 2026-09-13 | El movimiento es **destructivo**, sin script nuevo: lo hace la skill/orquestador con sus herramientas | Decisión del usuario: el inbox es una copia de paso y los originales están descargados en otro lado. Eso disolvió el argumento de pérdida de datos, que era la única razón para un `loga_import.py`. Se mantiene el set de 16 scripts |
| 2026-09-13 | Nunca se sobrescribe y nunca se borra lo que no se movió | Colisión de nombres (dos carpetas con `20260220-0.log`) se resuelve prefijando con la carpeta de origen. Los sobrantes (capturas, `.zip`, lo que no parsea) quedan en el inbox con su razón |
| 2026-09-13 | `loga_progress` detecta el inbox y sugiere `loga-import` solo | Verificado en las dos ramas: con intake hecho sugiere `loga-import`; sin intake sigue mandando `loga-intake` porque el gate 1 manda. Sin archivos, `ask-for-logs` como antes |
| 2026-09-13 | `loga_doctor` suma un check `inbox` que **falla si no está en `.gitignore`** | Un inbox versionable es peor que no tener inbox: es la carpeta donde la gente pega logs de producción sin pensarlo |

Archivos: `skills/loga-import/SKILL.md` (nuevo) · `.gitignore` · `orchestrator/LOGA-RUNTIME.md` ·
`skills/_shared/loga-flow-contract.md` · `skills/loga-init/SKILL.md` · los 2 adapters ·
`scripts/loga_core/analysis.py` · `scripts/loga_progress.py` · `scripts/loga_doctor.py` ·
`README.md` · `docs/USER_GUIDE.md` · `docs/architecture.md`.

Verificado: `loga_doctor` 10 ok · 1 partial · 1 missing (12 checks); los 16 scripts respetan el
contrato; coherencia cruzada de las 9 skills sin problemas; runtime en 123 de 150 líneas.

## Pruebas manuales — pendientes, fuera de los stages

Todo lo que necesita datos reales, una máquina Windows o una sesión de punta a punta acompañada.
Sale de S5 por decisión del usuario (2026-09-13). Nada de esto está hecho.

### 1. Aceptación sobre casos reales — checklist de §12 del plan

Sobre 2-3 casos de `logs_examples` con problema conocido, **que elige el usuario**.
Candidatos ya rankeados en `temp/08` §8; el más fuerte es `20260220-0.log`.

| # | Criterio | Estado |
|---|---|---|
| 1 | El flujo completo corre sin intervención manual sobre archivos, solo conversación | ⬜ |
| 2 | El análisis llega a la conclusión ya conocida, o explica con evidencia por qué no puede | ⬜ |
| 3 | Toda afirmación de los reports tiene cita verificada (`loga_verify_citations` en 0) | ⬜ |
| 4 | Ningún log entero entró en contexto: solo scripts o fragmentos del explorer | ⬜ |
| 5 | `SUMMARY.md` alcanza para entender el caso sin abrir `record/` | ⬜ |
| 6 | `loga_search` encuentra el análisis por status, plataforma y tag | ⬜ |
| 7 | Los scripts corren igual en Mac y en Windows: mismos comandos, misma salida | ⬜ |
| 8 | El mismo caso corre en Claude y en Codex con los mismos artefactos | ⬜ |

### 2. Corrida de punta a punta — el "done" de S4

Movida acá por decisión del usuario. Un análisis completo que produzca `state.toml`,
`SUMMARY.md`, `record/` y un report, en Claude y en Codex. Es lo que ejercita por primera vez
el runtime, las 8 skills, los dos gates y el adapter de worker. Hasta que corra, el flujo
conversacional está **escrito y verificado por coherencia, nunca ejecutado**.

### 3. Verificación en Windows

Decisión del 2026-09-13: no hay Windows disponible, se corre entera junto con la aceptación.
Correr desde la raíz del clon, con `py -3` o `python`. Ninguno usa shell, pipes ni rutas absolutas.

**Atajo**: `py -3 scripts\verify.py --corpus <carpeta>` corre los 16 y verifica el contrato de
salida de una. Si sale `every script honored the contract`, los casos 9 a 18 de abajo están
cubiertos; quedan los 1 a 8, que prueban los códigos de salida de error.

| # | Comando | Resultado esperado |
|---|---|---|
| 1 | `py -3 scripts\loga_doctor.py` | exit 4 · `python ok`, `templates ok` (11), `contracts ok` (3), `wrappers ok`, `permissions ok`; los de S4 en `missing` |
| 2 | `py -3 scripts\loga_index.py` | exit 0 · tabla con los 6 scripts de estado |
| 3 | `py -3 scripts\loga_new.py WIN-1-prueba` | exit 0 · crea `analyses\WIN-1-prueba` con `logs`, `record`, `record\runs`, `reports`, `state.toml`, `SUMMARY.md` |
| 4 | `py -3 scripts\loga_progress.py WIN-1-prueba` | exit **3** · una advertencia: el `title` sigue con el placeholder |
| 5 | `py -3 scripts\loga_search.py --status new` | exit 0 · una fila, `WIN-1-prueba` |
| 6 | `py -3 scripts\loga_search.py --status inventado` | exit **2** |
| 7 | Copiar `scripts\fixtures\sample.log` a `analyses\WIN-1-prueba\logs\P1.log`, crear un `record\findings.md` con una cita a una línea inexistente, y correr `py -3 scripts\loga_verify_citations.py analyses\WIN-1-prueba\record\findings.md` | exit **5** |
| 8 | En todos los casos | la primera línea de stdout es JSON válido; los acentos y los espacios dobles de los excerpts salen intactos |

Y los 10 de consulta, contra un corpus real (`--path` a una carpeta con logs):

| # | Comando | Resultado esperado |
|---|---|---|
| 9 | `py -3 scripts\loga_scan.py --path <carpeta>` | exit 0 · una fila por archivo; las pantallas repetidas agrupadas |
| 10 | `py -3 scripts\loga_summary.py --path <carpeta> --top 5` | exit 0 · 5 formas con su porcentaje |
| 11 | `py -3 scripts\loga_grep.py --path <carpeta> --regex "Heartbeat" --limit 3` | exit 0 · 3 filas con cita y excerpt |
| 12 | `py -3 scripts\loga_window.py --path <carpeta> --at F1:100 --before 2 --after 2` | exit 0 · 5 líneas numeradas |
| 13 | `py -3 scripts\loga_sessions.py --path <carpeta>` | exit 0 · una fila por arranque |
| 14 | `py -3 scripts\loga_resources.py --path <carpeta>` | exit 0 · rango de RAM observado |
| 15 | `py -3 scripts\loga_gaps.py --path <carpeta>` | exit 0 · tabla de baselines con la cadencia medida |
| 16 | `py -3 scripts\loga_check.py --path <carpeta> --all` | exit 0 · las 8 firmas con su veredicto |
| 17 | `py -3 scripts\loga_cluster.py --path <carpeta>` | exit 0 · una fila por snapshot |
| 18 | `py -3 scripts\loga_compare.py --path <carpeta>` | exit 0 · matriz, o el aviso de menos de dos pantallas |

Lo que hay que mirar con atención: que las citas se impriman con `/` y no con `\`, que no aparezcan `\r` en las salidas, y que los nombres de archivo con espacios y paréntesis se manejen bien.

## Pendientes y bloqueos

| # | Qué | Stage | Estado |
|---|---|---|---|
| 1 | ~~Verificar si las líneas `1969-/1970-` son arranque normal (X-11)~~ | S1 | ✅ **Resuelto**: 286 líneas `1969-12-31` = epoch 0 en −03:00, siempre dentro de un arranque. Es la forma normal del arranque en Tizen (levanta antes del NTP). Cero líneas `1970-`. Documentado en `docs/log-format.md` §2.6 |
| 2 | ~~Decidir si `catalog.toml` se parte por dominio~~ | S3 | ✅ Un solo archivo en v1; se parte al superar ~150 patrones |
| 3 | `.claude/settings.json` y los wrappers viven en `harness/log-assist/` y solo se activan con `log-assist` como cwd | — | 🟡 **Observado en S3**: con esa cwd, Claude Code carga `CLAUDE.md` y resuelve el `@AGENTS.md`, así que el wrapper funciona. Falta verificar que la allowlist de `settings.json` evite los prompts de permiso |
| 4 | Fixture para `loga_compare` y `loga_cluster` | S3 | 🟡 **Ya no hace falta fabricarlo**: `QMC32 QA 1/2` es el único grupo completo del corpus (2 de 2 miembros, 808 y 1.144 líneas, master claro, un miembro con 48 `Missing Content`). Se usa como caso de prueba real; el fixture sintético queda para las pruebas que no pueden tocar datos de cliente |
| 5 | ~~Ningún camino webOS verificado~~ | S3 | ✅ Verificado sobre 9 archivos webOS: cadencia 300 s y RAM 1.064-1.288 Mb exactas, stack traces 21,5-49,6 % de ERROR, split-brain 41,7 %, `[Webos Storage Manager]` ~10 % del volumen |
| 6 | Los nombres de los docs de `docs/idea/` y `docs/scripts-idea/` están en mayúsculas, contra la convención kebab-case minúscula que se fijó en S1 | — | ⬜ No se renombran sin pedido: son documentos previos con enlaces cruzados |
| 7 | Verificación en Windows de **todos** los scripts | — | ⬜ Ver «Pruebas manuales» §3. El usuario no tiene Windows disponible ahora y lo corre al final, junto con la aceptación. Los 8 comandos de los scripts de estado están en la sección de arriba; S3 suma los suyos a esa lista |
| 8 | ~~C-46 vs `loga_new` escribiendo `state.toml`~~ | S2 | ✅ Resuelto: copia el template y sustituye solo campos mecánicos |
| 9 | `docs/scripts-idea/08-TEMPLATES.md` quedaba fuera de git | — | ✅ **Bug preexistente del repo padre**: la regla `*-temp*` del `.gitignore` de `ai-tools` lo matchea porque git en macOS usa `core.ignorecase=true`. Resuelto con una negación en el `.gitignore` de este repo. La regla de `ai-tools` sigue siendo imprecisa y conviene arreglarla allá (`*-temp/` en vez de `*-temp*`) |
