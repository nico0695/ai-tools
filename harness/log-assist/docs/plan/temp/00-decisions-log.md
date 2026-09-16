# 00 · Registro de decisiones — log-assist (pre-plan)

Registro vivo durante el análisis. Fuente de verdad para armar `../log-assist-plan.md`.
Estados: **CONFIRMADO** (lo dijo o validó el usuario) · **DEDUCIDO** (inferido, falta validar) · **PENDIENTE** (pregunta abierta) · **FUERA v1**.

## Archivos del análisis

| Archivo | Contenido |
|---|---|
| `00-decisions-log.md` | Este registro: decisiones, deducciones, alcance v1, preguntas |
| `01-sdd-lite-patterns.md` | Patrones de sdd-lite: reutilizar / adaptar / no aplica |
| `02-idea-analysis.md` | Análisis crítico de `docs/idea/` vs lo pedido por el usuario |
| `03-scripts-analysis.md` | Planificación de scripts: runtime, contrato, extensibilidad, set v1 |

## 1. Confirmado por el usuario (chat)

| # | Tema | Decisión |
|---|---|---|
| C-01 | Referencia | `sdd/sdd-lite` es la referencia de patrones. **No** usar `sdd/blueprint-harness` |
| C-02 | Idea previa | `docs/idea/` es concepto, no fuente de verdad. Ante contradicción o duda, validar con el usuario |
| C-03 | Orquestador | Punto principal de la sesión, liviano: no carga contexto, lee la persistencia que escriben los subagentes y guía al usuario por el harness |
| C-04 | Estructura | Similar a sdd-lite: `skills/`, `orchestrator/`, `templates/`… *(superado por C-59: sin `schemas/`)* |
| C-05 | Persistencia | Carpeta por análisis, con los logs (planos o subcarpetas de 1 nivel por pantalla) + carpeta de persistencia tipo `changes` + `.md` legibles para humanos en los puntos importantes. Es la parte más importante: simple y validable |
| C-06 | Init | Skill de init: crea la estructura y valida que las IAs integradas (Claude, Codex) funcionen |
| C-07 | IAs | Funciona igual en Claude y en Codex |
| C-08 | Distribución | Configurado fijo en un repo que se clona para hacer análisis |
| C-09 | Scripts | Consultan los logs y devuelven solo lo necesario (preciso, determinístico, ahorra tokens). Los subagentes solo usan scripts para buscar. Tiene que haber un índice o una skill propia de scripts |
| C-10 | Scripts OS | Soportan Linux, Mac y Windows |
| C-11 | Scripts extensibles | Se puede extender con nuevos casos y nuevos tipos de logs |
| C-12 | Skills | Solo las necesarias para la v1, usables como subagentes. Evaluar grill-me |
| C-13 | Jira | Cada análisis persiste su ticket de Jira y metadata breve (fecha, plataforma, versión del player…) con un status simple que se completa con las interacciones |
| C-14 | Interacción | Interactivo, no asume nada, ayuda a que el usuario confirme el problema |
| C-15 | Búsqueda | Búsqueda simple entre análisis previos (por ejemplo por status) para detectar relación |
| C-16 | Relevamientos | Templates simples y breves: hallazgos formalizados, estado alcanzado o hipótesis aunque no haya conclusión |
| C-17 | Tipos de análisis | Inconsistencias, bugs conocidos, patrones (escalado de memoria/CPU), cross-log (varios archivos de una pantalla) y comparativo (varias pantallas) |
| C-18 | Evals | Sin evals por ahora |
| C-19 | Idioma | Documentos del plan en español por ahora |
| C-20 | Plan | Salida final: `docs/plan/log-assist-plan.md` con índice, resumen, secciones, stages controlables (pocos) y tabla de status por stage |
| C-21 | Topología (B1) | `harness/log-assist/` **es la raíz del repo clonable**: se desarrolla en ai-tools y se copia o publica tal cual. Sin instalador. Tiene en la raíz `AGENTS.md`, `CLAUDE.md`, `.claude/`, `.codex/`, `orchestrator/`, `skills/`, `scripts/`, `templates/`, `docs/` y `analyses/` (creada por init) |
| C-22 | Git (B1) | **Todo local**: `analyses/` completa gitignorada (logs y análisis). La búsqueda entre análisis previos solo ve lo que hay en la máquina |
| C-23 | Usuarios v1 (B1) | Dev y perfiles técnicos en Linux/Mac/Windows. Instalar runtime con un comando es aceptable |
| C-24 | Prefijo (B1) | Prefijo `loga-` para skills y artefactos del harness (p. ej. `loga-init`) |
| C-25 | Persistencia (B2) | **md por paso + `state.toml`** (estilo openspec): `analyses/<id>/{logs/, SUMMARY.md, state.toml, record/{intake.md, inventory.md, findings.md, hypotheses.md, runs/}, reports/<fecha>-<tipo>.md}`. IDs `F-01`/`H-01`, digest arriba de cada `.md`, nada se borra (se marca refuted/superseded). `SUMMARY.md` es lo único que necesita leer un humano. *(C-46: `state.toml`; C-50: curación en vez de "nada se borra")* |
| C-26 | ID de análisis (B2) | `<ref>-<slug>`: `ref` = ticket de Jira si existe; si no, **referencia libre** que pone el usuario (otro ticket, cliente, incidente). Ej: `DEX-1234-black-screen`, `ACME-INC42-black-screen` |
| C-28 | Status/outcome (B2) | Separados. `status`: `new · analyzing · needs-info · concluded · closed`. `outcome` (al concluir): `confirmed · probable · inconclusive · not-an-issue` |
| C-31 | Idioma de los análisis (B2) | **Configurable en init**, por defecto español. Términos técnicos en inglés (no traducir conceptos de logs). Claves TOML, nombres de archivos, valores de status y estructura siempre en inglés. Excerpts de log verbatim |
| C-32 | Salidas de scripts (B2) | El subagente vuelca lo relevante con citas en los `.md` de `record/`. El inventario técnico (aliases de archivo, identidad de pantalla) se cachea en `record/runs/manifest.json`. Salidas completas solo con `--save` en `record/runs/`. Scripts determinísticos: re-ejecutar en vez de guardar todo |
| C-33 | Búsqueda (B2) | `loga_search.py` lee en el momento todos los `analyses/*/state.toml` y filtra por status, outcome, platform, player_version, tags, jira o título. Sin índice persistido |
| C-34 | Multi-pantalla (B2) | `record/comparison.md` **condicional** (solo con 2+ pantallas o grupos): matriz pantalla × métrica con citas. Los hallazgos puntuales siguen en `findings.md` con campo `screen` |
| C-35 | Flujo (B3) | 6 pasos: `new` (carpeta + state + búsqueda de relacionados) → `intake` (grill-me) → `inventory` (scan + metadata sugerida) → `analyze` (loop findings/hypotheses/comparison; `needs-info` si falta) → `report` (template + verificación de citas + SUMMARY) → `close`. `state.toml` y `SUMMARY.md` se actualizan en cada paso. Se puede saltar o volver pasos con confirmación |
| C-36 | Gates (B3) | 2 gates duros: (1) no consultar logs sin intake mínimo (síntoma + qué se esperaba + logs presentes); (2) no emitir report si las citas `archivo:línea` no verifican |
| C-37 | Delegación (B3) | Inline: estado, búsqueda, progreso, crear carpeta, actualizar state/SUMMARY. **Consultas de logs muy chicas también inline, con guard**: si supera un umbral (cantidad de archivos o tamaño de salida), pasa a subagente. Umbral exacto a definir en el plan |
| C-38 | Init IAs (B3) | **Solo validación estática**, sin consumo de tokens: CLI `claude`/`codex` en PATH + versión, adapters `.claude/agents` y `.codex/agents` presentes y válidos, wrappers `CLAUDE.md`/`AGENTS.md`, Python ≥ 3.11. No lanza subagentes. *(superado por C-68: sin smoke test)* |
| C-39 | Paridad Codex (B3) | Workers nativos vía `.codex/agents`. Si no están disponibles, **fallback inline declarado**: la skill corre en el contexto principal, se avisa la degradación y se mantiene el mismo contrato (archivos y formato de retorno) |
| C-40 | Set de skills (B4) | `orchestrator/LOGA-RUNTIME.md` (cargado por wrapper, no es skill) + skills `loga-init` (sesión principal), `loga-intake` (grill-me), `loga-inventory` (worker), `loga-analyze` (worker), `loga-report` (worker), `loga-scripts` (referencia, la cargan inventory y analyze) + 3 contratos `_shared` (flow, persistence, user-interaction) + perfiles de worker *(superado por C-63: un solo `loga-worker`)*. `new`/`close` son operaciones de estado del orquestador vía script. Skills agregadas después: `loga-explorer` (C-49), `loga-challenger` (C-43) |
| C-41 | Grill-me (B4) | `loga-intake` corre en la **sesión principal**: bloques de máx. 5 preguntas con "por qué importa", escribe `record/intake.md` y deja solo el digest en contexto. Reutilizable cuando falta info (`needs-info`) |
| C-42 | Escritura (B4) | **El subagente escribe sus propios archivos** (write scope limitado a `analyses/<id>/record/` y `reports/`) y devuelve un retorno corto de 5 campos + digest |
| C-43 | Challenger (B4) | **Subagente opt-in** `loga-challenger`, que el usuario pide explícitamente: busca explicaciones alternativas, falta de cobertura y correlación tomada como causa. Escribe `record/challenge.md`. Usa el worker único (C-63) |
| C-30 | Scripts (B5) | **Scripts sueltos y finos** (`scripts/loga_<nombre>.py`) sobre la librería compartida `scripts/loga_core/` (parser, profiles, salida acotada, encoding, citas). Helper común obligatorio para flags, formato de salida y exit codes. Un script no importa otro: la lógica compartida va en el core. `loga_index.py` lista los scripts leyendo su `SPEC`. Reversible: se puede agregar un dispatcher después |
| C-44 | Set de scripts v1 (B5) | **Estado (6)**: `loga_doctor`, `loga_new`, `loga_progress` (progreso derivado + próximo paso + valida state), `loga_search`, `loga_verify_citations`, `loga_index`. **Consulta de logs (10)**: `loga_scan`, `loga_summary`, `loga_grep`, `loga_window`, `loga_sessions`, `loga_resources`, `loga_gaps`, `loga_check`, `loga_compare`, `loga_cluster` (resuelve X-10) |
| C-45 | Umbrales (B5) | **v1 solo mide**: compara contra el rango observado (corpus y otras pantallas), sin veredicto. `thresholds` opcional y vacío: si se carga un umbral, el script lo usa y lo indica |
| C-46 | Formato de datos (B5) | **TOML sin dependencias**: `state.toml`, catálogo y config en TOML (`tomllib`, stdlib desde Python 3.11; los scripts solo leen, escribe el agente). Único requisito: Python ≥ 3.11. Init detecta el comando de Python (`python3`/`python`/`py`) y lo guarda en config; las skills usan ese valor. Resuelve X-14 y **modifica C-25** (`state.yaml` → `state.toml`) |
| C-47 | Extensibilidad (B5) | **Manual, sin mecanismo automático** (modifica el alcance de C-11): el usuario agrega o ajusta scripts y patrones a mano en el repo cuando cambien los logs o haya flujos nuevos. Sin `_templates/`, `CONTRIBUTING`, `selftest`, auto-registro ni sistema de profiles/plugins. Solo organización interna: lo específico del formato Dex Player centralizado en `loga_core`, cada script con `SPEC` corto para `loga_index`. `docs/scripts-idea/` es la referencia para replicar |
| C-48 | Catálogo (B5) | Patrones y firmas de bugs conocidos en **archivo de datos TOML** (`scripts/catalog.toml` o uno por dominio) que se edita a mano; lo leen `loga_check`/`loga_grep` |
| C-49 | Explorer (B4) | Nueva skill worker **`loga-explorer`**: lee los logs directamente, por fragmentos acotados (ventanas de tiempo, zonas alrededor de errores/huecos, trozos de N líneas), para buscar más allá de scripts y patrones confirmados. **El orquestador la propone** tras 2+ rondas de analyze sin progreso (con motivo, el usuario confirma); también se puede pedir a mano. Escribe `record/exploration.md`: hallazgos **exploratorios, no confirmados por script** + sección de **patrones candidatos** (insumo para extender scripts a mano). Un hallazgo exploratorio no alcanza para `outcome: confirmed` sin verificación por script o validación del usuario |
| C-50 | Rondas e iteración (B2/B3) | Skills repetibles: `loga-intake`, `loga-analyze`, `loga-inventory` (logs nuevos), `loga-explorer`, `loga-challenger`. Se persisten en los **mismos archivos** con entradas etiquetadas por ronda (`F-07 [R3]`) + `rounds[]` corto en `state.toml` (`{n, skill, question, result: progress|no-progress}`), que alimenta el disparador del explorer. **Curación inteligente** (modifica "nada se borra" de C-25): al revalidar y descartar un punto, se saca del cuerpo vigente y queda en una sección `Discarded` de una línea con motivo y ronda. Así se conserva lo importante de cada ronda para los reportes (ruled out) sin ruido. `SUMMARY.md` muestra solo lo vigente |
| C-51 | Tamaño de logs (B5) | Archivos < 5 MB (se manejan chunks de 5 MB), **3-5 archivos por análisis**, a veces algunos más. Ejemplos en `/Users/nicolasschmidt/Documents/SIA/log_analyzer/logs_examples` (fuera del repo) |
| C-52 | Insumos (B5) | Hay logs reales de ejemplo; **no existen** los scripts de medición del corpus (`profile.py`, `flows.py`) |
| C-53 | Reports (B6) | 2 tipos: `reports/<YYYYMMDD>-findings.md` (digest, problema, conclusión confirmed/probable, evidencia F-xx con cita, descartado, comparación condicional, límites, acción sugerida, bloque Jira) y `reports/<YYYYMMDD>-status.md` (digest, qué se sabe, hipótesis vigentes + qué las confirmaría, descartado, qué falta / preguntas abiertas, próximos pasos, bloque Jira). Bloque Jira de 5-8 líneas para pegar |
| C-54 | SUMMARY (B6) | Vivo y corto (~1 pantalla), reescrito en cada paso, solo lo vigente: título con ref, status/outcome/ronda, platform/player/screens, problema, hallazgos vigentes, hipótesis vigentes, descartado, próximo paso + preguntas abiertas, links a reports |
| C-55 | Fuera de v1 (B7) | Confirmado todo fuera (ver §3) |
| C-56 | Permisos (B7) | `.claude/settings.json` con **allowlist mínima**: correr `scripts/loga_*.py` y escribir en `analyses/` sin confirmación. Sin deny de lectura de logs (el explorer los necesita; el límite lo ponen skills y guard). En Codex se documenta el equivalente, sin forzarlo |
| C-57 | Aceptación (B7) | Último stage: flujo completo sobre **2-3 casos reales de `logs_examples` con problema conocido que elige el usuario**, comparando con lo ya sabido. Checklist de aceptación escrito en el plan. Sin evals |
| C-58 | Perfil challenger (B7) | *(superado por C-61 y C-63: sin modelos por perfil y un solo `loga-worker`)* |
| C-59 | Layout (P-01) | **Sin carpeta `schemas/`** (modifica C-04): la forma de `state.toml` la definen `templates/state.toml` + `loga-persistence-contract` y la valida `loga_progress.py` |
| C-60 | Skills (P-01) | Las skills viven en `skills/` y **init las copia** a `.claude/skills/` y `.agents/skills/` (gitignoradas), para tener slash commands y listado nativo. `loga_doctor` detecta drift entre origen y copia |
| C-61 | Perfiles (P-08) | Los adapters **no definen modelo ni effort**: heredan los de la conversación principal (en Claude se omite `model`; en Codex se omite la clave `model`). Los perfiles quedan solo como rol: skills permitidas, tools y write scope |
| C-62 | Stages (P-10) | 5 stages: S1 base y contratos · S2 core + scripts de estado · S3 scripts de consulta · S4 orquestador, skills, agentes e init · S5 aceptación y guía. S4 puede ir en paralelo con S3 después de S2 |
| C-63 | Perfil único (P-08) | **Un solo worker `loga-worker`** (adapter `.md` para Claude, `.toml` para Codex), sin modelo ni effort. Escribe solo en `analyses/<id>/{record,reports}`; el handoff indica qué skill ejecutar (modifica C-40 y C-58: ya no hay 2 perfiles) |
| C-64 | Formatos (P-02, P-03) | Aprobados tal como están en `04-plan-outline.md`: `state.toml` completo y entradas `F-xx`/`H-xx` con digest arriba y sección `Discarded` |
| C-65 | Contrato de salida (P-04) | Aprobado: envelope JSON en la 1ª línea + markdown; `--max-chars` 8000 (techo 40000); `--limit`/`--offset`; citas `path:línea` con alias `F1`; líneas cortadas a 300 caracteres; ruido contado; exit codes 0/2/3/4/5/1; `--save`; UTF-8 forzado; sin pipes en las skills |
| C-66 | Guard inline (P-05) | Aprobado: un script por turno con `--max-chars ≤ 4000`, máximo 2 archivos, máximo 2 consultas inline seguidas. El orquestador nunca usa `Read` sobre logs ni escribe en `record/` |
| C-67 | Ruteo y handoff (P-06, P-07) | Aprobados tal como están en `04-plan-outline.md` |
| C-68 | Init (P-09) | Aprobado **sin smoke test** (modifica C-38): 1) detectar si ya está configurado · 2) detectar Python ≥ 3.11 · 3) preguntar idioma e IAs · 4) crear `analyses/`, verificar `.gitignore`, escribir `loga.config.toml` · 5) copiar skills a `.claude/skills` y `.agents/skills` · 6) validación estática (CLIs, adapters, wrappers, settings) · 7) cierre: resumen ok/partial + **indicación muy breve de uso con un par de casos de ejemplo**. El fixture sintético queda solo para pruebas manuales de scripts (S3/S5), no para init |
| C-69 | Idioma del harness | **Todo el harness en inglés**: skills, contratos, orquestador, adapters, wrappers, templates, scripts, comentarios, `README` y `USER_GUIDE`. **Configurable en init (default `es`)**: el chat y la prosa de los análisis (`SUMMARY`, `record/`, `reports/`). Los documentos de `docs/plan/` quedan en español (C-19). Refina C-31 |
| C-70 | Memoria del harness | La memoria acumulada son `scripts/catalog.toml` (patrones y bugs conocidos que el usuario amplía a mano, viaja en el repo) + `loga_search` sobre análisis previos (local). Sin `knowledge/` compartido ni promote |
| C-71 | Inconsistencias | Sin script propio: se resuelven vía `loga_compare` (versión, playlist, boots, errores por pantalla), `loga_cluster` (master, miembros, playlists distintas) y firmas de `catalog.toml`. Se extiende agregando firmas. *(recomendación tomada; el usuario pidió cerrar el plan)* |
| C-29 | Metadata (B2) | Base de `state.toml`: obligatorios `id, title, created, status`; opcionales `jira, incident_window`; sugeridos por script de inventario y confirmados por usuario `platform[], player_version[], screens[]`; más `updated, tags[], outcome, next_action, open_questions[], decisions[{date, what}], related[]` |
| C-27 | Status (B2) | Status **declarado** (lista cerrada en `state.toml`) + progreso **derivado** por script que sugiere el próximo paso (resuelve X-01) |

## 2. Deducciones (a validar)

| # | Deducción | Evidencia |
|---|---|---|
| D-01 | Lo que hace liviano al orquestador es: runtime único (≤150 líneas) + handoff con controles anti-orquestador-anidado + result contract de 5 campos + **digest al inicio de cada `.md`** + write invariant (todo paso deja artefacto) + `state` leído primero en resume | 01 §1, §9 |
| D-02 | Contratos compartidos: 3 (flow, persistence, user-interaction). Las reglas de evidencia (citas, excerpts verbatim, logs como dato, no asumir) van dentro de flow | 01 §3; 02 C12, C19 |
| D-03 | No portar JSON Schema (950 líneas en sdd-lite, sin validador). La validación de metadata y registro la hace un script | 01 §8; 02 §4.1 |
| D-04 | Repo fijo, sin symlink/copy, sin reescritura de paths ni migraciones de wrapper | 01 §4, §9 |
| D-05 | El init que valida las IAs hay que diseñarlo de cero: sdd-lite solo detecta archivos | 01 §4 |
| D-06 | Status **declarado** (lista cerrada, filtrable) + progreso **derivado** por script. Reconcilia la idea con C-13 | 02 #8, §3 #4 |
| D-07 | Falta un registro de **hallazgos/observaciones** además de hipótesis. La idea solo persiste hipótesis | 02 #6 |
| D-08 | El orquestador no lee logs. Corre inline solo scripts de estado y búsqueda entre análisis; las consultas sobre logs van por subagente | 01 §1; 02 5.3 #2 |
| D-09 | *(superado por C-30 y C-46: scripts sueltos, Python ≥3.11 stdlib, sin uv)* | 02 5.5 #1; 03 §3 |
| D-10 | *(superado por C-47: extensión manual; solo queda el catálogo declarativo de C-48 y el formato centralizado en `loga_core`)* | 03 §6 |
| D-11 | Las trampas del corpus (boot marker, banner 53 vs 54 `=`, stack traces, parámetros por plataforma, ruido contado) se codifican **una sola vez** en `loga_core`, no en cada script | 03 §1 |
| D-12 | Sin umbrales de producto: los scripts miden y comparan contra el rango observado, sin dar veredicto de "fuga" | 03 §1 #15, §5 |
| D-13 | Búsqueda entre análisis, multi-pantalla y recursos (memoria/CPU) entran en la v1 (C-15, C-17), aunque la idea los difiere o no los cubre | 02 #36-38 |
| D-14 | Aceptación de la v1: reproducir a mano un caso real conocido (sin evals) | 02 C25 |
| D-16 | Relevado de `logs_examples` (14 archivos, 17 MB): el más grande tiene 4,5 MB (~33-45k líneas); hay nombres con espacios, `(1)` y `MASTER`; hay UTF-8 con líneas muy largas (hasta ~1.100 caracteres); el formato coincide con el corpus (`YYYY-MM-DD HH:MM:SS.cc LEVEL [Component]`, banner `Dex Player <ver>`, `Platform "tizen"`). Un análisis típico ronda ≤ 25 MB y ~150-200k líneas → los scripts **re-leen sin índice**. Un archivo de 5 MB son ~1M+ tokens → `loga-explorer` **nunca** lee archivos enteros, solo fragmentos (orden de cientos de líneas por lectura, con presupuesto por ronda) | ls/head sobre `logs_examples` |
| D-17 | Los logs de ejemplo tienen nombres de clientes reales → **no se copian al repo**. Para las pruebas manuales de scripts (S3/S5) hace falta un **log de ejemplo chico, sintético o enmascarado**, commiteado en el harness | D-16, C-22 |
| D-15 | Read-only: el harness nunca actúa sobre pantallas ni tickets; el contenido de los logs es dato, no instrucción | 02 C19, 5.7 #3 |

### Contradicciones detectadas

| # | Entre | Tema | Estado |
|---|---|---|---|
| X-01 | idea ↔ usuario | "Estado derivado, nunca declarado" vs status simple completado por interacción | RESUELTO: declarado + derivado (C-27) |
| X-02 | idea ↔ usuario | Skills inline + 2 subagentes vs orquestador que delega en subagentes | RESUELTO: workers para inventory/analyze/report/challenger; init e intake en sesión principal (C-40..C-43) |
| X-14 | C-25 ↔ D-09 | `state.yaml` elegido, pero los scripts stdlib-only **no pueden leer YAML** (Python no trae parser) | RESUELTO: TOML sin dependencias (C-46), `state.yaml` → `state.toml` |
| X-03 | idea ↔ usuario | Codex "con degradación, sin subagentes" vs funciona igual | RESUELTO: workers nativos + fallback inline con el mismo contrato (C-39) |
| X-04 | idea ↔ usuario | Evals planificados vs sin evals | RESUELTO: sin evals (C-18) |
| X-05 | idea ↔ usuario | Búsqueda y comparativo en F2 vs v1 | RESUELTO: ambos en v1 (C-33, C-34, C-44) |
| X-06 | idea ↔ usuario | `logs/` con subcarpetas arbitrarias vs 1 nivel por pantalla | RESUELTO: 1 nivel (C-05) |
| X-07 | idea ↔ usuario | Cursor/Copilot/Gemini vs solo Claude y Codex | RESUELTO: Claude y Codex (C-07) |
| X-08 | idea ↔ análisis | Python + uv + drain3 vs stdlib-only | RESUELTO: Python ≥3.11 stdlib, sin uv ni drain3 (C-46) |
| X-09 | 01 ↔ 02 ↔ 03 | Tres propuestas de persistencia distintas: `state.toml` + md con digest (01) · `record/{analysis.yaml, journal.ndjson}` (02) · `.loga/{manifest.json, runs.ndjson}` (03) | RESUELTO: md por paso + `state.toml` (C-25); manifest en `record/runs/manifest.json` (C-32) |
| X-10 | 02 ↔ 03 | Set de scripts v1 distinto (02: ingest/coverage/absence/counts/metric-series/search/validate… · 03: 13 comandos scan/sessions/summary/…) | RESUELTO: 6 de estado + 10 de consulta (C-44) |
| X-11 | idea ↔ corpus | Líneas `1969-/1970-` "arranque normal" no aparecen en el corpus | ABIERTO (menor): se verifica contra `logs_examples` al implementar `loga_sessions` (S3) |
| X-12 | idea (interna) | 20 inconsistencias (cantidad de skills, fases, estimaciones, fast path vs gates, inmutabilidad no garantizada) | INFORMATIVO: la idea no es fuente de verdad |

## 3. Alcance v1 — entra / no entra

### Entra

| Área | Qué | Ref |
|---|---|---|
| Repo | `harness/log-assist/` = raíz clonable; `analyses/` local y gitignorada | C-21, C-22 |
| Orquestador | `orchestrator/LOGA-RUNTIME.md` liviano: flujo de 6 pasos, 2 gates, delegación con guard inline, propuesta de explorer tras 2+ rondas sin progreso | C-35..C-37, C-49 |
| Skills | `loga-init`, `loga-intake`, `loga-inventory`, `loga-analyze`, `loga-report`, `loga-scripts`, `loga-explorer`, `loga-challenger` (opt-in) | C-40, C-43, C-49 |
| Contratos | `_shared`: flow, persistence, user-interaction | C-40 |
| Agentes | 1 worker `loga-worker` sin modelo ni effort, con adapters `.claude/agents` y `.codex/agents`; fallback inline declarado en Codex | C-39, C-61, C-63 |
| Wrappers | `CLAUDE.md`, `AGENTS.md` | C-21 |
| Permisos | `.claude/settings.json` con allowlist mínima | C-56 |
| Init | Estructura + config (idioma, comando de Python) + copia de skills + validación estática de IAs y runtime + cierre con uso breve | C-46, C-60, C-68 |
| Persistencia | `analyses/<ref>-<slug>/{logs/, SUMMARY.md, state.toml, record/{intake, inventory, findings, hypotheses, comparison?, exploration?, challenge?}.md + runs/, reports/}` con rondas y curación | C-25..C-29, C-32, C-34, C-50 |
| Scripts | Python ≥ 3.11 stdlib, scripts sueltos + `loga_core`; 6 de estado + 10 de consulta; `catalog.toml` | C-30, C-44, C-46, C-48 |
| Templates | `state.toml`, `SUMMARY.md`, `record/*.md`, `reports/{findings,status}.md` | C-53, C-54 |
| Aceptación | 2-3 casos reales elegidos por el usuario | C-57 |

### No entra (C-55)

- `knowledge/` compartido, promote vía PR, índice de síntomas
- Drain3 / template mining con dependencias
- Evals, backtest, tests de alucinación
- Redacción, gitleaks, CI, export sanitizado
- Integración con API o MCP de Jira (solo metadata manual)
- Cursor, Copilot, Gemini
- Modo auto (solo interactivo)
- Scripts: playback, network, menuboard, storage, display, timeline, trace, bisect, anomaly
- Sistema de extensión (templates, selftest, plugins, profiles), validación de IAs con subagente real
- Archivo de i18n (el idioma es un setting de init + templates)
- Hipótesis "sellada", mínimo de N hipótesis
- `archive/` de análisis (se filtra por status `closed`)
- Logs comprimidos (`.gz`, `.zip`)

## 3.b Revalidación contra el pedido inicial

Chequeo de las 68 decisiones contra el primer mensaje del usuario.

### Cubierto y consistente

| Pedido inicial | Dónde queda |
|---|---|
| Carpeta base `harness/log-assist/*` | C-21 |
| Orquestador principal, liviano, que no carga contexto y guía al usuario | C-03, C-35, C-37, C-66, D-01 |
| Estructura tipo sdd-lite (skills, orchestrator, templates) | C-21, C-40 |
| Persistencia tipo `openspec/changes` pero más legible | C-25, C-53, C-54 |
| Init que crea estructura y valida IAs | C-38, C-68 |
| Cross IA Claude/Codex | C-39, C-60, C-63 |
| Detectar inconsistencias, bugs conocidos, memoria/CPU | C-44 (`check`+`catalog`, `resources`, `compare`, `cluster`) |
| Cross-log de una pantalla y comparativo entre pantallas | C-34, C-44 (`window`, `compare`, `scan` agrupa por `Machine`) |
| Carpeta por análisis con logs planos o 1 nivel por pantalla | C-05, C-25 |
| Scripts precisos, determinísticos, sin logs enteros en contexto + índice/skill | C-30, C-44, C-65, `loga-scripts`, `loga_index` |
| Skills mínimas usables como subagentes + init + grill-me | C-40, C-41 |
| Jira: ticket, fecha, plataforma, versión, status/metadata | C-26, C-28, C-29 |
| Interactivo, no asume nada, ayuda a confirmar el problema | C-14, C-36, C-41, D-15 |
| Búsqueda simple entre análisis (p. ej. por status) | C-33 |
| Relevamientos con templates simples, incluso sin conclusión (hipótesis) | C-53, C-54 |
| Sin evals | C-18, C-55, C-57 |
| Linux/Mac/Windows | C-46, C-65, C-68 |
| Plan final con índice, resumen, stages y tabla de status | C-20, C-62 |

### Desvíos conscientes (aprobados sobre la marcha, se documentan en el plan)

| # | Pedido inicial | Qué se decidió | Ref |
|---|---|---|---|
| R-1 | "estructura con: skills, schemas, orchestrator, templates" | Sin `schemas/`: la forma la dan templates + contrato y la valida un script | C-59 |
| R-2 | "init … valide que las ias integradas funcionen" | Solo validación estática (CLI en PATH, adapters, wrappers); no se lanza un subagente de prueba | C-38, C-68 |
| R-3 | "los subagentes solo usen scripts para buscar" | `loga-explorer` lee logs crudos por fragmentos acotados; es la excepción explícita, pedida después. Un hallazgo exploratorio no confirma nada sin verificación por script | C-09 vs C-49 |
| R-4 | "extensible con nuevos casos o nuevos tipos de logs" | Extensión **manual**, sin mecanismo automático | C-11 vs C-47 |

### Puntos a dejar explícitos en el plan

- **"Memoria" del harness**: no hay `knowledge/` compartido (C-55). La memoria acumulada son dos cosas: `catalog.toml` (patrones y bugs conocidos que el usuario amplía a mano) y `loga_search` sobre análisis previos.
- **"Inconsistencias"**: se materializan como firmas del catálogo y como filas de `compare`/`cluster` (versiones distintas en un grupo, playlists distintas, relojes desalineados, cobertura dispar). No es un script aparte.
- **Riesgo de tokens del explorer**: presupuesto por ronda y lectura solo por fragmentos.

## 4. Preguntas pendientes (bloques de validación)

| Bloque | Tema | Preguntas clave | Estado |
|---|---|---|---|
| B1 | Topología y distribución | Qué es el repo que se clona · qué se commitea de los análisis · usuarios de la v1 · nombre/prefijos | CONFIRMADO (C-21..C-24, C-30) |
| B2 | **Persistencia** | Layout de la carpeta de análisis · id de carpeta (Jira) · status declarado/derivado + lista · metadata Jira · formato del registro (hallazgos, hipótesis, decisiones) · `.md` humanos y digest · salidas de scripts · idioma de los `.md` | CONFIRMADO (C-25..C-29, C-31..C-34). El detalle de secciones de cada `.md` se define en los templates (B6) |
| B3 | Orquestador y flujo | Pasos/estados del análisis · gates obligatorios · inline vs subagente · buscar relacionados al inicio · profundidad de validación de IAs en init · paridad Codex · modo auto | CONFIRMADO (C-35..C-39). Pendiente: umbral del guard inline (plan); modo auto → B7 |
| B4 | Skills y subagentes | Set v1 · grill-me como skill propia · challenger · hipótesis del usuario | CONFIRMADO (C-40..C-43). Deducido a validar en el plan: la hipótesis del usuario se registra como `H-xx` con `source: user`; el challenger escribe `record/challenge.md` condicional |
| B5 | Scripts | Runtime/uv en Windows · CLI + plugins · TOML vs YAML · catálogo y firmas · set v1 · tamaño de logs · umbrales · formatos futuros · shell en Windows · scripts de medición existentes | CONFIRMADO (C-30, C-44..C-48, C-51, C-52). Deducido: sin pipes ni quoting complejo en las skills (mismo comando en PowerShell y bash); formatos futuros se agregan a mano (C-47) |
| B6 | Relevamientos | Tipos de template · bloque para Jira · citas verificadas | CONFIRMADO (C-53, C-54). Las secciones de `record/*.md` se detallan en el plan |
| B7 | Fuera de alcance | Confirmar exclusiones | CONFIRMADO (C-55..C-58) |
