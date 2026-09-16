# 01 · Patrones de sdd-lite para log-assist

Análisis de `sdd/sdd-lite/` como referencia de patrones para `harness/log-assist/`.
Rutas citadas relativas a `sdd/sdd-lite/` salvo prefijo `idea/` (= `harness/log-assist/docs/idea/`) o `C-xx` (= decisiones confirmadas en `00-decisions-log.md`).
Clasificación: **REUTILIZAR** (copiar casi igual) · **ADAPTAR** (con cambio explicado) · **NO APLICA** (con motivo).

## TL;DR

1. El núcleo que vale la pena copiar es chico: runtime hot-path único + handoff con controles anti-orquestador-anidado + result contract de 5 campos + digest al inicio de cada artefacto + "una skill = un artefacto". Eso es lo que hace liviano al orquestador (`orchestrator/SDDL-RUNTIME.md:128-157`, `skills/_shared/sddl-persistence-contract.md:161-166`).
2. `state.yaml` como ancla de resume sirve, pero el de sdd-lite es sobreingeniería (15 campos requeridos, mapa de stages, paths de artefactos que todavía no existen: `schemas/state.schema.yaml:5-20,90-168`). log-assist necesita ~8 campos y un `status` simple (C-13).
3. Los schemas (950 líneas entre los dos) **no tienen validador**: nadie los ejecuta; el LLM "valida" leyéndolos (`skills/sddl-init/SKILL.md:254`, `skills/sddl-proposal/SKILL.md:240`). En v1: sin JSON Schema, o un schema mínimo que valide un script.
4. El init de sdd-lite **no valida que Claude/Codex funcionen**: solo detecta archivos (`CLAUDE.md`, `.claude/`, `AGENTS.md`, `.agents/`, `.codex/`: `skills/sddl-init/SKILL.md:114-127`) y valida estáticamente lo generado (`:276-297`). Lo que pide el usuario (C-06) hay que diseñarlo de cero.
5. Multi-IA: lo neutral es runtime + skills + contratos + templates; lo específico es solo "cómo se lanza un worker" (wrapper + adapter). Patrón `profiles.yaml` → adapters `.claude/agents/*.md` y `.codex/agents/*.toml` es reutilizable, pero con 2-3 perfiles, no 8.
6. sdd-lite es un **paquete que se instala en otro repo** (`package_root` vs `./sdd-lite/`, symlink/copy, reescritura de paths, inyección con marcadores). log-assist es un **repo fijo que se clona** (C-08): casi toda esa maquinaria no aplica.
7. Contratos `_shared`: de 5, quedan 3 con equivalente (flow, persistence, user-interaction). `project-standards` se reduce a reglas de evidencia/idioma; `review-ledger` no aplica como contrato, pero su fila de hallazgo (`location/claim/evidence_class/proof_refs`) es un buen modelo para hallazgos con cita `archivo:línea`.
8. Protocolo de interacción muy aprovechable: preguntar solo si cambia algo, bloque único de máx. 5 preguntas con "por qué importa", `skip N`/`stop`, nunca inferir respuestas, lo salteado queda como pregunta abierta (`skills/sddl-proposal/SKILL.md:86-108`). Encaja con C-14.
9. No heredar: reviews 4R/judgment-day, delivery, macro-plan/escalation, 8 perfiles con tiering, overrides de modelo en config, migraciones de versión de wrapper, archive batch con rúbrica, 12 tipos de checkpoint.
10. Tensiones con `idea/`: estado declarado (sdd-lite) vs derivado (`idea/02-ARCHITECTURE.md:161`); persistencia solo en inglés vs prosa en idioma del usuario (`idea/02-ARCHITECTURE.md:589`); dos wrappers inyectados vs `AGENTS.md` único importado desde `CLAUDE.md` (`idea/02-ARCHITECTURE.md:532`). Ver preguntas.

---

## 1. Modelo de runtime del orquestador

Carga: el host lee `CLAUDE.md`/`AGENTS.md` → si el prompt es un handoff de worker, saltea todo → si no, el agente principal lee `SDDL-RUNTIME.md` una vez y lo mantiene; los módulos se leen solo cuando dispara su evento (`docs/orchestrator.md:7-15`, `SDDL-RUNTIME.md:17-31`).

| Patrón | Descripción (origen) | Clasif. | Cómo aplicarlo en log-assist |
|---|---|---|---|
| Runtime único hot-path | Un archivo (216 líneas) con routing, handoff, result processing, resume, guardrails (`SDDL-RUNTIME.md:1-216`; tabla hot vs condicional `docs/orchestrator.md:17-28`) | ADAPTAR | `orchestrator/LA-RUNTIME.md` ≤150 líneas. Sin complexity routes, sin review ni delivery |
| Módulos lazy por trigger | Tabla trigger→módulo, "no precargar", recargar tras compactación (`SDDL-RUNTIME.md:23-31`; `orchestrator/modules/*` 26-69 líneas) | ADAPTAR | Mantener el mecanismo (tabla), pero v1 con 0-1 módulos. Candidato único: recovery. No crear módulos "por si acaso" |
| Escalera de lectura (context ladder) | config → state → catálogo → digests → project-context → repo → usuario (`SDDL-RUNTIME.md:57-69`; `skills/_shared/sddl-flow-contract.md:113-131`) | REUTILIZAR | config → `state.yaml` del caso → digests de `.md` del caso → salida de scripts → usuario. El orquestador nunca lee logs crudos (C-09) |
| Tabla de delegación | Inline: decidir con 1-3 archivos, escritura atómica de 1 archivo, shell de solo estado; delegar: 4+ archivos, escrituras multi-archivo, tests/builds (`SDDL-RUNTIME.md:90-102`) | ADAPTAR | Cambiar la unidad: "archivo de repo" → "log". Inline: leer `state.yaml`/digests, correr scripts de estado (equivalente a "state-only shell checks" `:101`). Delegar: cualquier consulta sobre logs, cross-log, comparativo |
| Triggers obligatorios | 4+ archivos → delegar; 15 tool calls o 5 lecturas sin delegar → pausar; incidente → recovery (`SDDL-RUNTIME.md:106-114`) | REUTILIZAR | Mismos umbrales; agregar "si estás por leer un log con Read → delegar/script" |
| Delegar por fase, no por archivo | (`SDDL-RUNTIME.md:104,114`; `README.md:46`) | REUTILIZAR | Delegar por paso de análisis o por pregunta acotada, nunca por archivo de log |
| Límite orquestador/worker | Orquestador no implementa, no explora a fondo, no escribe artefactos de otra fase, no confía en chat (`README.md:214-235`; `SDDL-RUNTIME.md:15`) | REUTILIZAR | Mismo texto, adaptado a "no analiza logs, no escribe hallazgos" |
| Handoff controls | `sddl_role`, `stage`, `execution_profile`, `orchestration_allowed: false`, `runtime_loading_allowed: false` + boundary textual (`SDDL-RUNTIME.md:128-146`; `sddl-flow-contract.md:146-158`) | REUTILIZAR | Renombrar (`la_role`, `step`, `profile`…). Es lo que impide que un subagente que carga `CLAUDE.md` se vuelva orquestador (`docs/architecture.md:134`) |
| Handoff compacto | Paths + digests + standards relevantes; no pegar artefactos completos (`SDDL-RUNTIME.md:140,146`; `templates/bootstrap/skill-catalog.md:106-118`) | REUTILIZAR | Pasar `case_id`, pregunta acotada, paths del caso, digest del `TLDR`/estado, scripts permitidos |
| Result processing ordenado | status → findings → context_resolution → open_risks → recommended_next_stage (señal, no override) → resumen 3-5 líneas (`SDDL-RUNTIME.md:148-157`) | ADAPTAR | Quitar `findings`/`context_resolution`. Mantener: `blocked` se muestra ya, `partial` espera decisión, riesgos medium+ antes de rutear |
| Session mode interactive/auto | Pregunta una vez por sesión; auto nunca saltea gates (`SDDL-RUNTIME.md:33-44`) | ADAPTAR | v1: solo interactivo (C-14). Si se agrega auto, limitarlo a pasos read-only |
| Accumulation check | Cuenta changes al inicio y ofrece archivar si supera umbral (`SDDL-RUNTIME.md:46-55`) | ADAPTAR | Opcional: al inicio, listar casos abiertos por `status` (sirve también para C-15). Sin umbrales configurables |
| Complexity assessment / routes | `continue-lite` / `macro-plan-first` / `escalate-to-sdd-v2` (`SDDL-RUNTIME.md:116-126`) | NO APLICA | No hay harness superior al que escalar ni "tamaño de cambio". El equivalente es clasificar el tipo de análisis (C-17) |
| Stage routing table | Situación → siguiente acción → requiere aprobación (`SDDL-RUNTIME.md:159-186`) | ADAPTAR | Tabla corta (≈8 filas) sobre el `status` del caso: sin logs → pedir logs; sin problema confirmado → entrevista; etc. |
| Normal resume | Resolver caso, leer `state.yaml` primero, validar contra artefactos, retomar en primer checkpoint sin resolver (`SDDL-RUNTIME.md:188-194`) | REUTILIZAR | Igual. Ambigüedad (2+ casos abiertos) → preguntar |
| Recovery excepcional | Parar escrituras, congelar evidencia, clasificar recoverable/decision-required/incident, no reparar inline (`orchestrator/modules/exceptional-recovery.md:15-28`) | ADAPTAR | Versión de 10 líneas dentro del runtime, sin módulo aparte |
| Init en sesión principal | `sddl-init` no tiene perfil ni corre como worker (`sddl-flow-contract.md:90`; `SDDL-RUNTIME.md:104`) | REUTILIZAR | `la-init` corre en la sesión principal (necesita preguntar y validar CLIs) |
| Fallback inline | Sin subagentes: ejecutar la skill en el contexto principal, declarar la degradación, no fingir aislamiento (`templates/wrappers/claude-orchestrator.md:44`; `agents-orchestrator.md:56-58`) | REUTILIZAR | Igual; clave para Codex sin TOML o hosts sin subagentes |

## 2. Persistencia

Layout (`skills/_shared/sddl-persistence-contract.md:5-38`): `./sdd-lite/{project-context.md, skill-catalog.md, openspec/{config.yaml, changes/{change-name}/, reviews/{slug}/, delivery/{slug}/, archive/{YYYY-MM-DD}-{name}/, archive/_discarded/}}`. **No existe `specs/`** en sdd-lite (grep sin resultados): lo que el usuario llama "specs" no está en esta referencia; el equivalente conceptual en log-assist sería el conocimiento reutilizable (`knowledge/` en `idea/02-ARCHITECTURE.md:383`).

| Patrón | Descripción (origen) | Clasif. | Cómo aplicarlo en log-assist |
|---|---|---|---|
| Raíz única de runtime | Nada persistido fuera de `./sdd-lite/` (`sddl-persistence-contract.md:38`; `SDDL-RUNTIME.md:208`) | REUTILIZAR | Una raíz para análisis (nombre a decidir, ver preguntas). Permite gitignore y búsqueda simple |
| `config.yaml` de proyecto | Identidad, stack, paths const, quality commands, bootstrap, ai_setups, overrides (`docs/config-and-state.md:7-23`; ejemplo 148 líneas `templates/bootstrap/config.yaml`) | ADAPTAR | ≤25 líneas: `chat_language`, `ai_setups` (detectado/validado/fecha), versión del harness, raíz de casos. Sin stack ni quality commands |
| Carpeta por unidad de trabajo | `changes/{change-name}/` con regex kebab-case sin fechas (`sddl-persistence-contract.md:41-54`) | ADAPTAR | `cases/{case-id}/` con `logs/` adentro (C-05). Definir regla de id compatible con Jira (C-13) |
| `archive/` hermano de `changes/` | `changes/*/` lista solo activos; mover carpeta completa; sufijo `-2` en colisión; nunca borrar (`sddl-persistence-contract.md:114-131`) | ADAPTAR | Reutilizar "hermano" y "mover sin reescribir". Quitar `_discarded/`, dispositions y rúbrica |
| `reviews/` y `delivery/` standalone | Artefactos sin change activo (`sddl-persistence-contract.md:80-112`) | NO APLICA | No hay reviews de código ni textos de entrega |
| `state.yaml` ancla de resume | Memoria operativa, no transcript ni sustituto de artefactos (`sddl-flow-contract.md:217-221`; `sddl-persistence-contract.md:157-159`) | ADAPTAR | Mantener la idea; reducir a: `case_id`, `jira`, metadata breve, `status`, `current_step`, `next_action`, `decisions[]`, `open_questions[]`, `updated_at` |
| Lifecycle con dueño único por transición | 8 estados; solo QA final pone `completed`, solo archive pone `archived` (`docs/config-and-state.md:33-53`; `sddl-flow-contract.md:100-111,198-205`) | ADAPTAR | 5-6 estados simples (C-13). Reutilizar la regla "solo el paso X puede poner el estado Y" |
| Tabla de ownership | Cada artefacto tiene una skill dueña (`sddl-persistence-contract.md:56-78`; `README.md:401-417`) | REUTILIZAR | Una tabla igual en `la-persistence-contract.md` |
| Reglas de ownership | No reescribir bootstrap desde fases; cada fase reescribe su artefacto en rerun; downstream no redefine lo aprobado (`sddl-persistence-contract.md:133-139`) | REUTILIZAR | Igual. Agregar: excerpts de log verbatim |
| Digest al inicio de cada artefacto | "Routing Digest"/"Execution Digest"/"Closeout Digest" (`templates/artifacts/proposal.md:3-10`, `plan.md:3-10`, `qa-report.md:3-11`; regla `sddl-persistence-contract.md:161-166`) | REUTILIZAR | **Pieza clave del orquestador liviano**: cada `.md` del caso abre con 4-6 bullets que el orquestador lee sin abrir el resto |
| Budget por artefacto | 200-800 palabras según artefacto; riesgos y next action arriba; no duplicar narrativa en state (`sddl-persistence-contract.md:168-187`) | REUTILIZAR | Budgets propios (p. ej. hallazgos ≤400 palabras). Coincide con C-16 |
| Write invariant | El artefacto se escribe en todo camino (respondido, salteado, stop, blocked) para que el resume sea desde disco (`skills/sddl-proposal/SKILL.md:110`; `docs/skills.md:56`) | REUTILIZAR | Cada paso deja su `.md` aunque no haya conclusión (C-16: "estado alcanzado o hipótesis") |
| Contrato de escritura del worker | Secciones `## Reads` / `## Writes` explícitas; "no escribir X, Y, Z" (`skills/sddl-proposal/SKILL.md:121-140`) | REUTILIZAR | Cada skill declara qué lee y qué escribe; el adapter lo repite (`templates/agents/claude/sddl-framer.md:18`) |
| Orquestador actualiza state de workers read-only | Si un worker read-only corrió, el orquestador escribe el state (`skills/sddl-deep-explorer/SKILL.md:57-63`) | REUTILIZAR | Subagentes que solo consultan logs devuelven resultado; el orquestador persiste |
| Workers read-only nunca escriben; escritura = incidente | (`orchestrator/modules/review-runtime.md:11,53`) | REUTILIZAR | Si un scout escribe, se descarta su resultado |
| State con todos los campos requeridos desde el inicio | Declarar 7 stages y 7 paths aunque no existan (`skills/sddl-proposal/SKILL.md:240-245`) | NO APLICA | Ruido; los artefactos opcionales se listan cuando existen |
| Persistido solo en inglés | Contratos, skills, schemas, templates y artefactos en inglés; chat es/en (`skills/_shared/sddl-project-standards-contract.md:5-17`) | ADAPTAR | Claves/ids/archivos en inglés; prosa según decisión (conflicto con `idea/02-ARCHITECTURE.md:589`) |

Humano vs máquina en sdd-lite:

| Archivo | Lector principal | Observación |
|---|---|---|
| `config.yaml`, `state.yaml` | máquina/orquestador | YAML estricto con enums; poco legible para un humano (checkpoints/decisions anidados, `state.schema.yaml:357-453`) |
| `proposal.md`, `spec.md`, `design.md`, `plan.md` | humano + digest para máquina | Tablas + digest de bullets `key:` arriba |
| `execution-log.md` | semi-máquina | 139 líneas de template con bloques `key: value` repetidos por stage (`templates/artifacts/execution-log.md:39-139`); poco amigable |
| `skill-catalog.md` | máquina (inyección en prompts) | Sección `Project Standards (auto-resolved)` para copiar a handoffs (`templates/bootstrap/skill-catalog.md:58-104`) |

Recomendación: separar claramente **un** YAML de máquina (`state.yaml`) y `.md` pensados para humanos con un digest corto arriba; evitar `.md` con formato `key: value` masivo.

## 3. Contratos compartidos (`skills/_shared/`)

Rol: fijar vocabulario para que 12 skills no diverjan; se leen como fallback, lo preferido es que el orquestador inyecte lo relevante (`docs/architecture.md:48-56`; `sddl-project-standards-contract.md:97-112`).

| Contrato (líneas) | Qué resuelve | Clasif. | Equivalente en log-assist |
|---|---|---|---|
| `sddl-flow-contract.md` (221) | Ids canónicos (objetivo, ruta, stage, perfil, lifecycle), stage→perfil, context ladder, thin rules, handoff controls, result structure, flow rules, resume (`:18-221`) | ADAPTAR | `la-flow-contract.md` (~80 líneas): ids de pasos, estados del caso, mapa paso→perfil, handoff controls, result contract, resume |
| `sddl-persistence-contract.md` (198) | Layout, naming, ownership, archive, transfer rules, budgets (`:5-198`) | ADAPTAR | `la-persistence-contract.md` (~70 líneas): layout del caso, naming de id, ownership, digest, budgets, archive |
| `sddl-user-interaction-contract.md` (225) | Reglas de cuándo preguntar, 12 checkpoint types, shape estándar, contenido mínimo por tipo, registro de decisiones (`:5-225`) | ADAPTAR | `la-user-interaction-contract.md` (~60 líneas): reglas core + shape + 4-5 tipos + registro |
| `sddl-project-standards-contract.md` (117) | Idioma persistido, perfil del proyecto (stack/commands), registry, precedencia de fuentes, inyección compacta (`:5-117`) | ADAPTAR | Reducir a reglas de evidencia: idioma, citas `archivo:línea`, excerpts verbatim, precedencia (salida de script > digest > memoria). Puede fusionarse en flow-contract |
| `sddl-review-ledger-contract.md` (81) | Fila de finding, severidades, ids/estados, buckets de convergencia, budgets de review (`:7-81`) | NO APLICA (contrato) | Solo tomar la forma de fila de hallazgo: `location`, `claim`, `evidence_class: deterministic\|inferential`, `proof_refs` (`:11-20`) para hallazgos/hipótesis |
| Precedencia de fuentes | Config ejecutable > árbol > docs > bootstrap > usuario (`sddl-project-standards-contract.md:44-54`) | ADAPTAR | Salida de script verificable > artefacto del caso > usuario; nunca memoria de chat |
| `skill-catalog.md` generado | Registry de triggers, perfiles, heurísticas y standards para inyección (`templates/bootstrap/skill-catalog.md:1-124`) | ADAPTAR | En repo fijo no hace falta generarlo: puede ser un archivo estático del harness (índice de skills + índice de scripts, C-09) |

## 4. Init

Pasos de `sddl-init` (`skills/sddl-init/SKILL.md:85-274`):

| # | Paso (origen) | Clasif. | Cómo aplicarlo en `la-init` |
|---|---|---|---|
| 1 | Preflight: bootstrap missing/stale/usable (`:87-88`; estados `SDDL-RUNTIME.md:79-86`) | REUTILIZAR | Detectar si la estructura y `config.yaml` existen y están completos; rerun idempotente |
| 2-3 | Shallow scan + convention scan (máx. 6 archivos) (`:90-112`) | NO APLICA | No hay repo de producto que escanear; el harness es fijo |
| 4 | Detección de IA por señales de archivo (`:114-127`) | ADAPTAR | Mantener señales, **agregar** lo que sdd-lite no hace: verificar CLI instalada (`claude`/`codex` en PATH + versión) y, opcional, un smoke test mínimo. No hay precedente en sdd-lite (grep de `--version`/`command -v` sin resultados) |
| 5 | Checkpoint de selección de IA (uno / varios / ninguno) (`:129-155`) | REUTILIZAR | Mismo formato de menú; en repo fijo el default es "ambas" |
| 6a | Instalar skills symlink o copy + reescritura de paths (`:157-203`) | NO APLICA | Repo fijo: skills ya commiteadas o una sola ubicación. `idea/02-ARCHITECTURE.md:287` descarta symlinks por Windows (C-10) |
| 6b | Generar adapters desde `profiles.yaml`, siempre copy, reemplazar en rerun, borrar ids obsoletos (`:205-215`) | ADAPTAR | Solo si los adapters no se commitean. Si se commitean, init solo valida que existan y coincidan con `profiles.yaml` |
| 7 | Inyección de wrapper con marcadores `<!-- sdd-lite:start/end -->`, preview, confirmación, replace/append/create (`:217-238`) | ADAPTAR | Repo fijo: `CLAUDE.md`/`AGENTS.md` pueden venir commiteados. Reutilizar marcador con `version=` para detectar drift |
| 8-10 | Construir `project-context.md` y `skill-catalog.md` (`:240-250`) | NO APLICA | Sin contexto de proyecto variable |
| 11 | Construir `config.yaml` con `ai_setups` (`:252-264`) | ADAPTAR | Registrar `ai_setups` con resultado de validación y fecha |
| 12 | Resumen final: leído/escrito/inferido/preguntado + sección IA (`:266-274`) | REUTILIZAR | Igual, más estado de validación por IA |
| — | Crear carpetas | — | sdd-lite **no** crea `changes/`/`archive/` en init: solo escribe 3 archivos (`:39-43`). log-assist sí debe crearlas (C-06) |
| — | Validación final (`:276-297`) | ADAPTAR | Checks estáticos útiles: adapters existen, TOML parsea, a lo sumo una clave `model`, nunca `model = "inherit"` (`:292`), marcador de wrapper con versión. Quitar checks de migración |
| — | Status `partial` si IA salteada o dudosa; `blocked` si no se puede escanear (`:317-318`) | REUTILIZAR | `partial` si una IA no validó |
| — | No escribir fuera de la raíz salvo archivos de IA confirmados; no tocar overrides del usuario (`:54-56`) | REUTILIZAR | Igual |

## 5. Integración con varias IAs

| Patrón | Descripción (origen) | Clasif. | Cómo aplicarlo |
|---|---|---|---|
| Neutral vs específico | Runtime, skills, contratos, schemas, templates son agnósticos; solo cambia cómo se lanza un worker (`docs/architecture.md:119-121`) | REUTILIZAR | Misma división. Scripts también neutrales |
| Dos wrappers casi idénticos | Líneas 1-32 iguales en ambos; difiere solo "Platform" (`templates/wrappers/claude-orchestrator.md:34-44` vs `agents-orchestrator.md:34-58`) | ADAPTAR | Evitar duplicación: bloque común único + sección por plataforma. Alternativa de `idea/02-ARCHITECTURE.md:532` (`CLAUDE.md` con `@AGENTS.md`) a validar |
| Worker bypass primero | El wrapper evalúa los controles antes de activar (`claude-orchestrator.md:4-16`) | REUTILIZAR | Primera sección de ambos wrappers |
| Reglas de activación | Solo si se pide explícito o trabajo no trivial; ofrecer una vez (`claude-orchestrator.md:18-26`) | ADAPTAR | Repo dedicado: activar siempre en la sesión principal |
| `agents` como id neutral | `.codex/` detecta como `agents`; Grok/OpenCode reusan `AGENTS.md` + `.agents/skills/` (`docs/architecture.md:128`) | ADAPTAR | v1 solo Claude y Codex (C-07); ids `claude` y `codex` más claros |
| Claude: Agent tool con tipo nombrado | Lanzar `execution_profile` como tipo; no usar Skill tool ni Explore built-in; esperar resultado (`claude-orchestrator.md:36`) | REUTILIZAR | Igual |
| Claude: fallback general-purpose | Si el tipo no existe: general-purpose con el modelo del perfil + cuerpo del adapter pegado + aviso (`claude-orchestrator.md:41`) | REUTILIZAR | Igual |
| Caveat `permissionMode: plan` | En auto/bypass el host lo ignora; read-only queda a nivel prompt (`claude-orchestrator.md:42`) | REUTILIZAR | Relevante para scouts read-only |
| Codex: worker mode | Preguntar `native-workers` vs `inline-sequential`; roles en `.codex/agents/`; hilo nuevo, no fork (`agents-orchestrator.md:40-54`) | ADAPTAR | Detectar en init en vez de preguntar por sesión, si es posible |
| `profiles.yaml` fuente única | Perfiles con skills, capability, write_scope, modelo/effort por host, `stage_map`, mapa de tiers (`templates/agents/profiles.yaml:1-16,18-35,158-169`) | ADAPTAR | 2-3 perfiles (p. ej. `la-scout` read-only, `la-analyst` escribe en el caso). Mantener mapa de tiers comentado |
| Adapter Claude | Frontmatter `name`, `description`, `model`, `effort`, `permissionMode`, `tools`, `disallowedTools`, `skills:` (preload) + cuerpo de 5 bullets (`templates/agents/claude/sddl-explorer.md:1-22`) | REUTILIZAR | Mismo esqueleto. `skills:` en lista YAML (`CHANGELOG.md:30`) |
| Adapter Codex | TOML `name`, `description`, `model`, `model_reasoning_effort`, `sandbox_mode`, `developer_instructions` que apunta al `SKILL.md` por path (`templates/agents/codex/sddl-explorer.toml:1-12`) | REUTILIZAR | Igual; Codex lee la skill por path, no por descubrimiento |
| Codex `model: inherit` | Omitir clave `model` en TOML; effort independiente (`skills/sddl-init/SKILL.md:210`) | REUTILIZAR | Igual |
| Overrides `execution_profiles` en config | Por perfil y host; init regenera adapters (`schemas/config.schema.yaml:357-377`) | NO APLICA | Repo fijo: se edita `profiles.yaml` y se commitea |
| Tiering de modelos | Decisión high, framing/ejecución mid, mecánico cheap, verificación ≥ escritor (`sddl-flow-contract.md:72`; `CHANGELOG.md:9-13`) | ADAPTAR | Regla útil en una línea; con 2-3 perfiles |
| Paralelismo | Solo read-only independiente o escrituras disjuntas; esperar siempre (`claude-orchestrator.md:38`; `review-runtime.md:32-41`) | REUTILIZAR | Útil para análisis comparativo de varias pantallas (C-17) |

## 6. Anatomía de una skill

Tamaño: 122 (`sddl-deep-explorer`) a 335 líneas (`sddl-delivery`). Secciones presentes en las 12 skills: `Goal`, `Reads`, `Writes`, `Validation`, `Expected Output`; en 11: `Scope`, `Workflow`, `Runtime operating rules`; en 10: `User Interaction`; en 8: `Quality Bar`.

| Elemento | Descripción (origen) | Clasif. | Para log-assist |
|---|---|---|---|
| Frontmatter | Solo `name` + `description` con "cuándo usar" y `Triggers on:` (`skills/sddl-init/SKILL.md:1-8`; `sddl-proposal/SKILL.md:1-8`) | REUTILIZAR | Igual; triggers en es/en |
| `Goal` + rol en 1 línea | "You are the … skill for sdd-lite" (`sddl-deep-explorer/SKILL.md:10-19`) | REUTILIZAR | — |
| `Runtime operating rules` | No ser orquestador anidado, usar standards inyectados, fallback al catálogo, paths+digests (`sddl-proposal/SKILL.md:21-27`) | REUTILIZAR | 4-5 bullets fijos en todas |
| `Scope` should / should not | (`sddl-deep-explorer/SKILL.md:29-44`) | REUTILIZAR | Evita que un paso invada otro |
| `Reads` / `Writes` | Inputs y outputs explícitos con paths (`sddl-proposal/SKILL.md:121-140`) | REUTILIZAR | Agregar `Scripts` permitidos (C-09) |
| Budget propio del worker | P. ej. máx. 10 archivos, independiente de la regla del orquestador (`sddl-proposal/SKILL.md:56-64`) | ADAPTAR | Budget de invocaciones de script / líneas devueltas |
| `Artifact Shape` | Template base + secciones obligatorias + estados (`sddl-proposal/SKILL.md:142-185`) | REUTILIZAR | Apuntar a `templates/` breves (C-16) |
| `Workflow` numerado | 6-12 pasos (`sddl-deep-explorer/SKILL.md:77-90`) | REUTILIZAR | ≤8 pasos |
| `State Sync Rules` | Tabla status del artefacto → stage → lifecycle → next_action (`sddl-proposal/SKILL.md:236-268`) | ADAPTAR | Una tabla corta por skill que escribe |
| `Validation` checklist | Autoverificación antes de devolver (`sddl-deep-explorer/SKILL.md:99-106`) | REUTILIZAR | Incluir "toda afirmación tiene cita" |
| `Expected Output` | Result contract común: requeridos `status`, `executive_summary`, `artifacts`, `next_action`, `open_risks` (`sddl-flow-contract.md:160-173`); cuándo `partial` vs `blocked` (`sddl-deep-explorer/SKILL.md:121-122`) | REUTILIZAR | Mismos 5 campos + opcionales `decision_required`, `decision_options`, `evidence` |
| Opcionales de trazabilidad | `context_resolution`, `standards_source`, `artifact_digests_used` (`sddl-flow-contract.md:183-186`) | NO APLICA | Ruido para v1 |
| Distinguir hechos / inferencias / incógnitas | (`sddl-deep-explorer/SKILL.md:27,86`) | REUTILIZAR | Central en análisis de logs |
| Skill ≠ adapter | La skill es el algoritmo; el adapter solo modelo/tools/límites (`docs/architecture.md:46`; `profiles.yaml:2`) | REUTILIZAR | Igual |

## 7. Protocolo de interacción con el usuario

| Patrón | Descripción (origen) | Clasif. | Para log-assist |
|---|---|---|---|
| Preguntar solo si cambia algo | Scope, riesgo, dirección, calidad, camino; nunca hechos recuperables (`sddl-user-interaction-contract.md:5-10,221-225`) | REUTILIZAR | Nunca preguntar lo que un script puede responder |
| Shape de checkpoint | Resumen, pregunta concreta, 2-4 opciones, una recomendada, texto libre (`:29-37`) | REUTILIZAR | Igual |
| Bloque de clarificación | Máx. 5 preguntas en un solo bloque, cada una con "Why it matters", `skip N`, `stop`; input no reconocido reimprime; nunca inferir; lo salteado pasa a preguntas abiertas (`sddl-proposal/SKILL.md:86-108`) | REUTILIZAR | Base para entrevista / grill-me (C-12, C-14) |
| Precision gate | Levantar un gate solo con evidencia concreta (`sddl-proposal/SKILL.md:72`) | REUTILIZAR | Evita cuestionarios |
| Readiness gates | `contradiction`, `insufficient_context`, `ambiguous_framing` con verdict y severidad (`sddl-proposal/SKILL.md:74-84`) | ADAPTAR | Para confirmar el problema antes de analizar (C-14) |
| `phase_validation` inteligente | Omitir si el usuario ya indicó avanzar; siempre mostrar si hay ambigüedad o riesgos > medium (`sddl-user-interaction-contract.md:39-57`) | REUTILIZAR | Igual |
| Confirmaciones reconocidas | `sigue`, `dale`, `ok`, `listo`…; feedback reemplaza confirmación (`SDDL-RUNTIME.md:42`) | REUTILIZAR | Igual |
| 12 checkpoint types | (`sddl-user-interaction-contract.md:12-27`) | ADAPTAR | 4-5: `missing_context`, `problem_confirmation`, `phase_validation`, `scope_change`, `close_review` (propuesta, a validar) |
| Action set de selección | `all \| none \| 1,3 \| 1-4 \| inspect N \| done`; nada se mueve antes de `done` (`:140,150-154`) | ADAPTAR | Útil para elegir logs/pantallas o casos relacionados (C-15, C-17) |
| Registro de checkpoints/decisions | `checkpoints[]` 9 campos y `decisions[]` 6 campos en `state.yaml` (`:192-213`) | ADAPTAR | Una lista `decisions[]` de 3-4 campos; o sección "Decisions" legible en el `.md` del caso |
| `blocked` vs `partial` | Sin paso seguro sin decisión → `blocked`; trabajo útil pero depende del usuario → `partial` (`:215-219`) | REUTILIZAR | Igual |

## 8. Schemas

| Aspecto | Evidencia | Evaluación |
|---|---|---|
| Qué validan | `config.schema.yaml` (440 líneas): identidad, paths como `const`, quality commands, bootstrap, conventions, ai_setups, overrides (`schemas/config.schema.yaml:1-440`). `state.schema.yaml` (510): 15 requeridos, enums de stage/lifecycle/checkpoint, summaries de QA/review/delivery (`schemas/state.schema.yaml:1-510`) | Todo `additionalProperties: false` + enums |
| Quién los ejecuta | Nadie: no hay script ni dependencia (`jsonschema`/`ajv`/`yq` sin resultados). Solo instrucciones al LLM: "Must validate against" (`skills/sddl-init/SKILL.md:254`), "every field marked required" (`skills/sddl-proposal/SKILL.md:240,291`) | Enforcement débil, costo de contexto alto |
| Costo de mantenimiento | Cada cambio de id toca enums en schema, flow-contract, profiles, catálogo, wrappers (`CHANGELOG.md:24-33`) | Drift frecuente |
| Paths como `const` | `./sdd-lite/...` fijos en schema (`config.schema.yaml:80-106`) | Redundante: el contrato ya los fija |

Recomendación v1: **no portar JSON Schema**. Si hay scripts (C-09), un único validador de `state.yaml` (campos requeridos + enum de `status`, ~30 líneas) ejecutable en los 3 SO; los templates actúan como contrato de forma. Los enums viven en un solo lugar (flow-contract).

## 9. Layout del paquete vs layout del runtime

sdd-lite separa paquete (`sdd/sdd-lite/`: `orchestrator/`, `skills/`, `templates/`, `schemas/`, `README.md:68-144`) de runtime en el repo consumidor (`./sdd-lite/`, `README.md:146-181`) y de archivos de host (`.claude/skills|agents`, `.agents/skills`, `.codex/agents`, `CLAUDE.md`, `AGENTS.md`: `skills/sddl-init/SKILL.md:45-52`). Paths de paquete se resuelven desde `package_root`; `./sdd-lite/` desde la raíz del proyecto (`SDDL-RUNTIME.md:21`).

| Pieza | En sdd-lite | Propuesta log-assist (repo fijo, C-08) |
|---|---|---|
| Runtime, skills, contratos, templates | Paquete, referenciado vía `<package-root>` reescrito en init | Commiteado en el repo; paths fijos relativos a la raíz |
| Adapters `.claude/agents`, `.codex/agents` | Generados por init (copy) | A decidir: commiteados (simple) o generados por init |
| Skills visibles para Claude | Symlink/copy a `.claude/skills/` | A decidir; symlink descartado en Windows (`idea/02-ARCHITECTURE.md:287`) |
| `CLAUDE.md` / `AGENTS.md` | Bloque inyectado con marcadores | Commiteados; init valida marcador/versión |
| `config.yaml` | Generado por init | Generado por init (local por clon, ai_setups) |
| Casos / análisis | `./sdd-lite/openspec/changes/` | Raíz de casos creada por init; probablemente gitignorada (`idea/02-ARCHITECTURE.md:383`) |
| Overrides de template del usuario | `./sdd-lite/templates/`, nunca sobrescritos (`skills/sddl-init/SKILL.md:56`) | NO APLICA v1: se editan los templates del repo |

### Núcleo mínimo resultante (solo lo marcado REUTILIZAR/ADAPTAR)

Contraste de tamaño para dimensionar la v1. Las cifras de log-assist son objetivos, no evidencia.

| Pieza sdd-lite | Líneas sdd-lite | Equivalente log-assist | Objetivo |
|---|---|---|---|
| `orchestrator/SDDL-RUNTIME.md` + 3 módulos | 216 + 129 | `orchestrator/LA-RUNTIME.md` (recovery inline) | ≤150 |
| 5 contratos `_shared` | 842 | 3 contratos (flow, persistence, user-interaction) | ≤210 |
| 12 skills | 2934 | skills v1 (C-12) | 60-150 c/u |
| `schemas/` | 950 | ninguno o validador por script | ≤30 |
| `templates/artifacts/` (10) | ~770 | templates breves del caso (C-16) | ≤40 c/u |
| `templates/bootstrap/` | 330 | `config.yaml` ejemplo | ≤25 |
| `templates/wrappers/` | 104 | bloque común + sección por plataforma | ≤60 |
| `templates/agents/` (profiles + 16 adapters) | 434 | profiles + 2-3 adapters por host | ≤120 |

Mecanismos que sostienen al orquestador liviano y conviene preservar juntos (si falta uno, el resto se degrada):

1. Handoff con controles de worker evaluados primero por el wrapper (`claude-orchestrator.md:4-16`).
2. Result contract de 5 campos con `partial`/`blocked` explícitos (`sddl-flow-contract.md:160-173`).
3. Digest al inicio de cada artefacto (`sddl-persistence-contract.md:161-166`).
4. Write invariant: todo camino deja artefacto (`sddl-proposal/SKILL.md:110`).
5. `state.yaml` leído primero en resume, validado contra artefactos (`SDDL-RUNTIME.md:188-194`).
6. Tabla de delegación con umbrales numéricos (`SDDL-RUNTIME.md:90-112`).

## 10. Lo que no heredar en v1

| Qué | Origen | Por qué |
|---|---|---|
| Reviews 4R / judgment-day + ledger + módulo de review | `docs/review-protocols.md:1-140`; `skills/_shared/sddl-review-ledger-contract.md`; `orchestrator/modules/review-runtime.md` | Diseñado para diffs de código; ~490 líneas. Un único "challenger" read-only alcanza si se quiere contraste |
| `sddl-delivery`, `templates/delivery/`, `delivery_gate`, `delivery_summary` | `docs/skills.md:159-171`; `state.schema.yaml:263-303` | Sin commits/PR |
| Objetivos y rutas (`planner`, `macro-plan-first`, `escalate-to-sdd-v2`) | `sddl-flow-contract.md:20-35`; `docs/flow.md:80-118` | No hay equivalente en análisis de logs |
| Cadena proposal→spec→design→plan con inbound contracts y "Needed Before" | `docs/skills.md:70-110` | Demasiadas fases para un caso; C-20 pide pocos stages |
| 8 perfiles con tiering + migraciones | `templates/agents/profiles.yaml`; `CHANGELOG.md:1-45` | 2-3 perfiles cubren scout/analista |
| `execution_profiles` overrides y regeneración | `config.schema.yaml:357-430`; `sddl-init/SKILL.md:205-215` | Repo fijo: se edita la fuente |
| Versionado estricto de wrapper con migración | `docs/architecture.md:239-241`; `sddl-init/SKILL.md:213-214,236` | Sin instalaciones legacy |
| Symlink/copy + reescritura de paths | `sddl-init/SKILL.md:157-203` | Repo fijo |
| Convention scan, `project-context.md`, stack, quality commands | `sddl-init/SKILL.md:90-112`; `templates/bootstrap/project-context.md` | No hay proyecto que describir |
| `state.yaml` de 15 requeridos con stages/artifacts declarados | `state.schema.yaml:5-20,90-168` | Frágil y costoso de mantener a mano |
| Archive batch con rúbrica, dispositions, `_discarded/`, `related_changes`, umbrales | `skills/sddl-archive/SKILL.md` (284 líneas); `sddl-persistence-contract.md:114-131` | Mover carpeta + campo `status` alcanza |
| `execution-log.md` con bloques `key: value` repetidos | `templates/artifacts/execution-log.md:39-139` | Poco legible (C-05) |
| Campos de trazabilidad del result contract | `sddl-flow-contract.md:183-186` | Sin valor para el usuario |
| Excepción `git add` y reglas git | `SDDL-RUNTIME.md:212`; `skills/sddl-executor/SKILL.md:82-83` | No hay operaciones git en el flujo |
| 12 checkpoint types con contenido mínimo cada uno | `sddl-user-interaction-contract.md:12-190` | 4-5 tipos bastan |
| Schemas JSON de 950 líneas sin validador | §8 | Ver recomendación |

## Preguntas o dudas para validar con el usuario

1. **Estado declarado vs derivado.** sdd-lite declara el estado en `state.yaml` que escriben orquestador y fase (`sddl-persistence-contract.md:68`); `idea/02-ARCHITECTURE.md:161` propone derivarlo de qué archivos existen. C-13 pide "status simple que se completa con las interacciones" (suena a declarado). ¿Declarado con validación por script, derivado, o híbrido?
2. **Idioma de la persistencia.** sdd-lite persiste todo en inglés (`sddl-project-standards-contract.md:5-17`); `idea/02-ARCHITECTURE.md:589` propone prosa en el idioma del usuario. "Archivos más legibles para humanos" ¿implica prosa en español?
3. **Nombre y ubicación de la raíz de persistencia.** ¿Literal `openspec/` como en sdd-lite, `history/` como en la idea, u otro? ¿Gitignorada completa?
4. **Id del caso.** sdd-lite exige kebab-case minúscula sin fechas (`sddl-persistence-contract.md:43-53`); la idea usa `JIRA-4821` (`idea/02-ARCHITECTURE.md:139`). ¿Carpeta = ticket de Jira tal cual, slug, o `ticket-slug`?
5. **Wrappers.** ¿Dos bloques (como sdd-lite) o `AGENTS.md` como fuente única con `CLAUDE.md` importándolo (`idea/02-ARCHITECTURE.md:532`)? ¿Commiteados o inyectados por init?
6. **Alcance de "validar que las IAs funcionen".** sdd-lite solo detecta archivos. ¿Alcanza con CLI en PATH + versión, o se quiere un smoke test real (lanzar un subagente de prueba, consume tokens y requiere auth)?
7. **Adapters y skills: ¿commiteados o generados por init en cada clon?** Afecta si init escribe en `.claude/` y `.codex/` o solo valida.
8. **Scripts desde el orquestador.** sdd-lite permite al orquestador shell "state-only" inline (`SDDL-RUNTIME.md:101`). ¿El orquestador de log-assist puede correr scripts de estado/búsqueda entre casos (C-15) inline, y los de consulta de logs solo vía subagente (C-09)?
9. **Codex sin roles nativos.** sdd-lite soporta `inline-sequential` como fallback (`agents-orchestrator.md:43,56-58`). ¿Es aceptable ese modo degradado en v1 o Codex debe correr siempre con subagentes?
10. **Modo `auto`.** ¿Se descarta en v1 (solo interactivo, C-14) o se quiere para encadenar consultas read-only?
