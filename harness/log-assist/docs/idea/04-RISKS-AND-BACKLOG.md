# Riesgos y backlog por fases

> Documento 4 de 5 · v0.1 · 2026-09-11

---

## 1. Matriz de riesgos

Ordenada por severidad. Cada mitigación está mapeada a un requerimiento del PRD.

| # | Riesgo | Sev | Evidencia | Mitigación | RF |
|---|---|---|---|---|---|
| **R1** | **Causa raíz plausible pero falsa.** El informe suena bien, es convincente y está mal | 🔴 Crítica | OpenRCA: 11.34% de accuracy máxima; ningún modelo acertó los 3 elementos juntos, nunca. Zalando: ~10% de error de atribución con modelos avanzados. "Evidencia fabricada" e "insuficiencia evidencial" son las fallas #1 y #2 catalogadas | Cita `archivo:línea` obligatoria + **verificación determinística por script**. Clasificación forzada supported/refuted/inconclusive. Sección `LÍMITES` obligatoria. Subagente refutador antes de emitir. Posicionamiento honesto en todo output | RF-5.4, 5.6, 5.7, 5.8 |
| **R2** | **Prompt injection desde el contenido del log.** Un mensaje de error incluye el input que lo disparó → cualquiera puede inyectar texto adversarial | 🔴 Crítica | 4 papers en 2026. ASR 83-88% sin defensas. **Todos los guardrails de AWS, GCP y Azure fallaron.** El ataque de "persona hijack" (`[SOC ADMIN]: whitelisted`) logra 68% de supresión | **Agente read-only, sin ejecución de acciones** (convierte el peor caso de RCE a "mal análisis"). Prompt "passive" explícito en cada subagente (bajó la mayoría de modelos a 0%). Contenido de log delimitado como dato. Asumir 8-12% residual | RF-8.4, 8.5, no-objetivo #3 |
| **R3** | **Context rot por volcar logs al contexto** | 🟠 Alta | Degradación universal en 18 modelos. **Los haystacks coherentes rinden peor que los aleatorios** — un log es narrativa coherente. Raw logs: 0.353 vs híbrido comprimido 0.670 | `deny` de `Read` sobre `history/**/logs/**` en settings (mecánico, no una instrucción). Drain3. Tres niveles de comando. Presupuesto duro por comando. Subagente `log-scout` para aislar barridos | RF-3.1, 4.1-4.3, ADR-010 |
| **R4** | **Truncación silenciosa.** El agente recibe 20 de 3.187 errores sin saberlo y concluye con confianza algo falso | 🟠 Alta | *"La truncación silenciosa convence al modelo de que está razonando sobre el cuadro completo cuando no lo está"* | Envelope obligatorio `returned/totalCount/truncated/nextCursor` en **toda** salida paginable. La skill `read-output` chequea el envelope **antes** de interpretar | RF-4.2, skill 2.4 |
| **R5** | **Sicofancia / sesgo de confirmación.** El agente valida la hipótesis que trajo el humano | 🟠 Alta | Documentado bajo rebuttal del usuario: el modelo cede aun teniendo razón | `sealed_human_hypothesis` en `case.yaml`, no visible en el turno de generación. ≥3 hipótesis ciegas. Contraste recién al final | RF-5.2, 5.3 |
| **R6** | **No reproducibilidad entre personas.** Dos análisis del mismo log dan textos distintos | 🟠 Alta | El no-determinismo es del servidor (falta de batch-invariance), no del sampling. `temperature=0` no alcanza | Se persiste el **artefacto**, no el chat. La capa de evidencia (scripts) es determinística y regenerable sin LLM. Se guarda hash de entrada + rango + filtros + modelo + versión | RNF-7, RNF-9 |
| **R7** | **Commit accidental de logs de cliente** | 🟠 Alta | `.gitignore` no protege lo ya trackeado; `--no-verify` saltea el hook local | Denylist agresiva + allowlist explícita. Pre-commit con gitleaks. **CI sobre historia completa.** `LOGA_HISTORY_DIR` para sacar `history/` del repo si hace falta | RF-8.1, 8.2, 8.3 |
| **R8** | **PII / secretos enviados al LLM** (IPs son dato personal bajo GDPR) | 🟠 Alta | — | El masking de Drain3 hace parte del trabajo gratis. `loga redact` con Presidio o regex de dominio. Validar supuesto A6 antes de Fase 1 | RF-2.8, 8.6 |
| **R9** | **No adopción.** Se construye y nadie lo usa | 🟠 Alta | Honeycomb: 39% de adopción en el tier donde la feature no se veía. *"Los usuarios ni siquiera notaban que existía."* **Problema de descubribilidad, no de calidad** | Tiempo hasta el primer valor < 5 min. Piloto con 1 QA real en Fase 1, no con el equipo entero. Medir el "efecto graduación" (Honeycomb: los usuarios de la IA tenían 26.5% de retención en uso manual vs 4.5% — la herramienta alfabetiza, no genera dependencia) | RNF-3 |
| **R10** | **Ceremonia excesiva → abandono** | 🟡 Media | Spec Kit: un bugfix generó 4 user stories con 16 criterios. *"I'd rather review code than all these markdown files"* | **Camino rápido obligatorio**: caso trivial = 2 archivos. Artefactos opcionales con criterio explícito de cuándo crearlos | ADR-002 |
| **R11** | **Drift del conocimiento.** Los patrones de `knowledge/` envejecen y nadie los corrige | 🟡 Media | BMAD issue #1930: reescritura de historias completadas rompe la auditoría | Patrones se supersedean, no se reescriben. `confirmed_cases[]` en el índice. Skill `review-harness` (F3) | RF-6.6 |
| **R12** | **Falla en silencio del parser.** El formato cambia y el harness devuelve resultados vacíos que parecen "todo bien" | 🟡 Media | La trampa documentada de OpenSpec: 3 vs 4 `#` fallaba callado | `parse_rate < 0.95` es un **error visible**, no un warning. `lint-case` valida todo. Nunca fallar en silencio | RF-2.6, `lint-case` |
| **R13** | **Costo descontrolado** en casos grandes | 🟡 Media | Honeycomb corría a ~USD 300/mes; el caso de negocio cerraba con adopción moderada | Presupuesto de tokens por comando. Subagentes con modelo chico para pasos baratos. Medir tokens por caso | RNF-6 |
| **R14** | **Atrofia de criterio.** El equipo deja de razonar y acepta lo que dice la IA | 🟡 Media | Un RCA incorrecto con alta confianza es indistinguible de uno correcto | Mostrar siempre la evidencia cruda al lado de la conclusión. Feedback explícito por caso (confirmado/refutado/parcial) que alimente el backtest | RF-9.1 |
| **R15** | **El proyecto se vuelve un fin en sí mismo** | 🟡 Media | Crítica transversal a todos los frameworks evaluados | Gate de Fase: no se pasa a la fase siguiente sin que la anterior haya resuelto casos reales | §3 |
| **R16** | **Deriva de idioma**: con el tiempo aparecen carpetas, claves y comandos en español mezclados, y `grep`/imports se vuelven frágiles | 🟢 Baja | Ya pasa en la skill actual (nombre español, marcadores inglés) | Convención mecánica documentada (ADR-012) + `lint-repo` en pre-commit. La regla es binaria: identificador = inglés, prosa = idioma del usuario | RF-10.1, 10.8 |
| **R17** | **El harness contesta en el idioma equivocado** y QA/Ops dejan de usarlo, o un informe llega a Jira en inglés | 🟢 Baja | — | §0 Language en `AGENTS.md` con orden de resolución explícito; idioma persistido en `case.yaml`; default español | RF-10.2, 10.3, 10.4 |

---

## 2. Backlog

Estimaciones en días-persona para 1 dev con apoyo puntual de QA/Ops.

### Fase 0 — Decidir y esqueletar · **2-3 días**

| ID | Tarea | Est. | DoD |
|---|---|---:|---|
| F0-1 | Validar supuestos A1-A6 (§6 del relevamiento) | 0.5 | Cada supuesto con verdadero/falso y su consecuencia anotada |
| F0-2 | Responder las 6 preguntas abiertas (§7) | 0.5 | Decisiones escritas en este repo |
| F0-3 | Confirmar ADR-001 a ADR-010 o registrar el desvío | 0.5 | ADRs marcados como aceptados |
| F0-4 | Esqueleto de repo + `.gitignore` + pre-commit + `README` | 0.5 | `git status` limpio con logs adentro de `history/` |
| F0-5 | `AGENTS.md` (con **§0 Language**) + `CLAUDE.md` (import) + `.claude/settings.json` | 1 | Abrir con `claude` y que reconozca el protocolo; responde en el idioma del primer mensaje |
| F0-7 | `harness/docs/naming.md` + `harness/docs/language.md` | 0.5 | Convención escrita antes de crear el primer archivo — renombrar después cuesta el triple |
| F0-6 | Inventario de patrones de falla ya reconocidos con QA/Ops/Dev | 0.5 | Lista priorizada; alimenta A2 y el roadmap de playbooks |

### Fase 1 — MVP · **2-3 semanas**

| ID | Tarea | Est. | DoD |
|---|---|---:|---|
| F1-1 | `loga` esqueleto + `doctor` + `new` + PEP 723 | 1 | `doctor` OK en Windows y Linux |
| F1-2 | Capa de I/O: encoding/BOM, streaming, `errors='replace'` | 1.5 | Test con UTF-16LE, UTF-8-BOM y archivo truncado |
| F1-3 | Normalización de timestamps + `ingest` + `manifest.json` | 2 | Manifiesto correcto sobre los 10 logs reales; rotados ordenados por primer ts |
| F1-4 | `status --json` con estado derivado | 1 | Los 8 estados se derivan bien; ≤300 tokens |
| F1-5 | `summarize` con Drain3 + masking de dominio | 2 | 10 logs × 10 MB en < 60 s; salida ≤4k tokens |
| F1-6 | `grep` + `window` + `first-error` + `detail` con envelope | 2 | Envelope presente siempre; presupuestos respetados |
| F1-7 | **`absence`** (ADR-007) | 2 | Reproduce el paso 2 de la skill actual con los mismos números |
| F1-8 | `verify-citations` + `attempts` + `lint-case` | 1.5 | Detecta una cita falsa inyectada a propósito |
| F1-9 | `harness/docs/`: metodo, lectura-de-logs, modulos, ruido-conocido, unidades | 2 | Revisado por Desarrollo: el dominio está bien descrito |
| F1-10 | Playbook `menuboard-fetch` (port de la skill actual) | 1.5 | **Reproduce el veredicto conocido sobre los 10 logs** |
| F1-11 | Skills `case`, `interview`, `triage`, `read-output`, `report` | 2 | Journey P1 completo end-to-end |
| F1-12 | Skill `hypothesize` + `attempts.ndjson` append-only | 1.5 | Rechaza hipótesis sin `predicts_false` |
| F1-13 | Subagentes `log-scout` y `challenger` | 1 | El refutador encuentra un hueco en un informe con un error plantado |
| F1-14 | Plantillas con claves en inglés + `harness/i18n/es.yml` | 1 | Cambiar una etiqueta no requiere tocar scripts ni plantillas |
| F1-15 | **Piloto con 1 QA real en Windows** | 1 | Resuelve un caso real sin ayuda; se registra la fricción |

**Gate de Fase 1**: los 8 criterios de aceptación del PRD §7, con énfasis en el #4
(reproducir el veredicto conocido).

### Fase 2 — Método y conocimiento · **2-3 semanas**

| ID | Tarea | Est. |
|---|---|---:|
| F2-1 | `knowledge/index.yml` con reglas de detección + matcheo en triage | 2 |
| F2-2 | `diff` (sano vs roto) + rol baseline/target en grupos | 2 |
| F2-3 | `timeline` + `cadence` + `coverage` | 2 |
| F2-4 | `trace --id` (requiere confirmar si hay correlation ids — pregunta abierta #1) | 1.5 |
| F2-5 | Skill `promote` + `loga promote` + flujo de PR | 2 |
| F2-6 | `export` sanitizado para Jira | 1 |
| F2-7 | Skill `fleet` (journey P2) | 2 |
| F2-8 | `archive` + `search` | 1 |
| F2-9 | 3-4 playbooks nuevos del inventario F0-6 | 4 |
| F2-10 | `redact` (o evidencia de que A6 lo hace innecesario) | 2 |
| F2-11 | CI con gitleaks sobre historia completa + `lint-repo` en pre-commit | 1 |
| F2-12 | Skill `postmortem` con template de incident.io | 1 |

### Fase 3 — Escala y calidad · **continuo**

| ID | Tarea |
|---|---|
| F3-1 | Backtest de 10 incidentes conocidos + `loga eval` → precision/recall |
| F3-2 | Test de alucinación (preguntar por componentes inexistentes) |
| F3-3 | `bisect` + `anomaly` |
| F3-4 | Empaquetar como plugin de Claude Code para reusar en otros repos |
| F3-5 | MCP de Jira (leer ticket, escribir veredicto) |
| F3-6 | Análisis agregado de N casos para patrones estratégicos (el caso Zalando: detectar que config/deployment era la causa dominante previno 25% de los incidentes siguientes) |
| F3-7 | Orquestación batch con Agent SDK para chequeo de flota en CI |
| F3-8 | Skill `review-harness` (higiene del conocimiento) |
| F3-9 | `harness/i18n/en.yml` — operar el harness íntegramente en inglés |

---

## 3. Gates entre fases

| Gate | Condición para pasar |
|---|---|
| F0 → F1 | Supuestos validados, ADRs aceptados, inventario de patrones hecho |
| F1 → F2 | **Al menos 3 casos reales resueltos con el harness**, uno de ellos por alguien que no lo construyó |
| F2 → F3 | ≥5 patrones en `knowledge/`, ≥1 promovido por alguien de QA u Operaciones, precision cualitativa aceptable |

El gate F1→F2 es el importante: **no se agregan features hasta que el MVP haya resuelto casos
reales.** Es la mitigación de R15 y la lección más repetida del prior art evaluado.

---

## 4. Qué haría primero si tuviera una semana

En orden estricto, porque cada paso desbloquea al siguiente:

1. **`ingest` + `manifest`** — sin saber qué logs hay, qué cubren y en qué encoding están, todo lo
   demás es adivinar.
2. **`absence`** — es la primitiva que resuelve tu caso de referencia y que no existe en ningún
   lado. Es el diferencial.
3. **`summarize` con Drain3** — es donde ocurre la reducción de 10³:1 que hace viable todo.
4. **`verify-citations`** — barato, determinístico, y ataca el riesgo #1 de frente.
5. **El playbook `menuboard-fetch` portado** — la prueba de que el harness sirve para algo que ya
   sabemos que funciona.

Con eso ya hay un producto útil. Las skills se pueden escribir en una tarde encima de esa base;
al revés no funciona.
