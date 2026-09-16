# log-assist — Plan de implementación v1

> Estado del documento: **aprobado para implementar**.
> Fuente de verdad de las decisiones: [`temp/00-decisions-log.md`](temp/00-decisions-log.md) (refs `C-xx`, `D-xx`, `R-x`).
> Análisis de respaldo: [`temp/01-sdd-lite-patterns.md`](temp/01-sdd-lite-patterns.md) · [`temp/02-idea-analysis.md`](temp/02-idea-analysis.md) · [`temp/03-scripts-analysis.md`](temp/03-scripts-analysis.md) · [`temp/04-plan-outline.md`](temp/04-plan-outline.md).

## Índice

1. [Resumen](#1-resumen)
2. [Alcance de la v1](#2-alcance-de-la-v1)
3. [Decisiones clave](#3-decisiones-clave)
4. [Arquitectura](#4-arquitectura)
5. [Persistencia](#5-persistencia)
6. [Orquestador y flujo](#6-orquestador-y-flujo)
7. [Skills y agentes](#7-skills-y-agentes)
8. [Scripts](#8-scripts)
9. [Init](#9-init)
10. [Templates](#10-templates)
11. [Stages](#11-stages)
12. [Aceptación](#12-aceptación)
13. [Riesgos y pendientes](#13-riesgos-y-pendientes)
14. [Tabla de status](#14-tabla-de-status)
15. [Referencias](#15-referencias)

---

## 1. Resumen

`log-assist` es un harness para analizar logs de players de digital signage (Dex Player) con asistencia de IA, inspirado en los patrones de `sdd-lite`.

- **Qué hace**: recibe una carpeta con logs de una o varias pantallas y guía un análisis interactivo para detectar inconsistencias, bugs conocidos y patrones de recursos (RAM/CPU), comparando archivos de una pantalla o varias pantallas entre sí.
- **Cómo lo hace**: un **orquestador liviano** conduce la sesión y delega en subagentes; los subagentes **consultan los logs con scripts determinísticos**, nunca cargan logs enteros en contexto, y persisten lo relevante con citas `archivo:línea`.
- **Qué deja**: una carpeta por análisis con los logs, un registro legible por pasos, metadata ligada a Jira con status, y relevamientos finales (con conclusión o con hipótesis).
- **Cómo se usa**: se clona el repo, se corre `loga-init` y se trabaja conversando con el orquestador, en **Claude Code o Codex indistintamente**.
- **Qué no hace**: no ejecuta acciones sobre pantallas ni tickets, no afirma sin evidencia verificable y no reemplaza el criterio del usuario: ayuda a confirmar o descartar.

## 2. Alcance de la v1

### Entra

| Área | Qué | Ref |
|---|---|---|
| Repo | `harness/log-assist/` como raíz clonable; `analyses/` local y gitignorada | C-21, C-22 |
| Orquestador | `orchestrator/LOGA-RUNTIME.md`: flujo de 6 pasos, 2 gates duros, delegación con guard, propuesta de explorer | C-35..C-37, C-49 |
| Skills | `loga-init`, `loga-intake`, `loga-inventory`, `loga-analyze`, `loga-explorer`, `loga-challenger`, `loga-report`, `loga-scripts` | C-40, C-43, C-49 |
| Contratos | `skills/_shared/`: flow, persistence, user-interaction | C-40, D-02 |
| Agentes | Un worker `loga-worker` sin modelo ni effort, con adapters para Claude y Codex; fallback inline en Codex | C-39, C-61, C-63 |
| Persistencia | `analyses/<ref>-<slug>/` con `logs/`, `SUMMARY.md`, `state.toml`, `record/`, `reports/` | C-25..C-34, C-50 |
| Scripts | Python ≥ 3.11 stdlib; 6 de estado + 10 de consulta sobre `loga_core`; `catalog.toml` | C-30, C-44, C-46, C-48 |
| Init | Estructura, config, copia de skills, validación estática, cierre con uso breve | C-60, C-68 |
| Permisos | `.claude/settings.json` con allowlist mínima | C-56 |
| Aceptación | 2-3 casos reales con problema conocido, elegidos por el usuario | C-57 |

### No entra

`knowledge/` compartido, promote vía PR e índice de síntomas · Drain3 o template mining con dependencias · evals, backtest y tests de alucinación · redacción, gitleaks, CI y export sanitizado · integración con API o MCP de Jira · Cursor, Copilot, Gemini · modo auto · scripts `playback`, `network`, `menuboard`, `storage`, `display`, `timeline`, `trace`, `bisect`, `anomaly` · sistema de extensión automático (plugins, selftest, profiles) · validación de IAs lanzando subagentes · archivos de i18n · hipótesis "sellada" y mínimos de N hipótesis · `archive/` de análisis · logs comprimidos. (C-55)

### Desvíos conscientes respecto del pedido original

| # | Pedido | Decisión | Ref |
|---|---|---|---|
| R-1 | Estructura con `schemas/` | Sin `schemas/`: la forma la dan los templates y el contrato de persistencia, y la valida `loga_progress` | C-59 |
| R-2 | Init que valide que las IAs funcionan | Validación **estática** (CLI en PATH, adapters, wrappers); no se lanza un subagente de prueba | C-68 |
| R-3 | Los subagentes solo usan scripts | `loga-explorer` es la excepción: lee logs por fragmentos acotados y sus hallazgos no confirman nada sin verificación | C-49 |
| R-4 | Extensible con nuevos casos y tipos de log | Extensión **manual** en el repo, sin mecanismo automático | C-47 |

## 3. Decisiones clave

| Tema | Decisión | Ref |
|---|---|---|
| Distribución | El repo se clona y se usa; no hay instalador | C-21 |
| Git | `analyses/` completa gitignorada; todo local | C-22 |
| Usuarios | Perfiles técnicos en Linux, Mac y Windows | C-23 |
| Nombres | Prefijo `loga-` para skills y `loga_` para scripts | C-24, C-30 |
| Persistencia | Un `.md` por paso + `state.toml`, estilo openspec | C-25 |
| Formato de datos | TOML, sin dependencias (`tomllib`, Python ≥ 3.11) | C-46 |
| Status | Declarado (`status`) + progreso derivado por script; `outcome` aparte | C-27, C-28 |
| Escritura | Cada worker escribe sus archivos; el orquestador nunca escribe en `record/` | C-42, C-66 |
| Agentes | Un solo worker sin modelo ni effort: hereda el de la sesión | C-61, C-63 |
| Idioma | Harness en inglés; chat y prosa de los análisis configurables (default `es`) | C-69 |
| Memoria | `catalog.toml` + `loga_search`; sin base de conocimiento compartida | C-70 |
| Evals | No hay; la validación es manual sobre casos reales | C-18, C-57 |

## 4. Arquitectura

### 4.1 Layout del repo

```
log-assist/
├── README.md                     # qué es + quickstart (EN)
├── AGENTS.md                     # wrapper Codex: bloque común + sección Codex
├── CLAUDE.md                     # wrapper Claude: bloque común + sección Claude
├── .gitignore                    # analyses/, loga.config.toml, .claude/skills/, .agents/skills/
├── loga.config.example.toml
├── .claude/
│   ├── settings.json             # allowlist mínima
│   ├── agents/loga-worker.md
│   └── skills/                   # copia generada por init (gitignorada)
├── .codex/
│   └── agents/loga-worker.toml
├── .agents/skills/               # copia generada por init (gitignorada)
├── orchestrator/
│   └── LOGA-RUNTIME.md
├── skills/
│   ├── _shared/                  # loga-flow-contract, loga-persistence-contract, loga-user-interaction-contract
│   ├── loga-init/  loga-intake/  loga-inventory/  loga-analyze/
│   └── loga-explorer/  loga-challenger/  loga-report/  loga-scripts/
├── templates/
│   ├── state.toml  SUMMARY.md
│   ├── record/                   # intake, inventory, findings, hypotheses, comparison, exploration, challenge
│   └── reports/                  # findings.md, status.md
├── scripts/
│   ├── loga_core/                # lectura, parser Dex Player, TOML, salida, citas, helper de CLI
│   ├── loga_*.py                 # 16 scripts
│   ├── catalog.toml              # patrones + firmas de bugs conocidos
│   └── fixtures/sample.log       # log sintético para pruebas manuales
├── docs/                         # idea/, scripts-idea/, plan/, USER_GUIDE.md
└── analyses/                     # creada por init, gitignorada
```

### 4.2 Capas

```
wrapper (CLAUDE.md / AGENTS.md)
   └── orquestador (LOGA-RUNTIME.md)  ── contexto liviano: state + digests
         ├── inline: scripts de estado y consultas mínimas (guard)
         └── worker (loga-worker) ── ejecuta una skill ── scripts de consulta
                                            └── escribe record/ y reports/
```

Regla base: **el orquestador decide y persiste estado; el worker analiza y escribe su artefacto**. Nada de análisis en el contexto principal más allá del guard (§6.3).

### 4.3 Claude y Codex

| Pieza | Neutral | Específico |
|---|---|---|
| Runtime, skills, contratos, templates, scripts | ✅ | — |
| Lanzamiento del worker | — | Claude: tipo de agente `loga-worker`. Codex: rol en `.codex/agents/loga-worker.toml` |
| Descubrimiento de skills | — | Copia a `.claude/skills/` y `.agents/skills/` que hace init (C-60) |
| Fallback | — | Codex sin workers nativos: la skill corre inline, se declara la degradación y se mantiene el mismo contrato (C-39) |

Los adapters **no fijan modelo ni effort**: heredan la sesión (C-61).

### 4.4 Idioma

- **Inglés**: skills, contratos, runtime, wrappers, adapters, templates, scripts, comentarios, `README`, `USER_GUIDE`.
- **Configurable en init, default `es`**: chat y prosa de `SUMMARY.md`, `record/*.md` y `reports/*.md`.
- **Siempre en inglés**: claves TOML, nombres de archivos, ids (`F-01`, `H-01`), valores de `status`/`outcome`.
- **Siempre verbatim**: los excerpts de log no se traducen. (C-69, C-31)

## 5. Persistencia

### 5.1 Carpeta de análisis

```
analyses/<ref>-<slug>/           # ref = ticket Jira o referencia libre (C-26)
├── logs/                        # planos, o logs/<screen>/ con un solo nivel
├── SUMMARY.md                   # lo único que necesita leer un humano
├── state.toml                   # metadata + status + rondas (máquina)
├── record/                      # persistencia del trabajo (equivalente a changes)
│   ├── intake.md
│   ├── inventory.md
│   ├── findings.md
│   ├── hypotheses.md
│   ├── comparison.md            # condicional: 2+ pantallas
│   ├── exploration.md           # condicional: corrió el explorer
│   ├── challenge.md             # condicional: corrió el challenger
│   └── runs/                    # manifest.json + salidas guardadas con --save
└── reports/<YYYYMMDD>-<tipo>.md # findings | status
```

### 5.2 `state.toml`

```toml
id = "DEX-1234-black-screen-tizen"
title = "Pantalla negra tras cambio de playlist"
jira = "DEX-1234"                            # opcional
created = 2026-09-13
updated = 2026-09-13
incident_window = "2026-09-10..2026-09-12"   # opcional
platform = ["tizen"]                         # sugerido por loga_scan, confirmado por el usuario
player_version = ["6.4.2408.2600"]
screens = ["P1", "P3", "P4"]
tags = ["black-screen", "playlist"]
status = "analyzing"       # new | analyzing | needs-info | concluded | closed
outcome = ""               # confirmed | probable | inconclusive | not-an-issue
current_round = 3
next_action = "Confirmar si el negro coincide con el cambio de playlist"
open_questions = ["¿Hubo corte de red en ese horario?"]
related = []

[[decisions]]
date = 2026-09-13
what = "Ignorar P2: sin logs del día"

[[rounds]]
n = 1
skill = "loga-inventory"
question = "Inventario inicial"
result = "progress"        # progress | no-progress
```

Obligatorios: `id`, `title`, `created`, `status`. Los valida `loga_progress` (C-29, C-59).

### 5.3 Entradas de `record/`

Todos los archivos abren con `## Digest` (3-6 bullets: vigentes, descartados, última ronda, bloqueo). **El orquestador lee solo el digest.**

```markdown
### F-02 [R1] Reinicio inesperado cada ~6 h en P3
- screen: P3 · source: script (loga_sessions) | exploratory | user
- evidence: `logs/P3.log:1234` — "<excerpt verbatim ≤200 chars>"
- confidence: high | medium | low

### H-01 [R2] El negro lo causa JSON corrupto al cambiar de playlist
- status: open | supported | refuted
- source: analysis | user | explorer
- confirmaría: … · refutaría: …
- a favor: F-02, F-05 · en contra: —

## Discarded
- F-03 [R1→R2] Falso positivo: el hueco era política de apagado (`logs/P3.log:88`)
```

Contenido por archivo:

| Archivo | Contenido |
|---|---|
| `intake.md` | síntoma · alcance (pantallas, fechas) · qué se esperaba · qué cambió · qué ya se probó · hipótesis del usuario (pasa a `H-xx` con `source: user`) · preguntas abiertas |
| `inventory.md` | tabla de archivos (alias `F1`, screen, platform, version, rango, líneas, `parse_rate`, boots) · cobertura y huecos · metadata sugerida |
| `findings.md` | `F-xx` + `## Discarded` |
| `hypotheses.md` | `H-xx` + `## Discarded` |
| `comparison.md` | matriz pantalla × métrica con citas |
| `exploration.md` | fragmentos leídos (`archivo:rango`) · hallazgos `E-xx` exploratorios · **patrones candidatos** `P-xx` con regex o secuencia y cita |
| `challenge.md` | checklist (cobertura, correlación ≠ causa, alternativas, hipótesis del usuario) · veredicto por `H-xx` |

### 5.4 Rondas y curación

- Cada ronda de una skill repetible suma una entrada a `rounds[]` en `state.toml` con `result: progress | no-progress`.
- Las entradas nuevas se etiquetan con la ronda (`F-07 [R3]`).
- **Curación**: al revalidar y descartar un punto, se saca del cuerpo vigente y queda como una línea en `## Discarded` con motivo y ronda. Se conserva lo necesario para la sección "Descartado" de los reportes, sin acumular ruido. (C-50)
- `SUMMARY.md` muestra solo lo vigente.

### 5.5 Reports y SUMMARY

| Archivo | Secciones |
|---|---|
| `reports/<YYYYMMDD>-findings.md` | digest · problema reportado · conclusión (`confirmed`/`probable`) · evidencia (`F-xx` + cita) · descartado · comparación (condicional) · límites · acción sugerida · bloque Jira |
| `reports/<YYYYMMDD>-status.md` | digest · qué se sabe · hipótesis vigentes y qué las confirmaría · descartado · qué falta y preguntas abiertas · próximos pasos · bloque Jira |
| `SUMMARY.md` | ~1 pantalla: título con ref · status/outcome/ronda · platform/player/screens · problema · hallazgos vigentes · hipótesis vigentes · descartado · próximo paso y preguntas abiertas · links a reports |

El bloque Jira son 5-8 líneas listas para pegar. (C-53, C-54)

### 5.6 Búsqueda entre análisis

`loga_search` lee en el momento todos los `analyses/*/state.toml` y filtra por `status`, `outcome`, `platform`, `player_version`, `tags`, `jira` o texto del título. No mantiene índice, así que no se desincroniza. Es un paso fijo al crear un análisis nuevo. (C-33)

## 6. Orquestador y flujo

### 6.1 Pasos

```
loga-init (una vez por clon)
1. new       crear analyses/<ref>-<slug>/ + state.toml + buscar análisis relacionados
2. intake    grill-me → record/intake.md                              [gate 1]
3. inventory scan de logs → record/inventory.md + metadata sugerida → confirmar
4. analyze   loop de rondas → findings / hypotheses / comparison
             sin progreso 2 rondas → proponer explorer
             falta info → needs-info → intake o pedir logs
5. report    challenger opcional → reports/ + verificación de citas   [gate 2]
6. close     status closed
```

### 6.2 Gates duros

1. **No se consultan logs sin intake mínimo**: síntoma, qué se esperaba y logs presentes.
2. **No se emite un report si las citas `archivo:línea` no verifican** (`loga_verify_citations`, exit 5). (C-36)

### 6.3 Delegación y guard

Inline (orquestador): leer `state.toml` y digests, `loga_progress`, `loga_search`, `loga_new`, actualizar `state.toml` y `SUMMARY.md`.

Consultas de logs inline **solo si se cumplen las tres**:

1. un único script de consulta en el turno, con `--max-chars ≤ 4000`;
2. sobre 2 archivos como máximo;
3. no más de 2 consultas inline seguidas sin delegar.

En cualquier otro caso delega en `loga-analyze`. El orquestador **nunca** usa `Read` sobre logs ni escribe en `record/`: un resultado inline que merece registrarse se pasa a `loga-analyze`. (C-66)

### 6.4 Tabla de ruteo

| Situación (`state.toml` + `loga_progress`) | Acción | Confirma el usuario |
|---|---|---|
| Sin `loga.config.toml` | `loga-init` | sí |
| Pedido de análisis nuevo | `loga_new` + `loga_search` de relacionados | sí (id y relacionados) |
| `status=new`, sin intake | `loga-intake` | — |
| Intake ok, `logs/` vacío | pedir logs | — |
| Intake + logs, sin inventario | `loga-inventory` → confirmar metadata → `analyzing` | sí (metadata) |
| `analyzing` | `loga-analyze` con la pregunta de la ronda | sí (pregunta) |
| 2+ rondas `no-progress` seguidas | proponer `loga-explorer` con el motivo | sí |
| Falta información | `needs-info` + `loga-intake` o pedir logs | — |
| Hipótesis `supported` y el usuario quiere cerrar | `loga-challenger` (opcional) → `loga-report` findings | sí |
| Sin conclusión y el usuario quiere pausar o cerrar | `loga-report` status | sí |
| Report emitido | `concluded` + `outcome`; `close` cuando el usuario lo indique | sí |

### 6.5 Handoff y retorno

- **Handoff**: `loga_role: worker`, `skill`, `analysis_id`, `round`, `question`, rutas relevantes + digests, `orchestration_allowed: false`, `python_cmd`, `language`.
- **Retorno (5 campos)**: `status` (`ok|partial|blocked`) · `summary` (≤ 5 líneas) · `artifacts` · `next_action` · `open_risks`. Opcionales: `round_result` (`progress|no-progress`) y `decision_required` con opciones.
- El worker escribe su `.md` y su digest; el orquestador actualiza `state.toml` (rounds, status) y `SUMMARY.md`. (C-67)

### 6.6 Interacción

Preguntar solo lo que cambia una decisión y nunca lo que un script puede responder. Bloques de hasta 5 preguntas, cada una con "por qué importa", con opción de saltear; lo salteado queda en `open_questions`. Nunca inferir respuestas. (C-14, C-41)

## 7. Skills y agentes

| Skill | Dónde corre | Lee | Escribe | Repetible |
|---|---|---|---|---|
| `loga-init` | sesión principal | repo, entorno | `loga.config.toml`, `analyses/`, copias de skills | idempotente |
| `loga-intake` | sesión principal | `state.toml`, `intake.md` | `record/intake.md` | sí |
| `loga-inventory` | worker | `logs/` vía `loga_scan` | `record/inventory.md`, metadata sugerida | sí (logs nuevos) |
| `loga-analyze` | worker | scripts de consulta, `record/` | `findings.md`, `hypotheses.md`, `comparison.md` | sí |
| `loga-explorer` | worker | logs por fragmentos acotados | `record/exploration.md` | sí (opt-in) |
| `loga-challenger` | worker | `record/`, scripts | `record/challenge.md` | sí (opt-in) |
| `loga-report` | worker | `record/`, `state.toml` | `reports/<fecha>-<tipo>.md` | sí |
| `loga-scripts` | referencia | — | — | la cargan los workers |

Anatomía de cada `SKILL.md` (en inglés): frontmatter `name` + `description` con triggers · `Goal` · `Runtime operating rules` (no orquestar, no leer el runtime, honrar el handoff) · `Scope` (should / should not) · `Reads` / `Writes` / `Scripts` permitidos · `Workflow` (≤ 8 pasos) · `Artifact shape` (apunta al template) · `Validation` (incluye "toda afirmación tiene cita") · `Expected output` (los 5 campos).

`loga-scripts` es corta y estable: invocación canónica, cómo leer el envelope y los exit codes, tabla síntoma → script, y "para la lista viva, correr `loga_index`".

**Agente**: un solo `loga-worker`, sin modelo ni effort, con write scope limitado a `analyses/<id>/{record,reports}` y prohibición de generar subagentes o rutear fases. (C-63)

## 8. Scripts

### 8.1 Runtime y organización

- **Python ≥ 3.11, solo stdlib** (`tomllib` para TOML). Sin `uv`, sin PyYAML, sin Drain3.
- Init detecta el comando (`python3`, `python`, `py -3`) y lo guarda en `loga.config.toml`; las skills usan ese valor.
- **Scripts sueltos y finos** sobre `loga_core`; un script no importa a otro: lo compartido vive en el core. Cada script expone un `SPEC` corto (nombre, pregunta que responde, cuándo usarlo, cuándo no, args, columnas de salida, tamaño típico) que `loga_index` lista. (C-30, C-46)

### 8.2 Contrato de salida

- **stdout**: primera línea con envelope JSON (`script`, `ok`, `returned`, `total`, `truncated`, `warnings`, `next[]`) y luego markdown compacto.
- `--format md|json` · `--max-chars` default 8000, techo 40000 · `--limit` / `--offset` (paginar = re-ejecutar, la salida es determinística).
- Citas `path:línea` POSIX relativas a la carpeta del análisis; alias `F1…` con leyenda al pie cuando hay más de un archivo.
- Líneas largas cortadas a 300 caracteres con `…[+N chars]`; ruido oculto siempre contado en el envelope.
- Exit codes: `0` ok (incluye cero resultados) · `2` args · `3` input · `4` parcial (`parse_rate` bajo) · `5` verificación fallida · `1` error interno.
- `--save` guarda la salida completa en `record/runs/`; `loga_scan` siempre cachea `record/runs/manifest.json`.
- UTF-8 forzado en stdout; lectura binaria partida por `\n` para que los números de línea coincidan con el editor.
- Las skills no usan pipes ni `head`/`grep` del shell: todo filtro es un flag, así el comando es idéntico en PowerShell y en bash. (C-65)

### 8.3 Set v1

**Estado (6)** — los usa el orquestador inline:

| Script | Qué hace |
|---|---|
| `loga_doctor` | verifica runtime, adapters, wrappers y copias de skills |
| `loga_new` | crea `analyses/<ref>-<slug>/` desde los templates |
| `loga_progress` | valida `state.toml`, calcula el progreso derivado y sugiere el próximo paso |
| `loga_search` | busca entre análisis por status, outcome, plataforma, versión, tags, jira o título |
| `loga_verify_citations` | verifica que las citas de un `.md` existan y coincidan (gate 2) |
| `loga_index` | lista scripts (desde `SPEC`) y el contenido del catálogo |

**Consulta de logs (10)** — los usan los workers:

| Script | Pregunta que responde |
|---|---|
| `loga_scan` | qué archivos hay, de qué pantalla y plataforma, qué rango cubren, si parsean |
| `loga_summary` | qué mensajes hay por nivel, componente y forma; ruido contado; ERROR sin stack traces |
| `loga_grep` | líneas que matchean un patrón del catálogo o una regex, paginadas y con citas |
| `loga_window` | contexto alrededor de un timestamp o de `archivo:línea`, con merge multi-archivo |
| `loga_sessions` | cuántas veces arrancó, si fue programado o inesperado, uptime |
| `loga_resources` | RAM y CPU por sesión: mínimo, máximo, tendencia, muestras faltantes |
| `loga_gaps` | qué debería ocurrir cada X y no ocurrió (ausencia y cadencia) |
| `loga_check` | qué firmas de bugs conocidos matchean (`hit`/`miss`/`insufficient_data`) |
| `loga_compare` | matriz pantalla × métrica para el análisis comparativo |
| `loga_cluster` | sync group: master, split-brain, miembros inactivos, playlists distintas |

### 8.4 Trampas del corpus (van una sola vez en `loga_core`)

| # | Trampa | Regla |
|---|---|---|
| 1 | Banner de arranque (53 `=`) vs bloque de cluster (54 `=`) | contar arranques por `^Dex Player [\d.]+$`; confundirlos infla los reinicios un 404 % |
| 2 | Stack traces (`^\s+at\s`) | son el 20 % de las líneas ERROR y no son eventos: se pliegan al evento anterior |
| 3 | Identidad de la pantalla | sale de `Machine:` en el contenido, no del nombre del archivo; los archivos `(1)` son **otras pantallas**, no duplicados |
| 4 | Telemetría por plataforma | webOS reporta cada 300 s y usa 1.064-1.288 Mb; Tizen cada 60 s y usa 648-885 Mb: un umbral único falla |
| 5 | Ruido | el 60 % del volumen son 20 mensajes: se oculta en la vista pero **se cuenta** (varios importan por su ausencia) |
| 6 | Tiempo | sin zona horaria y con saltos hacia atrás en reinicios: ordenar por (archivo, línea) y marcar las comparaciones entre pantallas |
| 7 | Intervalo entre comandos PLAY | es la duración del medio, no una cadencia: no sirve como señal de split-brain |
| 8 | Sin umbrales de producto | los scripts miden y comparan contra el rango observado; sin umbral cargado no hay veredicto |

Fuente: `docs/scripts-idea/` (corpus de 178.415 líneas verificadas).

### 8.5 Catálogo y extensión manual

`scripts/catalog.toml` contiene patrones (id, componente, nivel, regex, ejemplos y contraejemplos, plataformas, si es ruido) y firmas de bugs conocidos (combinación de patrones con `match`, `count >= N per window`, `sequence within`, `absence`, `streak`, más `not_if` para descartes y síntomas en lenguaje natural).

Extender es manual y lo hace el usuario en el repo: agregar una firma al catálogo, agregar un `loga_<consulta>.py` nuevo o ajustar el parser en `loga_core` si cambia el formato del log. No hay plugins, templates de contribución ni selftest. (C-47, C-48)

## 9. Init

`loga-init` corre en la sesión principal y es idempotente:

1. detectar si ya está configurado (`loga.config.toml` completo) → rerun = revalidar;
2. detectar Python ≥ 3.11 probando `python3`, `python`, `py -3`;
3. preguntar idioma (default `es`) e IAs a usar (claude / codex / ambas);
4. crear `analyses/`, verificar `.gitignore` y escribir `loga.config.toml` (`language`, `python_cmd`, `ai_setups`, `validated_at`);
5. copiar `skills/` a `.claude/skills/` y `.agents/skills/`;
6. validación estática con `loga_doctor`: CLI en PATH y versión, adapters presentes y parseables, wrappers presentes, `settings.json`, copias de skills sin drift;
7. cerrar con un resumen `ok`/`partial` por check y **una indicación muy breve de uso con un par de casos de ejemplo**.

No lanza subagentes ni consume tokens de validación. (C-68)

## 10. Templates

| Template | Notas |
|---|---|
| `templates/state.toml` | estructura de §5.2 con comentarios de los valores permitidos |
| `templates/SUMMARY.md` | ~1 pantalla, secciones de §5.5 |
| `templates/record/*.md` | uno por archivo de `record/`, con `## Digest` arriba y el formato de entradas de §5.3 |
| `templates/reports/{findings,status}.md` | secciones de §5.5 + bloque Jira |

Presupuestos: los `.md` de `record/` apuntan a 200-600 palabras; los reports, a menos de 800. Todo paso deja su archivo escrito, aun si quedó bloqueado (write invariant). (D-01)

## 11. Stages

### S1 · Base y contratos

Layout del repo, `.gitignore`, `loga.config.example.toml`, `.claude/settings.json`, wrappers `CLAUDE.md` y `AGENTS.md` (bloque común + sección por plataforma), los 3 contratos `_shared`, todos los templates y `scripts/fixtures/sample.log` (sintético).
**Done**: la estructura existe y contratos y templates son consistentes entre sí y con este plan.

### S2 · Core y scripts de estado

`loga_core` (lectura binaria y encoding, parser Dex Player con las trampas de §8.4, lectura de TOML, helper de CLI con flags/envelope/exit codes, citas y aliases) y los 6 scripts de estado.
**Done**: se crea un análisis, se valida su `state.toml`, se calcula el progreso y se busca entre análisis, en Mac y en Windows.

### S3 · Scripts de consulta

Los 10 scripts de consulta y `catalog.toml` con las primeras firmas (pantalla negra, loop de reinicios, split-brain, sin master, outage de heartbeat, contenido faltante).
**Done**: corren sobre `logs_examples` respetando el contrato de salida, sin violar las trampas del corpus y con salidas deterministas.

### S4 · Orquestador, skills, agentes e init

`LOGA-RUNTIME.md` (≤ 150 líneas), las 8 skills, el adapter `loga-worker` para Claude y Codex, y `loga-init` completo.
**Done**: un análisis de punta a punta produce `state.toml`, `SUMMARY.md`, `record/` y un report, tanto en Claude como en Codex (con fallback declarado si no hay workers nativos).

### S5 · Aceptación y guía

`README.md`, `docs/USER_GUIDE.md` y la corrida de los casos reales.
**Done**: checklist de §12 en verde.

Dependencias: S1 → S2 → S3. S4 puede arrancar después de S2, en paralelo con S3; `loga-scripts` se cierra cuando termina S3. S5 al final.

## 12. Aceptación

Sobre 2-3 casos reales de `logs_examples` con problema conocido, elegidos por el usuario:

1. el flujo completo corre sin intervención manual sobre archivos (solo conversación);
2. el análisis llega a la misma conclusión que ya se conocía, o explica con evidencia por qué no puede;
3. toda afirmación de los reports tiene cita verificada (`loga_verify_citations` en 0);
4. ningún log entero entró en contexto: las lecturas fueron por script o por fragmentos del explorer;
5. `SUMMARY.md` alcanza para entender el caso sin abrir `record/`;
6. `loga_search` encuentra el análisis por status, plataforma y tag;
7. los scripts corren igual en Mac y en Windows (mismos comandos y misma salida);
8. el mismo caso corre en Claude y en Codex con los mismos artefactos.

Sin evals automatizadas. (C-57)

## 13. Riesgos y pendientes

| # | Riesgo | Mitigación |
|---|---|---|
| 1 | El explorer consume muchos tokens o se tienta con leer archivos enteros | presupuesto por ronda, lectura solo por fragmentos, lo pide el usuario, hallazgos marcados como no confirmados |
| 2 | El parser no cubre alguna variante de log y arruina las cuentas | `parse_rate` visible y exit 4 si baja; validación contra `logs_examples` en S3 |
| 3 | Las copias de skills en `.claude/` y `.agents/` se desactualizan | `loga_doctor` detecta drift; init las regenera |
| 4 | Sin evals, una regresión de un patrón pasa desapercibida | ejemplos y contraejemplos por patrón en `catalog.toml`; aceptación manual sobre casos reales |
| 5 | Codex sin workers nativos degrada el aislamiento | fallback inline declarado, mismo contrato de archivos y de retorno |
| 6 | Los logs tienen nombres de clientes reales | `analyses/` gitignorada; fixture sintético para pruebas |
| 7 | Diferencias de shell en Windows (PowerShell vs Git Bash) | sin pipes ni quoting complejo; paths relativos POSIX; alias de archivo en vez de rutas con espacios |
| 8 | El catálogo crece y se solapan firmas | ids únicos y aviso cuando una línea de ejemplo matchea dos patrones del mismo dominio |

Pendientes menores para resolver al implementar: verificar contra `logs_examples` si las líneas `1969-/1970-` son un arranque normal (X-11), y decidir si `catalog.toml` se parte por dominio cuando crezca.

## 14. Tabla de status

| Stage | Objetivo | Depende de | Criterio de done | Estado |
|---|---|---|---|---|
| S1 | Base y contratos | — | estructura, contratos y templates consistentes | ⬜ pendiente |
| S2 | Core y scripts de estado | S1 | crear, validar y buscar análisis en Mac y Windows | ⬜ pendiente |
| S3 | Scripts de consulta | S2 | 10 scripts + catálogo corriendo sobre logs reales | ⬜ pendiente |
| S4 | Orquestador, skills, agentes, init | S2 (paralelo a S3) | análisis completo en Claude y en Codex | ⬜ pendiente |
| S5 | Aceptación y guía | S3, S4 | checklist de §12 en verde | ⬜ pendiente |

Leyenda: ⬜ pendiente · 🟡 en curso · ✅ hecho · ⛔ bloqueado.

## 15. Referencias

| Fuente | Para qué |
|---|---|
| `temp/00-decisions-log.md` | todas las decisiones con su ref y las contradicciones resueltas |
| `temp/01-sdd-lite-patterns.md` | qué patrón de sdd-lite se reutiliza, se adapta o no aplica |
| `temp/02-idea-analysis.md` | análisis crítico del pre-planning previo |
| `temp/03-scripts-analysis.md` | detalle de familias de scripts, contrato y runtime |
| `temp/04-plan-outline.md` | esqueleto y propuestas de detalle validadas |
| `docs/scripts-idea/` | corpus verificado: patrones, flujos y trampas de los logs |
| `docs/idea/` | conceptos de origen (no es fuente de verdad) |
| `sdd/sdd-lite/` | harness de referencia |
