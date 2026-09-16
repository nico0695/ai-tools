# 04 · Esqueleto del plan + puntos a validar

Base para generar `../log-assist-plan.md`. Todo sale de `00-decisions-log.md` (refs `C-xx`/`D-xx`).
Los puntos **P-xx** son propuestas de detalle que faltan validar antes de escribir el plan final.

## A. Estructura del documento final

1. Resumen (qué es, qué hace la v1, en 10 líneas)
2. Alcance v1: entra / no entra
3. Decisiones clave (tabla con refs)
4. Arquitectura: layout del repo, capas, Claude/Codex
5. Persistencia: carpeta de análisis, `state.toml`, `record/`, rondas y curación, reports, `SUMMARY.md`, búsqueda
6. Orquestador y flujo: pasos, gates, guard inline, ruteo, handoff/result, disparador del explorer
7. Skills y agentes: catálogo, perfiles, adapters, fallback
8. Scripts: runtime, estructura, contrato de salida, set v1, catálogo, extensión manual, cross-OS
9. Init
10. Templates
11. Stages (detalle, entregables, criterio de done)
12. Aceptación (checklist + casos reales)
13. Riesgos y pendientes
14. Tabla de status por stage
15. Referencias (`temp/`, `docs/idea`, `docs/scripts-idea`, sdd-lite)

---

## B. Puntos a validar

### P-01 · Layout del repo (raíz clonable)

```
log-assist/
├── README.md                     # qué es + quickstart
├── AGENTS.md                     # wrapper (Codex); bloque común de reglas
├── CLAUDE.md                     # wrapper (Claude); mismo bloque común + sección Claude
├── .gitignore                    # analyses/, loga.config.toml
├── loga.config.example.toml      # init lo copia a loga.config.toml (local por máquina)
├── .claude/
│   ├── settings.json             # allowlist mínima (C-56)
│   └── agents/                   # loga-analyst.md, loga-investigator.md
├── .codex/
│   └── agents/                   # loga-analyst.toml, loga-investigator.toml
├── orchestrator/
│   └── LOGA-RUNTIME.md
├── skills/
│   ├── _shared/                  # loga-flow-contract, loga-persistence-contract, loga-user-interaction-contract
│   ├── loga-init/  loga-intake/  loga-inventory/  loga-analyze/
│   ├── loga-explorer/  loga-challenger/  loga-report/  loga-scripts/
├── templates/
│   ├── state.toml  SUMMARY.md
│   ├── record/                   # intake, inventory, findings, hypotheses, comparison, exploration, challenge
│   └── reports/                  # findings.md, status.md
├── scripts/
│   ├── loga_core/                # lectura, parser Dex Player, TOML, salida, citas
│   ├── loga_<nombre>.py          # 16 scripts (C-44)
│   ├── catalog.toml              # patrones + firmas de bugs conocidos (C-48)
│   └── fixtures/sample.log       # log sintético para smoke test (D-17)
├── docs/                         # idea/, scripts-idea/, plan/ (existentes) + USER_GUIDE.md
└── analyses/                     # creada por init, gitignorada
```

Cambios frente a lo acordado, a validar:
- **Sin carpeta `schemas/`** (D-03): la forma de `state.toml` la define `templates/state.toml` + `loga-persistence-contract` y la valida `loga_progress.py`. C-04 mencionaba `schemas/`.
- **Descubrimiento de skills sin copias ni symlinks**: las skills viven solo en `skills/`. Los wrappers y adapters las referencian **por path** (Claude y Codex hacen `Read skills/<x>/SKILL.md`). Ventaja: una sola copia y cero problemas en Windows. Costo: no aparecen como `/loga-init` en Claude ni en el listado nativo de Codex; se invocan pidiéndoselo al orquestador ("iniciá", "nuevo análisis"). Alternativa: init copia `skills/` a `.claude/skills/` y `.agents/skills/` (gitignoradas), lo que habilita slash commands pero crea copias que se pueden desactualizar.

### P-02 · `state.toml` completo

```toml
id = "DEX-1234-black-screen-tizen"
title = "Pantalla negra tras cambio de playlist"
jira = "DEX-1234"                 # opcional
created = 2026-09-13
updated = 2026-09-13
incident_window = "2026-09-10..2026-09-12"   # opcional
platform = ["tizen"]              # sugerido por loga_scan, confirmado por usuario
player_version = ["6.4.2408.2600"]
screens = ["P1", "P3", "P4"]
tags = ["black-screen", "playlist"]
status = "analyzing"              # new|analyzing|needs-info|concluded|closed
outcome = ""                      # confirmed|probable|inconclusive|not-an-issue
current_round = 3
next_action = "Confirmar si el negro coincide con el cambio de playlist"
open_questions = ["¿Hubo corte de red en ese horario?"]
related = []                      # ids de otros análisis

[[decisions]]
date = 2026-09-13
what = "Ignorar P2: sin logs del día"

[[rounds]]
n = 1
skill = "loga-inventory"
question = "Inventario inicial"
result = "progress"               # progress|no-progress
```

### P-03 · Formato de entradas en `record/`

Todos los `.md` abren con `## Digest` (3-6 bullets: vigentes, descartados, última ronda, bloqueo). El orquestador lee solo eso.

`findings.md`
```
### F-02 [R1] Reinicio inesperado cada ~6 h en P3
- screen: P3 · source: script (loga_sessions) | exploratory | user
- evidence: `logs/P3.log:1234` — "<excerpt verbatim ≤200>"
- confidence: high | medium | low
...
## Discarded
- F-03 [R1→R2] Falso positivo: el hueco era política de apagado (`logs/P3.log:88`)
```

`hypotheses.md`
```
### H-01 [R2] El negro lo causa JSON corrupto al cambiar de playlist
- status: open | supported | refuted
- source: analysis | user | explorer
- confirmaría: … · refutaría: …
- a favor: F-02, F-05 · en contra: —
```

- `intake.md`: síntoma · alcance (pantallas, fechas) · qué se esperaba · qué cambió · qué ya se probó · hipótesis del usuario (→ H-xx `source: user`) · preguntas abiertas
- `inventory.md`: tabla de archivos (alias F1…, screen, platform, version, rango, líneas, parse_rate, boots) · cobertura y huecos · metadata sugerida
- `comparison.md` (condicional): matriz pantalla × métrica con citas
- `exploration.md`: fragmentos leídos (archivo:rango) · hallazgos `E-xx` exploratorios · **patrones candidatos** `P-xx` (regex o secuencia + cita)
- `challenge.md`: checklist (cobertura, correlación ≠ causa, alternativas, hipótesis del usuario) · veredicto por H-xx

Curación (C-50): lo descartado sale del cuerpo y pasa a `## Discarded` en una línea con motivo y ronda.

### P-04 · Contrato de salida de los scripts

- **stdout**: 1ª línea envelope JSON `loga {"script","ok","returned","total","truncated","warnings","next":[…]}` + cuerpo markdown compacto
- `--format md|json` · `--max-chars` default **8000**, techo 40000 · `--limit` / `--offset` para paginar (re-ejecución determinística)
- Citas: `path:línea` POSIX relativo a la carpeta del análisis; alias `F1…` con leyenda al pie cuando hay >1 archivo
- Líneas largas cortadas a 300 caracteres con `…[+N chars]`
- Ruido oculto siempre contado en el envelope
- Exit codes: `0` ok (incluye 0 resultados) · `2` args · `3` input (archivo inexistente o formato no reconocido) · `4` parcial (algún archivo con parse_rate bajo) · `5` verificación fallida · `1` error interno
- `--save` guarda la salida completa en `record/runs/`; `loga_scan` siempre cachea `record/runs/manifest.json`
- UTF-8 forzado en stdout; lectura binaria partida por `\n` (números de línea iguales a los del editor)
- Las skills nunca usan pipes, `head` ni `grep` del shell: todo filtro es un flag (mismo comando en PowerShell y bash)

### P-05 · Guard de consultas inline del orquestador (C-37)

Inline permitido solo si se cumplen **todas**:
1. un solo script de consulta por turno, con `--max-chars 4000` o menos
2. sobre 2 archivos como máximo
3. como máximo 2 consultas inline seguidas sin delegar

Si no, delega en `loga-analyze`. El orquestador **nunca** usa `Read` sobre logs (eso es solo del explorer, como worker). Un resultado inline que merece quedar como hallazgo se pasa a `loga-analyze` para que lo registre: el orquestador no escribe `record/`.

### P-06 · Tabla de ruteo del orquestador

| Situación (`state.toml` + `loga_progress`) | Siguiente acción | ¿Confirma el usuario? |
|---|---|---|
| Sin `loga.config.toml` | `loga-init` | sí |
| Pedido de análisis nuevo | `loga_new` + `loga_search` de relacionados | sí (id y relacionados) |
| `status=new`, sin intake | `loga-intake` | — |
| Intake ok, sin logs en `logs/` | pedir logs | — |
| Intake + logs, sin inventory | `loga-inventory` → confirmar metadata → `analyzing` | sí (metadata) |
| `analyzing` | `loga-analyze` con la pregunta de la ronda | sí (pregunta) |
| 2+ rondas `no-progress` seguidas | proponer `loga-explorer` | sí |
| Falta info | `needs-info` + `loga-intake` o pedir logs | — |
| Hipótesis `supported` y el usuario quiere cerrar | opcional `loga-challenger` → `loga-report` (findings) | sí |
| Sin conclusión y el usuario quiere pausar o cerrar | `loga-report` (status) | sí |
| Report emitido | `concluded` + outcome → `close` cuando el usuario lo indique | sí |

### P-07 · Handoff y retorno de workers

- **Handoff**: `loga_role: worker`, `skill`, `analysis_id`, `round`, `question`, rutas relevantes + digests, `orchestration_allowed: false`, `python_cmd`, `language`
- **Retorno (5 campos)**: `status` (ok|partial|blocked) · `summary` (≤5 líneas) · `artifacts` (archivos escritos) · `next_action` · `open_risks`. Opcionales: `round_result` (progress|no-progress) · `decision_required` + `options`
- El worker actualiza su `.md` + digest. El orquestador actualiza `state.toml` (rounds, status) y `SUMMARY.md`

### P-08 · Perfiles de agente (cambia nombres de C-40/C-58)

| Perfil | Tier | Skills | Claude | Codex | Escritura |
|---|---|---|---|---|---|
| `loga-analyst` | mid | inventory, analyze, report | sonnet | gpt-5.6 | `analyses/<id>/record`, `reports` |
| `loga-investigator` | high | explorer, challenger | opus | gpt-5.6-sol | `analyses/<id>/record` |

Motivo: el explorer lee logs crudos y busca lo que los scripts no ven, y el challenger verifica; los dos piden más razonamiento. El report sintetiza sobre registros ya escritos (mid). Los modelos salen del tier map de sdd-lite y se ajustan en el archivo del adapter.

### P-09 · Pasos de `loga-init` (sesión principal, idempotente)

1. Detectar estado: ¿existe `loga.config.toml` y está completo? (rerun = revalidar)
2. Detectar Python ≥ 3.11 probando `python3`, `python` y `py -3`
3. Preguntar idioma (default `es`) e IAs a usar (claude / codex / ambas)
4. Crear `analyses/`, verificar `.gitignore`, escribir `loga.config.toml` (`language`, `python_cmd`, `ai_setups`, `validated_at`)
5. Validación estática (`loga_doctor.py`): CLI en PATH + versión, adapters presentes y parseables, wrappers presentes, `settings.json`
6. Smoke test: `loga_scan.py` sobre `scripts/fixtures/sample.log`
7. Resumen con ok / partial por check y próximo paso ("creá un análisis")

### P-10 · Stages

| # | Stage | Entregables | Done cuando |
|---|---|---|---|
| S1 | Base y contratos | layout, wrappers, `.gitignore`, `settings.json`, config de ejemplo, 3 contratos `_shared`, templates, `fixtures/sample.log` | la estructura existe y los contratos y templates son consistentes con el plan |
| S2 | Core + scripts de estado | `loga_core`, `loga_doctor`, `loga_new`, `loga_progress`, `loga_search`, `loga_verify_citations`, `loga_index` | crean, validan y buscan análisis sobre fixtures en mac y Windows |
| S3 | Scripts de consulta | `loga_scan`, `summary`, `grep`, `window`, `sessions`, `resources`, `gaps`, `check` + `catalog.toml`, `compare`, `cluster` | corren sobre `logs_examples` respetando el contrato de salida y las trampas del corpus |
| S4 | Orquestador, skills, agentes, init | `LOGA-RUNTIME.md`, 8 skills, 2 perfiles × 2 adapters, `loga-init` | un análisis de punta a punta en Claude y en Codex (con fallback) produce todos los archivos |
| S5 | Aceptación y guía | 2-3 casos reales, `README`, `USER_GUIDE.md` | checklist de aceptación en verde |

Dependencias: S1 → S2 → S3. S4 puede arrancar después de S2 en paralelo con S3; `loga-scripts` se cierra al terminar S3. S5 al final.
