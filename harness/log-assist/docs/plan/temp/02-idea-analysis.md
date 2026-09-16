# 02 — Análisis crítico del pre-planning `docs/idea/`

> Insumo de planning. Fuente analizada: `harness/log-assist/docs/idea/` (README, 00-DISCOVERY, 01-PRD,
> 02-ARCHITECTURE, 03-SKILLS-AGENTS-SCRIPTS, 04-RISKS-AND-BACKLOG, 05-SOURCES), leídos completos.
> Regla aplicada: la doc es **concepto**, no fuente de verdad. Donde choca con el pedido del usuario,
> gana el usuario. Las citas usan `archivo:línea` con prefijos abreviados (`README`, `00`, `01`, ... `05`).
> No se analizó `docs/scripts-idea/` (fuera del alcance pedido; existe y puede ser relevante para scripts).

## TL;DR

- La doc diseña **otro producto**: un repo standalone `logharness` para QA/Ops/Dev con base de conocimiento compartida vía PR (`00:14-21`, `02:53`). El usuario pide un harness estilo sdd-lite, `log-assist`, con **carpeta por análisis** como centro. El núcleo técnico sirve; la topología y el alcance, no tal cual.
- Conceptos de alto valor y bajo costo para v1: *el agente consulta, no recibe*; contrato de salida con envelope anti-truncación; `absence` + `coverage`; registro append-only; cita `archivo:línea` verificada por script; hipótesis falsables con estado; fast path; interview por bloques; TLDR con `LIMITS`/`RULED_OUT`.
- **Contradicción central con el usuario**: la doc impone *estado derivado, nunca declarado* (`README:24-25`, `02:161-178`). El usuario pide un **status/metadata simple que se completa con las interacciones**. Se pueden reconciliar: status declarado a nivel humano y progreso derivado por script.
- **Jira no está modelado**: solo aparece como formato de ID (`01:137`), `export` en F2 (`03:291`) y MCP en F3 (`04:97`). `case.yaml` no tiene plataforma, versión del player ni status (`02:138-155`).
- **No cubierto por la idea**: patrones de recursos (escalado de memoria/CPU), init que valide que Claude y Codex funcionen, índice o skill de scripts, extensibilidad formal a nuevos tipos de log y búsqueda entre análisis en v1 (`search` es F2, `03:290`).
- **Codex no queda en paridad**: la doc acepta "degradación elegante, sin subagentes" (`02:551-553`), y el enforcement anti-lectura (`deny Read`) es solo de Claude (`02:559-579`). El usuario pide que "funcione igual".
- En la doc, las skills corren inline en la conversación principal y hay solo 2 subagentes (`03:8-18`, `03:213-217`). El usuario pide un orquestador liviano que delegue y skills que funcionen como subagentes.
- Runtime Python+uv+drain3 (`02:244-265`) es razonable para cross-platform, pero suma fricción en Windows y para usuarios no técnicos (`00:199` A4 sin validar). Drain3 es prescindible en v1.
- La doc tiene **inconsistencias internas** relevantes: cantidad de skills y subagentes del MVP, fase de `index.yml` y de hipótesis, estimaciones que no suman (F1 = 23 días-persona contra "2-3 semanas"), un fast path incompatible con los gates obligatorios, y una "inmutabilidad" de `attempts.ndjson` que los permisos no garantizan.
- Propuesta (a validar): v1 = carpeta por análisis + `record/` append-only con schema + scripts core con índice + 5-6 skills + 2-3 templates de reporte. Afuera: knowledge/promote, drain3, i18n yml, gitleaks/CI, redacción, evals, fleet y postmortem.

---

## 1. Conceptos valiosos

Valor: impacto en la v1 que pidió el usuario. Costo: complejidad de implementación y mantenimiento.

| # | Concepto | Qué es | Dónde | Valor v1 | Costo | Nota de adaptación |
|---|---|---|---|---|---|---|
| C1 | **El agente consulta, no recibe** | Nunca se lee un log entero; se consulta con herramientas de salida acotada | `README:19-20`, `00:137`, `02:40-43`, `03:17-18` | Alto | Bajo (regla + scripts) | Es literalmente el pedido del usuario ("nunca pasa logs enteros") |
| C2 | **Contrato de salida de scripts** | Resultado completo a disco, resumen + ruta al agente, envelope `returned/totalCount/truncated/nextCursor`, `next[]` | `01:175-185` (RF-4), `02:476-528` (ADR-008) | Alto | Medio | Conviene simplificarlo: envelope + `artifact` + `next`, sin tres niveles de presupuesto por comando (`03:330-336`) |
| C3 | **Prohibida la truncación silenciosa** | Toda salida paginable declara lo que omitió | `01:180`, `02:520-528`, `04:16` (R4) | Alto | Bajo | Parte del contrato (C2), sin costo extra |
| C4 | **Detección por ausencia** | `absence --scope --key --expect --per`: eventos esperados que no ocurrieron | `README:21-23`, `00:64-67`, `02:448-472` (ADR-007) | Alto | Medio | Generaliza a heartbeats, syncs y descargas (`02:468-470`) |
| C5 | **`coverage`: "no pasó" vs "no hay dato"** | Huecos temporales por grupo; equipo apagado = punto ciego | `00:42`, `03:300` | Alto | Bajo | Clave para el análisis multi-pantalla y el cross-log |
| C6 | **Registro append-only** | `attempts.ndjson`: nunca se edita, se corrige con `supersedes` | `README:26-27`, `02:217-231`, `01:195` | Alto | Bajo-medio | Encaja con "persistencia simple y fácil de validar". Requiere validador por schema. La inmutabilidad es por convención (ver §3 #9) |
| C7 | **Cita verificada por script** | Toda afirmación lleva `archivo:línea` + excerpt ≤200; un script chequea que existan | `README:34-36`, `01:197`, `03:338-350` | Alto | Bajo-medio | Determinístico y barato. Gate natural antes de emitir un reporte |
| C8 | **Hipótesis falsables con estado** | `statement`, `predicts_true[]`, `predicts_false[]`; estado `open/supported/refuted/superseded` | `01:193-194`, `02:219-226`, `03:112-150` | Alto | Bajo como schema; medio si se exige ≥3 | Cubre el "estado alcanzado aunque no haya conclusión". Mínimo de 3: evaluar (ceremonia) |
| C9 | **Fast path** | Un caso trivial se cierra con 2 archivos | `00:159`, `02:233-238`, `01:290` (AC8) | Alto | Bajo | Choca con los gates de la propia doc (§3 #6) |
| C10 | **Interview por bloques con gating** | Síntoma / alcance / temporalidad / cambios / ya probado / expectativa / cobertura; no avanza con huecos críticos | `03:44-71`, `01:191` | Alto | Bajo | Base directa para la skill tipo grill-me. "Expectativa" alimenta `absence` (`03:60`) |
| C11 | **Parar si los logs no cubren el quiebre** | Pedir más días en vez de concluir | `03:87`, `03:258` | Alto | Bajo | Refuerza el "no asume nada solo" |
| C12 | **Reglas de lectura de salida** | Primero el envelope; declarar qué no se puede concluir; descartes explícitos; no acomodar la narrativa | `03:94-108` | Alto | Bajo | Mejor como regla compartida (`_shared`) que como skill aparte |
| C13 | **TLDR con secciones fijas** | `verdict/cause/evidence/ruled_out/action/preventive/limits`; "no determinado, falta X" es un resultado válido | `03:154-178` | Alto | Bajo | Base de los templates breves que pidió el usuario |
| C14 | **Docs de dominio** | `modules.md`, `known-noise.md`, `units-of-analysis.md`, `glossary.md` | `03:354-373`, `00:41` | Alto | Bajo (redacción) | Según la doc, lo que "ningún modelo infiere solo" (`03:372-373`) |
| C15 | **Playbook como árbol de decisión** | Rombos que se contestan con un comando y al menos una hoja "no es este patrón" | `03:377-447` | Alto | Medio por playbook | Vehículo de "bugs conocidos" y de extensibilidad a casos nuevos |
| C16 | **Ingesta robusta** | BOM/UTF-16, `errors='replace'`, ts normalizado preservando el crudo, orden por primer ts, `parse_rate<0.95` como error visible | `01:150-156`, `03:303-311`, `04:24` (R12) | Alto | Medio | Obligatorio si hay logs de Windows o de varios tipos |
| C17 | **Grupos baseline/target + `diff`** | Pantalla sana vs rota como técnica de primera clase | `01:139`, `01:169`, `03:56`, `03:324` | Alto | Medio | Es el análisis comparativo multi-pantalla que pide el usuario (en la doc queda como S/F2) |
| C18 | **`status --json` + siguiente acción** | Un documento JSON por invocación; el orquestador pregunta en vez de recordar | `02:177-178`, `02:337-340`, `02:375-379` | Alto | Medio | Encaja con el orquestador liviano. El estado se puede combinar con el status declarado |
| C19 | **Logs como dato adversarial** | Prompt "passive"; texto con forma de orden se reporta, no se obedece | `01:231-232`, `03:233-240` | Medio | Bajo | Una regla en el prompt de los workers |
| C20 | **Challenger** | Subagente que busca explicaciones alternativas, falta de cobertura y correlación tomada como causa | `03:242-264`, `01:196` | Medio | Medio (subagente + paridad Codex) | Candidato a opt-in o a checklist dentro de `report` |
| C21 | **Hipótesis humana sellada** | La hipótesis del usuario no entra en la generación | `01:192`, `03:64-66` | Bajo-medio | Medio | Solo se puede aislar si la generación corre en un worker sin ese dato. Inline no es enforceable |
| C22 | **Índice de detección con `symptoms.es`** | `index.yml`: reglas → qué patrón cargar (progressive disclosure) | `03:451-482`, `01:206-207` | Medio | Medio-alto (DSL `any_of/requires_all`) | Para v1 alcanza un catálogo simple de known-issues con firmas grep/absence |
| C23 | **Drain3 `summarize`** | Template mining 10³–10⁶:1 | `00:140-141`, `02:426-444` | Medio | Medio-alto (dependencia, masking) | Útil para lo desconocido. Prescindible si hay conteos por componente/nivel |
| C24 | **Posicionamiento honesto** | "Reduce el espacio de búsqueda, no dice qué pasó" | `01:29-38`, `README:39-42` | Medio | Bajo | Coincide con el "ayuda a confirmar el problema" |
| C25 | **Validación con un caso real conocido** | Reproducir el veredicto de `menuboard-fetch-diag` sobre 10 logs | `README:50-51`, `01:285-287` | Alto | Bajo | Sirve como aceptación manual sin evals |
| C26 | **Gate de fase por uso real** | No agregar features hasta resolver casos reales | `04:105-114` | Medio | Bajo | Protege la "v1 simple" |

---

## 2. Matriz de alineación

Estados: **COINCIDE** · **CONTRADICE** · **NO MENCIONADO POR USUARIO** (lo trae la idea, el usuario no lo pidió) · **NO CUBIERTO POR IDEA** (lo pidió el usuario, la idea no lo trata). "(parcial)" indica que coincide solo en parte.

| # | Tema | Qué dice la idea | Qué dijo el usuario | Estado | Nota |
|---|---|---|---|---|---|
| 1 | Nombre y ubicación | Repo standalone `logharness/` clonado por QA/Ops/Dev; CLI `loga` (`02:53`, `00:10-12`) | `log-assist` en `harness/log-assist/`; "configurado fijo en un repo que se clona" | CONTRADICE (parcial) | Coinciden en "repo clonable". Difieren nombre y relación con ai-tools (fuente vs repo instalado) |
| 2 | Contención del harness | `harness/` + `.claude/` fino en raíz + `AGENTS.md`/`CLAUDE.md` en raíz (`02:287-301`) | Estructura sdd-lite: skills, schemas, orchestrator, templates | COINCIDE (parcial) | Misma tensión real: Claude y Codex descubren desde la raíz (`02:289-290`). sdd-lite la resuelve con bootstrap y wrappers |
| 3 | Unidad de trabajo | "Caso" = `history/<ID>/` (`02:114-129`) | "Carpeta por análisis" | COINCIDE | Cambia la terminología, no el concepto |
| 4 | Layout de logs | `logs/` con subcarpetas **arbitrarias** como grupos (por equipo, fecha o módulo) (`01:138`, `02:119-122`) | Logs planos o **un solo nivel** de subcarpetas por pantalla | CONTRADICE (parcial) | El usuario restringe la profundidad y fija la semántica (pantalla). Simplifica `ingest` y la comparación |
| 5 | Carpeta de persistencia | No existe como tal: `case.yaml`, `TLDR.md` y `attempts.ndjson` sueltos + `.work/` con salidas completas (`02:117-127`) | Carpeta de persistencia "tipo `changes` de openspec" dentro del análisis; "lo más importante, simple y fácil de validar" | CONTRADICE (parcial) | La idea mezcla persistencia, md humanos y salidas crudas en el mismo nivel. `.work/` guarda excerpts de logs (tamaño, privacidad) |
| 6 | Persistir "todo lo analizado" | Solo hipótesis/veredictos en `attempts`; `read-output` no persiste hallazgos (`03:94-108`); `triage.md` en `.work/` (`03:88`) | Persistencia de todo lo analizado | NO CUBIERTO POR IDEA | Falta un registro de **findings/observaciones** que no son hipótesis (p. ej. "memoria +2%/h en pantalla A") |
| 7 | `case.yaml` | Solo lo no derivable: id, slug, language, goal, severity, components, groups, sealed hypothesis, related_cases, resolution (`02:136-159`) | Ticket, descripción breve (fecha, plataforma, versión del player, etc.), status/metadata simple | CONTRADICE (parcial) | Faltan `platform`, `player_version`, rango de fechas, pantallas y `status`. El formato YAML separado es aprovechable |
| 8 | Estado derivado vs status | "Estado derivado, nunca declarado"; 8 estados computados (`README:24-25`, `02:161-178`, `01:140`) | "Status o metadata simple que se completa con las interacciones"; buscar por status | CONTRADICE | La propia doc declara campos (`resolution`, respuestas del interview en `case.yaml`, `03:69`). Propuesta: `status` declarado + `progress` derivado |
| 9 | `attempts.ndjson` | Append-only, `supersedes`, rechaza sin `predicts_false` (`02:217-231`) | Persistencia simple y fácil de validar | COINCIDE | Validable por schema. Nombre y alcance a revisar (incluir findings) |
| 10 | TLDR y reportes | `TLDR.md` ≤40 líneas + `report.md.tmpl` + `postmortem.md.tmpl` (`02:99-103`, `03:154-178`) | `.md` legibles en puntos importantes; relevamientos finales breves; uno o varios tipos (formal, hipótesis) | COINCIDE (parcial) | Falta el tipo "estado alcanzado / hipótesis sin conclusión" como template propio. `postmortem` (formato incident.io) excede |
| 11 | `history/` vs `knowledge/`; qué se commitea | `history/**` gitignorado completo; `knowledge/` commiteado vía PR (`02:383-422`); C2 "requerimiento explícito" (`00:180`) | No lo mencionó | NO MENCIONADO POR USUARIO | Impacta la búsqueda entre análisis: si todo es local, no se comparte entre personas. Preguntar |
| 12 | Playbooks | `harness/playbooks/<slug>.md` ejecutables con árbol de decisión (`03:377-447`) | "Bugs conocidos"; extensible con nuevos casos | COINCIDE (parcial) | El concepto sirve para bugs conocidos. En la doc queda amarrado a `knowledge/` y a promote |
| 13 | Promote | Caso cerrado → borrador de patrón sanitizado → PR (`02:396-398`, `03:182-193`), F2 | No lo mencionó | NO MENCIONADO POR USUARIO | Ceremonia de v2. Depende de `findings.md`, que también es F2 |
| 14 | Índice de knowledge | `knowledge/index.yml` con DSL de detección + `symptoms.es` (`03:451-482`) | No lo mencionó (sí "bugs conocidos") | NO MENCIONADO POR USUARIO | Un catálogo simple de known-issues puede cubrir la necesidad sin DSL |
| 15 | Orquestador (ADR-004) | Skill `/case` + CLI de estado; las skills corren inline y el orquestador rutea (`02:327-379`, `03:26-40`) | Orquestador liviano estilo sdd-lite: no carga contexto, persiste, **delega en subagentes**, guía | CONTRADICE (parcial) | Coincide "el CLI es la autoridad del estado". Difiere en que la doc no delega el trabajo en workers |
| 16 | Init | `doctor` (runtime, deps, permisos) + `new <id>` (`03:285-286`) | Init obligatorio que crea la estructura y **valida que las IAs funcionen** | NO CUBIERTO POR IDEA | No hay validación de Claude/Codex (wrappers, skills visibles, subagentes invocables) |
| 17 | Skill `case` | Orquestador conversacional, MVP (`03:26-40`) | Orquestador | COINCIDE | Rol equivalente al runtime del orquestador sdd-lite |
| 18 | Skill `interview` | Grill-me por bloques, MVP (`03:44-71`) | "Evaluar una skill tipo grill-me al inicio o cuando falta información" | COINCIDE | La doc lo limita al arranque (`03:51`). El usuario también la quiere a mitad de camino |
| 19 | Skill `triage` | Ingest + summarize + match contra index + decisión escrita (`03:75-90`) | Relevar y analizar | COINCIDE (parcial) | Depende de drain3 e `index.yml`. En v1 se puede reducir a manifest + coverage + known-issues |
| 20 | Skill `read-output` | Interpretar salida de scripts (`03:94-108`) | "Solo las skills necesarias" | NO MENCIONADO POR USUARIO | Conviene como regla compartida, no como skill |
| 21 | Skill `hypothesize` | ≥3 hipótesis ciegas, experimento por hipótesis, append (`03:112-150`) | Hipótesis como estado alcanzado | COINCIDE (parcial) | El mínimo de ≥3 y el sellado son ceremonia a validar |
| 22 | Skill `report` | Template + TLDR + verify-citations + challenger (`03:154-178`) | Relevamientos finales con templates simples | COINCIDE | — |
| 23 | Skill `promote` | F2 (`03:182`), aunque aparece en el diagrama principal (`02:16`) | — | NO MENCIONADO POR USUARIO | Fuera de v1 |
| 24 | Subagente `log-scout` | Barrido read-only multi-archivo, ≤40 líneas citadas (`03:219-240`) | Subagentes para relevar | COINCIDE | Encaja como worker de consulta. Ojo: `tools: Bash` puede leer logs completos (§3 #9) |
| 25 | Subagente `challenger` | Refutador adversarial, gate obligatorio (`03:242-264`, `02:377-379`) | No lo mencionó | NO MENCIONADO POR USUARIO | Valor medio. Candidato a opt-in |
| 26 | CLI `loga` y comandos | ~30 subcomandos: MVP con doctor/new/status/close/ingest/groups/coverage/summarize/grep/window/first-error/absence/detail/verify-citations/attempts/lint-case (`03:275-350`) | Scripts precisos y determinísticos, con skills relacionadas | COINCIDE (parcial) | Buen set de primitivas. Demasiado amplio para v1; faltan primitivas de métricas y comparación |
| 27 | Índice o skill de scripts | No existe; hay `output-contract.md`, `reading-logs.md` y `cookbook.md` para humanos (`02:90-98`) | "Tiene que haber un índice o una skill propia para los scripts" | NO CUBIERTO POR IDEA | Hace falta un catálogo máquina-legible (propósito, args, tipo de log, salida) |
| 28 | Runtime Python/uv/drain3 | Python 3.11+ con uv + PEP 723; drain3, pyyaml, orjson; rg/duckdb opcionales (`02:244-269`) | Linux, Mac y Windows | COINCIDE (parcial) | Cross-platform sí. A4 ("aceptan instalar uv") sin validar (`00:199`). Drain3 agrega dependencia y superficie. `cookbook.md` awk solo Linux/Mac (`02:267-269`) |
| 29 | Contrato de salida (ADR-008) | Envelope, NDJSON a disco, markdown al agente, presupuestos (`02:476-528`) | Devolver solo lo necesario, ahorrar tokens | COINCIDE | Adoptar la versión simplificada |
| 30 | Wrapper multi-agente y Cursor (ADR-009) | `AGENTS.md` fuente única, `CLAUDE.md` con `@AGENTS.md`; Codex/Cursor/Copilot/Gemini "con degradación" (`02:532-553`, `01:217`) | Igual en Claude y Codex | CONTRADICE (parcial) | Cursor/Copilot/Gemini: NO MENCIONADO POR USUARIO. "Degradación sin subagentes" contradice "funcionar igual" |
| 31 | Permisos (ADR-010) | `.claude/settings.json`: allow loga, `deny Read` sobre logs, `Write(./history/**)` (`02:557-585`) | No lo mencionó (sí "nunca pasa logs enteros") | NO MENCIONADO POR USUARIO | Solo Claude. No bloquea `Bash cat` ni aplica si `LOGA_HISTORY_DIR` apunta fuera del repo |
| 32 | i18n e idioma (ADR-011/012) | Identificadores en inglés; prosa en el idioma del usuario (default es); `i18n/<lang>.yml`; §0 Language; `lint-repo` (`02:589-679`) | No lo mencionó | NO MENCIONADO POR USUARIO | Identificadores en inglés coincide con sdd-lite. `i18n` yml + `lint-repo` exceden v1. Idioma de los md: preguntar |
| 33 | Privacidad y redacción (RF-8) | Gitignore agresivo, gitleaks pre-commit (M), CI (S), redacción (S), export sanitizado (`01:224-234`) | No lo mencionó | NO MENCIONADO POR USUARIO | Gitignore de logs: sí. gitleaks, CI y Presidio: fuera de v1 |
| 34 | Evals (RF-9) | Registrar causa real (M), backtest (S), runner (C), test de alucinación (S) (`01:236-243`) | "Sin evals por ahora" | CONTRADICE | Solo RF-9.1 (registrar resolución) sobrevive como metadata |
| 35 | Jira | ID de caso "típicamente de Jira" (`01:137`); pregunta abierta (`00:211-212`); export F2, MCP F3 | Cada análisis persiste ticket + descripción breve + status | NO CUBIERTO POR IDEA | La idea no define campos de ticket ni ciclo de status |
| 36 | Búsqueda entre análisis | `search <síntoma>` F2 (`03:290`), skill `compare` F2 (`03:201`), `related_cases` (`02:152`) | Buscar fácil entre análisis previos (p. ej. por status) | CONTRADICE (fase) | El usuario lo quiere en v1. Sin status declarado no hay filtro por status |
| 37 | Multi-pantalla y cross-log | `window` multi-archivo (M), grupos (M), baseline/target y `diff` (S), `fleet` y journey P2 (F2) (`01:98-104`, `03:202`, `03:324`) | Análisis cruzado de una pantalla y comparativo entre varias | CONTRADICE (fase) | En la doc el comparativo es F2. Para el usuario es core |
| 38 | Recursos (memoria/CPU) | Nada: solo `cadence`/`anomaly` de frecuencia (F2/F3, `03:326-328`); ningún parseo de series numéricas | Patrones como escalado de memoria o CPU | NO CUBIERTO POR IDEA | Hace falta una primitiva de series métricas (extraer valor numérico + tendencia por pantalla) |
| 39 | Inconsistencias y bugs conocidos | Known-noise, playbooks, `absence`, `diff` | Detectar inconsistencias y bugs conocidos | COINCIDE (parcial) | "Inconsistencias" (p. ej. contradicciones entre archivos o pantallas) no está definido |
| 40 | Extensibilidad a nuevos tipos de log o casos | `formato_detectado` + `parse_rate` (`01:150`); A3 versionado (`00:198`); subagente `normalizador` F2 (`03:270`); nuevos playbooks | "Extensible con nuevos casos o nuevos tipos de logs" | NO CUBIERTO POR IDEA (parcial) | Casos: sí, vía playbooks. Tipos de log: no hay registro de formatos (ts regex, prefijos, ruido) ni convención para agregar scripts |
| 41 | Interactividad | Interview con gating, "declarar la decisión", no saltear pasos (`03:36`, `03:67-68`, `03:84`) | No asume nada; ayuda a confirmar el problema | COINCIDE | — |
| 42 | Read-only / no remediación | Read-only por diseño (`00:243`, `01:48`) | No lo mencionó | NO MENCIONADO POR USUARIO | Compatible. Barato de adoptar |
| 43 | Fases y estimaciones | F0 2-3 días, F1 2-3 semanas, F2 2-3 semanas, F3 continuo (`01:301-308`, `04:37-101`) | v1 simple pero funcional | CONTRADICE | El MVP de la doc (≈16 comandos, 6 skills, 2 subagentes, 9 docs, i18n) no es "simple". Además las estimaciones no suman (§3 #12) |

---

## 3. Contradicciones internas de la doc

| # | Contradicción | Citas | Impacto |
|---|---|---|---|
| 1 | **Cantidad de skills y subagentes del MVP**: "5 skills, 2 subagentes" vs "4 skills, 1 subagente" vs 6 skills MVP + 2 subagentes MVP. El diagrama general lista 6 skills sin `read-output` y con `promote` (F2) | `README:46-47`, `01:306`, `03:26-242` ([MVP] en case/interview/triage/read-output/hypothesize/report, log-scout, challenger), `04:62-65`, `02:16` | Alto: alcance indefinido |
| 2 | **Fase de `knowledge/index.yml` y del matcheo**: RF-6.2/6.3 son Must, el journey P1 y AC4 matchean en MVP; pero Fase 2 y F2-1 los ubican en F2 | `01:206-207`, `01:79-80`, `01:285`, `01:307`, `04:76` | Alto: el criterio de aceptación #4 depende de algo de F2 |
| 3 | **Fase de hipótesis**: RF-5.3/5.5 Must y `hypothesize` [MVP] + F1-12, pero Fase 2 entrega "Hipótesis formales" | `01:193-195`, `03:112`, `04:64`, `01:307` | Medio |
| 4 | **"Estado derivado, nunca declarado" usa campos declarados**: `closed` = `resolution != null`; `interviewed` depende de respuestas escritas en `case.yaml`; `triaged` depende de un `triage.md` escrito por el LLM (no hay comando `loga triage`) | `02:170-175`, `03:69`, `03:88`, `03:281-292` | Alto: el principio no se sostiene tal cual. Refuerza el status híbrido |
| 5 | **`case.yaml` sin lugar para el interview**: el interview "se escribe a `case.yaml`", pero el schema no tiene campos para esas respuestas | `03:69`, `02:138-155` | Medio |
| 6 | **Fast path vs gates obligatorios**: un caso trivial "se cierra con 2 archivos", pero `case` "nunca" saltea el interview, `reported` exige verify-citations y hay "dos puertas de las que no se sale" (challenger + verify). ADR-002 Fase 1 exige además `logs/` + `attempts.ndjson` | `02:233-238`, `01:290`, `03:36`, `02:174`, `02:377-379`, `02:281` | Alto: la regla de flujo no está definida |
| 7 | **¿Challenger siempre o solo en hipótesis nuevas?** El flujo de ADR-004 lo aplica solo en la rama `hypothesize` (patrón conocido → playbook directo), pero `report` y `CLAUDE.md` lo exigen antes de todo veredicto | `02:359-365`, `03:173`, `02:547` | Medio |
| 8 | **Journey P1 incoherente con la tabla de estados**: `status` devuelve `empty · next=ingest`, pero `empty` = "no hay nada en `logs/`" y Vale ya copió los logs | `01:68-72`, `02:168` | Bajo |
| 9 | **"El agente no puede reescribir/leer aunque quiera" no se garantiza**: `Write(./history/**)` permite reescribir `attempts.ndjson`; `log-scout` y `challenger` tienen `Bash` (pueden `cat` un log); el `deny Read` es relativo al repo y deja de aplicar con `LOGA_HISTORY_DIR` externo | `02:228-230`, `02:33`, `02:567-573`, `03:225`, `03:248`, `02:419-422` | Alto: la inmutabilidad y el anti-context-rot son convención, no enforcement. La validación tiene que ser por script (hash/secuencia) |
| 10 | **Idioma en el MVP**: Fase 1 solo `es.yml` y `en.yml` es Could/F3, pero AC9 exige responder en inglés en el MVP | `02:647-648`, `01:257`, `04:101`, `01:291-294` | Medio |
| 11 | **Violaciones de ADR-012 dentro de la propia doc**: claves del manifest en español (`archivo, grupo, primer_ts, líneas`), `ejemplo`, `señal:`, docs nombrados en español en F1-9, subagentes `normalizador`/`catalogador` | `01:150`, `03:298`, `03:317`, `03:389`, `04:61`, `03:270-271` vs `02:658-663` | Bajo, pero muestra el costo de la regla |
| 12 | **Estimaciones que no suman**: F0 = 4 días (dice 2-3); F1 = 23 días-persona ≈ 4,5 semanas (dice 2-3); F2 = 21,5 días ≈ 4,3 semanas (dice 2-3) | `04:37-47`, `04:49-67`, `04:72-87`, `01:305-307` | Alto para planificar |
| 13 | **Gate de F1 cita "8 criterios"**, pero PRD §7 tiene 9; F0-3 confirma "ADR-001 a ADR-010", pero hay 12 ADRs | `04:69`, `01:280-294`, `04:43`, `README:12` | Bajo |
| 14 | **Enum de estado de hipótesis inconsistente**: `open/supported/refuted/superseded` vs `supported/refuted/inconclusive` | `01:194`, `04:13`, `00:143` | Medio (afecta el schema) |
| 15 | **Artefactos F2 usados en contratos MVP**: `report` verifica `analysis.md` y `promote` parte de `findings.md`, ambos opcionales de F2 | `03:171`, `02:396`, `03:292`, `02:281-283` | Medio |
| 16 | **Fase de `coverage` y `groups`**: MVP en el catálogo, F2 en el backlog; los roles baseline/target son S | `03:299-300`, `04:77-78`, `01:139` | Bajo |
| 17 | **RNF-2 "cero dependencias" vs gitleaks + pre-commit Must** y "primer valor < 5 min" | `01:266-267`, `01:229`, `02:58` | Medio |
| 18 | **C2 "todo lo generado se ignora" se reinterpreta** en ADR-005 para commitear `knowledge/` | `00:180`, `02:385-387` | Bajo (tensión declarada) |
| 19 | **"Contenido en una carpeta" (C6) vs árbol con 6 entradas en raíz** (`AGENTS.md`, `CLAUDE.md`, `.claude/`, `knowledge/`, `history/`, `harness/`) | `00:184`, `02:52-129` | Medio: la contención queda solo parcial |
| 20 | **Posicionamiento "no dice qué pasó" vs visión "veredicto en minutos"** y la hoja "CAUSA IDENTIFICADA" | `01:31`, `01:21-23`, `03:428` | Bajo (tono) |

---

## 4. Propuesta dentro/fuera de la v1

> **PROPUESTA A VALIDAR CON EL USUARIO.** Surge de la matriz. Nombres de carpetas y archivos ilustrativos.

### 4.1 Dentro de la v1

| Área | Qué entra | Origen |
|---|---|---|
| Estructura | Paquete estilo sdd-lite (`orchestrator/`, `skills/`, `schemas/`, `templates/`, `scripts/`) + init que instala wrappers para Claude y Codex y crea la carpeta de análisis | Usuario; ADR-003/009 como concepto |
| Init | Crea estructura y config, verifica runtime de scripts y **hace un smoke test por IA** (skills visibles, un worker invocable, un script con envelope) | Usuario (no cubierto por idea); `doctor` (`03:285`) |
| Carpeta por análisis | `analyses/<ticket>-<slug>/` con `logs/` (plano o `logs/<screen>/`, un nivel), `record/` (persistencia) y md humanos en la raíz del análisis | Usuario; C5 de §2 |
| Persistencia `record/` | `analysis.yaml` (ticket, resumen, fechas, plataforma, versión del player, pantallas, `status` declarado, `related`), `manifest.json` (generado), `journal.ndjson` append-only (findings + hipótesis + decisiones, con `supersedes`), `runs/` con solo resumen + comando + hash (salida completa opcional) | C6, C8, C16; reconciliación de #8 |
| Status | `status` declarado de lista cerrada (a definir con el usuario) + `progress` derivado por script, que sugiere la siguiente acción | C18; contradicción #4 |
| Validación | Script `validate` con schema para `analysis.yaml` y `journal.ndjson` (append-only chequeado por secuencia/hash) + `verify-citations` | C6, C7; contradicción #9 |
| Scripts core | `ingest` (manifest, encoding, orden por ts, `parse_rate`), `coverage`, `grep`, `window`, `first-seen`, `absence`, `counts` (por componente/nivel, sin drain3), `metric-series` (memoria/CPU: extracción numérica + tendencia), `compare` (por pantalla), `search` (entre análisis por status/ticket/plataforma/versión/texto), `verify-citations`, `validate`, `status` | C2-C5, C7, C17; gaps #38, #36 |
| Contrato de salida | Envelope `returned/totalCount/truncated/nextCursor/artifact/next`, markdown compacto al agente, cita `archivo:línea` + excerpt ≤200 | C2, C3 |
| Índice de scripts | `scripts/index.yaml` (id, propósito, args, tipos de log soportados, forma de salida) consultado por una skill de consulta | Usuario (gap #27) |
| Extensibilidad | `log-types/<type>.yaml` (regex de ts, prefijos de componente, ruido conocido, métricas extraíbles) + `known-issues/<id>.md` (síntoma, firma ejecutable, árbol de decisión, descartes) | C14, C15, C22 simplificado; gap #40 |
| Skills v1 | orquestador (`analysis`), `init`, `intake` (grill-me, reutilizable a mitad de camino), `query` (worker de scripts, ex `log-scout`), `analyze` (findings + hipótesis falsables), `report` | Usuario; C10, C8, C13 |
| Reglas compartidas | Lectura de salidas (C12), logs como dato (C19), parar sin cobertura (C11), no asumir | Idea como `_shared` |
| Reportes | `SUMMARY.md` vivo (tipo TLDR) + `report-findings.md` (hallazgos formalizados) + `report-status.md` (estado alcanzado / hipótesis sin conclusión). Opcional: bloque breve para pegar en Jira | C13; usuario |
| Aceptación | Reproducir a mano un caso conocido (p. ej. menuboard-fetch) sin evals | C25 |

### 4.2 Fuera de la v1 (diferido)

| Qué | Por qué | Cita |
|---|---|---|
| `knowledge/` + `promote` + flujo PR + `index.yml` con DSL | No lo pidió el usuario; ceremonia; depende de F2 | `02:383-398`, `03:182-193`, `03:451-482` |
| Drain3 `summarize` | Dependencia y masking de dominio; `counts` + `grep` cubren v1 | `02:426-444` |
| Challenger obligatorio | Valor medio y costo de paridad. En v1, checklist en `report` o modo opt-in | `03:242-264` |
| Hipótesis sellada, mínimo de ≥3 hipótesis | Ceremonia; no enforceable inline | `03:64-66`, `03:115` |
| `i18n/<lang>.yml`, §0 Language elaborado, `lint-repo` | Sobrediseño para v1 | `02:589-679` |
| gitleaks, CI, Presidio/`redact`, `export` sanitizado | No pedido; alcanza con gitignore de logs | `01:224-234` |
| Evals, backtest, test de alucinación | Pedido explícito: sin evals | `01:236-243` |
| `trace`, `bisect`, `anomaly`, `cadence`, `timeline` | Depende de correlation ids (pregunta abierta `00:207-209`) y de uso real | `03:323-328` |
| `fleet`, `postmortem`, `review-harness`, plugin, MCP Jira, Agent SDK batch, hooks | F2/F3 en la propia doc | `03:197-205`, `04:89-101`, `02:581-583` |
| Cursor/Copilot/Gemini | No pedidos | `01:217` |
| `archive` y `history/archive/` | Innecesario si la búsqueda filtra por status | `03:289` |

---

## 5. Preguntas para el usuario

Formato: pregunta → opciones → **recomendación** (con la evidencia). Solo preguntas que cambian el diseño.

### 5.1 Topología y repo

1. **¿Qué es exactamente "el repo que se clona"?**
   (a) `ai-tools` con `harness/log-assist/` usado in situ · (b) repo dedicado de análisis donde un init instala el harness desde ai-tools (modelo sdd-lite) · (c) el harness vive en un repo propio que ya trae todo instalado.
   **Rec: (b) o (c).** Claude y Codex descubren skills y wrappers desde la raíz (`02:289-290`, `02:534`). In situ ensucia ai-tools con logs y análisis.
2. **¿Los análisis se commitean?**
   (a) todo gitignorado (la idea, `02:391-393`) · (b) logs ignorados, `record/` + md commiteados · (c) análisis en repo privado aparte o carpeta externa (`02:419-422`).
   **Rec: logs siempre ignorados; `record/` + md commiteables por config.** Sin eso, la búsqueda entre análisis previos no se comparte entre personas.
3. **¿Quién usa la v1?**
   (a) vos y devs (Linux/Mac/Windows técnicos) · (b) también QA/Ops no técnicos en Windows (`01:57`).
   **Rec: (a) para v1.** Define el runtime (5.5 #1) y cuánto invertir en fricción cero (`01:267`).
4. **Nombre y prefijos**: ¿`log-assist` para todo (skills `la-*`?, CLI) o se mantiene `loga`?
   **Rec: `log-assist` como paquete** y un prefijo corto único para skills y CLI, igual que `sddl-*`.

### 5.2 Persistencia

1. **Status: ¿declarado, derivado o ambos?**
   (a) solo derivado (idea) · (b) solo declarado · (c) `status` declarado + `progress` derivado.
   **Rec: (c).** El usuario quiere filtrar por status. La propia doc termina declarando campos (§3 #4).
2. **Lista de status y metadata Jira mínima**: ¿`open / in-progress / needs-info / hypothesis / confirmed / closed / discarded`? ¿Campos obligatorios: ticket, fecha del incidente, plataforma, versión del player, pantallas, resumen de 1-2 líneas? ¿Resolución al cerrar?
   **Rec: 5-7 estados + 6 campos obligatorios.** Resolución opcional (RF-9.1 sin evals).
3. **¿Un análisis por ticket o varios por ticket?** (p. ej. reabrir con logs nuevos)
   **Rec: carpeta `<ticket>-<slug>`**, lo que permite varios por ticket y `related` entre ellos.
4. **Formato del registro**:
   (a) NDJSON append-only único (`journal`) · (b) archivos separados por tipo (`findings.ndjson`, `hypotheses.ndjson`) · (c) md por paso estilo openspec.
   **Rec: (a) o (b) con schema**, más md solo en hitos. NDJSON es validable y no se corrompe (`02:228-231`). Los md no son validables.
5. **¿Guardar salidas completas de scripts dentro del análisis?** (`.work/`, `01:179`)
   (a) siempre · (b) solo resumen + comando + hash, regenerable · (c) opcional por flag.
   **Rec: (b)/(c).** Las salidas completas repiten excerpts de log (tamaño, privacidad) y la capa es determinística (`01:271`).
6. **Logs multi-pantalla**: ¿nombre de subcarpeta = ID de pantalla/dispositivo? ¿se marca una pantalla sana como baseline? ¿mezcla de tipos de log en una misma pantalla?
   **Rec: un nivel `logs/<screen-id>/`**, rol `baseline/target` opcional en `analysis.yaml` (`02:146-148`).

### 5.3 Orquestador y flujo

1. **Gates**: ¿qué es obligatorio antes de avanzar?
   (a) intake mínimo antes de correr scripts · (b) `verify-citations` antes de cualquier reporte · (c) challenger antes de "confirmed".
   **Rec: (a) mínimo + (b) duro; (c) opt-in.** Resuelve la contradicción fast path vs gates (§3 #6).
2. **Delegación**: ¿el orquestador puede correr inline scripts de salida acotada, o todo pasa por workers?
   **Rec: umbral estilo sdd-lite.** Consultas puntuales (`status`, `search`) inline; barridos multi-archivo o multi-pantalla y análisis en workers (`02:545-546` usa ">3 archivos").
3. **¿Buscar análisis relacionados al iniciar siempre?** (por plataforma, versión y síntoma)
   **Rec: sí, paso fijo del intake**, con `search` determinístico.
4. **Hipótesis del usuario**: ¿sellarla (`03:64-66`) o registrarla como una hipótesis más con `source: user`?
   **Rec: registrarla con `source: user` y `predicts_false` obligatorio.** El sellado no es enforceable en la misma sesión.

### 5.4 Skills y subagentes

1. **Set v1**: ¿`analysis` (orquestador), `init`, `intake`, `query`, `analyze`, `report`? ¿Falta o sobra alguna?
   **Rec: esas 6.** `read-output` pasa a regla compartida y `triage` se funde en intake + query (§2 #19-20).
2. **Grill-me**: ¿skill propia reutilizable (inicio y "falta información") o bloque dentro del orquestador?
   **Rec: skill propia `intake`** con los bloques de `03:53-61`, invocable en cualquier punto.
3. **Paridad Codex**: ¿se acepta que Codex corra los mismos workers con otro mecanismo, o puede degradar?
   **Rec: contrato de worker neutral** (prompt + paths + salida acotada), mapeado por wrapper a cada IA, como sdd-lite. La idea degrada (`02:551-553`), lo que contradice "funcionar igual". Verificar las capacidades vigentes de Codex para subagentes.
4. **Challenger**: ¿entra en v1?
   **Rec: opt-in** (checklist de 6 preguntas `03:253-258` dentro de `report` por defecto).

### 5.5 Scripts

1. **Runtime**:
   (a) Python 3 solo stdlib · (b) Python + uv + PEP 723 + drain3 (idea) · (c) Node · (d) bash + PowerShell duplicados (descartado en `02:248`).
   **Rec: (a), con uv opcional.** Cross-platform y legible (`02:249`), sin dependencias que instalar. Drain3 fuera de v1. Validar que Python esté disponible en las máquinas Windows objetivo (A4 `00:199` sin validar).
2. **Organización**:
   (a) CLI único con subcomandos (idea, `03:277`) · (b) scripts sueltos por tipo de log/caso · (c) core de primitivas genéricas + extensiones por tipo de log/known-issue registradas en `scripts/index.yaml`.
   **Rec: (c).** Cumple "índice o skill de scripts" y "extensible" sin reescribir el core.
3. **Tipos de log v1**: ¿solo DexPlayer (`00:38`)? ¿qué otros (plataformas Tizen/Android/Windows, backend)? ¿hay correlation ids (`00:207-209`)?
   **Rec: v1 con 1 tipo + mecanismo `log-types/`** probado con un segundo tipo mínimo.
4. **Métricas de recursos**: ¿qué líneas reportan memoria/CPU y en qué formato? ¿por pantalla o por proceso?
   **Rec: definir 1-2 métricas reales antes de diseñar `metric-series`.** La idea no las cubre.
5. **`docs/scripts-idea/`**: ¿es el catálogo candidato de scripts de dominio para v1?
   **Rec: analizarlo aparte** antes de cerrar el set de scripts.

### 5.6 Reportes

1. **Tipos v1**: ¿`SUMMARY` vivo + `report-findings` + `report-status` (hipótesis sin conclusión)? ¿Comparativo multi-pantalla como tipo propio? ¿Bloque para Jira?
   **Rec: 3 templates + bloque Jira dentro de `SUMMARY`.** El comparativo, como sección condicional.
2. **Idioma de los md generados**:
   (a) español (idea, `02:596`) · (b) inglés como sdd-lite · (c) configurable en init.
   **Rec: (c)**, con identificadores y claves siempre en inglés y excerpts verbatim (`02:597`), sin `i18n` yml.
3. **Citas**: ¿toda afirmación de reporte con `archivo:línea` verificada, incluso en el reporte de estado/hipótesis?
   **Rec: sí**, es barato (`03:348-350`). Las hipótesis sin evidencia se marcan como tales.

### 5.7 Fuera de alcance

1. **Confirmar fuera de v1**: `knowledge/` + promote vía PR, drain3, gitleaks/CI/redacción, evals/backtest, fleet, postmortem, hooks, Cursor/Copilot/Gemini, MCP Jira.
   **Rec: todo fuera** (§4.2).
2. **Bugs conocidos en v1**: ¿catálogo simple `known-issues/` con firma ejecutable, o también índice de síntomas en lenguaje natural (`symptoms.es`, `03:472-474`)?
   **Rec: catálogo simple con firmas grep/absence**, más una lista breve de frases de síntoma sin DSL.
3. **Read-only estricto**: ¿el harness nunca ejecuta acciones sobre pantallas o tickets? (`01:48`)
   **Rec: sí**; mitiga la inyección desde logs (`04:14`).
