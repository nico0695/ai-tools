# blueprint-harness — Guía de Usuario

Guía práctica para instalar y usar `blueprint-harness` en el día a día. Para el fundamento de diseño ver `blueprint-spec.md`; para un vistazo rápido ver `README.md`.

> Traducción de `USER-GUIDE.md`. Ante cualquier diferencia, vale la versión en inglés. Los identificadores del sistema (nombres de skills, archivos, estados como `draft`/`approved`) se mantienen en inglés porque son valores literales del motor.

---

## Tabla de contenidos

1. [¿Qué es blueprint-harness?](#1-qué-es-blueprint-harness)
2. [Cuándo usarlo (y cuándo no)](#2-cuándo-usarlo-y-cuándo-no)
3. [Conceptos clave](#3-conceptos-clave)
4. [Setup (`bp-init`)](#4-setup-bp-init)
5. [El archivo `config.yaml`](#5-el-archivo-configyaml)
6. [Layout de archivos en runtime](#6-layout-de-archivos-en-runtime)
7. [Las 7 skills](#7-las-7-skills)
8. [Los tres flujos](#8-los-tres-flujos)
9. [Cómo se garantiza el read-only](#9-cómo-se-garantiza-el-read-only)
10. [Ejemplos de uso](#10-ejemplos-de-uso)
11. [Qué NO hacer](#11-qué-no-hacer)
12. [Handoff hacia sdd-lite](#12-handoff-hacia-sdd-lite)

---

## 1. ¿Qué es blueprint-harness?

`blueprint-harness` es un workflow agéntico para la **fase de descubrimiento** del trabajo de software: el pensamiento que ocurre *antes* de que alguien decida escribir código. Convierte conversaciones sueltas en artefactos durables y estructurados:

- una idea se vuelve un **RFC** revisado con alternativas evaluadas,
- un reporte de bug se vuelve un **documento de triaje** con causa raíz respaldada por evidencia,
- una pregunta técnica se vuelve una respuesta — opcionalmente persistida como **audit**.

Lo que **no** es: una herramienta de implementación. Blueprint nunca escribe ni modifica código fuente, nunca corre tests, nunca toca el estado de git. Cuando decidís que algo efectivamente hay que construirlo, produce un seed de handoff para `sdd-lite` (o para el proceso que uses) y se detiene ahí.

Corre dentro de tu CLI de IA (Claude Code, o cualquier agente compatible con AGENTS.md). Un orquestador liviano conduce la sesión; workers chicos de solo lectura hacen la lectura pesada; todo lo durable vive en una carpeta local `bp-workspace/`.

## 2. Cuándo usarlo (y cuándo no)

### Usá `blueprint-harness` cuando

- Querés **formalizar una idea**: "quiero agregar caché a las consultas de productos — ayudame a escribirlo bien".
- Necesitás un **bug diagnosticado**, no arreglado: "los logins fallan con 500 desde el último deploy — ¿qué está pasando?".
- Tenés una **pregunta de código o de historia** que merece una respuesta cuidadosa: "¿qué cambió en el módulo de auth entre v2 y v3?".
- Querés una **decisión de arquitectura documentada** con alternativas y riesgos antes de comprometerte.

### NO lo actives para

- Implementar algo de verdad — ese es el trabajo de `sdd-lite` (o el tuyo).
- Preguntas triviales que el agente puede responder desde un archivo — el orquestador las responde inline sin ceremonia.
- Editar documentos que ya escribiste — blueprint genera sus propios artefactos desde evidencia, no es un editor de texto.

### La regla de routing de bugs

"Tengo un bug" es ambiguo entre los dos harnesses. La regla: **blueprint `bug-triage`** cuando querés entender o un diagnóstico documentado; **sdd-lite `bug-fix`** cuando querés que se arregle. Ante la duda, primero el triaje — su salida se transfiere limpio hacia un fix.

## 3. Conceptos clave

| Concepto | Significado |
|---|---|
| **Objetivo** | Una unidad de trabajo (un bug a triagear, una idea a refinar, una pregunta). Cada uno tiene su carpeta `bp-workspace/objectives/{slug}/` con su propio estado — así una consulta rápida nunca pisa un RFC abierto. |
| **Workspace** | `bp-workspace/` — local, por usuario, por máquina. No pensado para control de versiones (tu decisión, igualmente). Los documentos finales que quieras compartir los exportás manualmente. |
| **Digest** | El pequeño bloque de cabecera con el que abre todo artefacto (status, fecha, resumen de una línea). Es cómo el sistema retoma el trabajo sin releer todo. |
| **Rigor** | `light` / `standard` / `deep` en `config.yaml` — cuánta evidencia se exige y cuánto análisis se permite. |
| **Rúbrica de complejidad** | Un score de 3 preguntas (superficie, preguntas abiertas, concerns transversales) evaluado tras la primera ronda de entrevista. Define la profundidad de análisis y puede sugerir una entrevista profunda. |
| **Checkpoint** | Una pregunta estructurada que el orquestador te hace (¿aprobar este RFC? ¿persistir este audit?). Los checkpoints respondidos quedan registrados y nunca se re-preguntan. |
| **Worker** | Un sub-agente fresco que ejecuta una fase (mapeo, análisis, estrategia…) con un budget duro, y devuelve un resultado estructurado. Los workers de análisis no escriben nada. |
| **Envelope** | El paquete compacto de instrucciones que recibe un worker, y el resultado estructurado que devuelve. No los vas a ver salvo que los pidas. |

## 4. Setup (`bp-init`)

### Instalación

Desde tu CLI de IA, dentro del repo destino:

> Read `<package-path>/skills/bp-init/SKILL.md` and execute it, using `<package-path>` as the source package.

Qué hace:

1. Copia el motor a `.bp-harness/` (versionado vía un archivo `VERSION`).
2. Crea `bp-workspace/` — config, índice vacío, carpetas de artefactos, y tus propias copias editables de los templates.
3. Detecta tus AI setups (`CLAUDE.md`/`.claude/` → Claude Code; `AGENTS.md`/`.agents/` → agents) y **copia** las skills `bp-*` adentro.
4. Muestra el bloque de wrapper y, con tu `[y/n]`, lo inyecta en `CLAUDE.md`/`AGENTS.md` entre marcadores idempotentes.
5. **Ofrece** escribir el set de permisos read-only en la configuración de tu plataforma (p.ej. `.claude/settings.json`). Declinar está bien — el set queda documentado en el wrapper para aplicarlo a mano.
6. Si existe `./sdd-lite/`, reutiliza su identidad de proyecto en vez de preguntar.

Hace **como máximo 2 preguntas** (qué AI setups, solo si detecta varios; la oferta de permisos). **Nunca toca `.gitignore`** — si commiteás `.bp-harness/`, `bp-workspace/` o las copias de skills es enteramente tu decisión (recomendado: no).

### Update

Re-ejecutá la misma instrucción. Misma versión → reporta "up to date" y no cambia nada. Paquete más nuevo → ofrece un update que re-copia el motor y refresca las copias de skills y los bloques de wrapper. `bp-workspace/` se preserva siempre, incluido cualquier template que hayas editado.

### Desinstalación

Borrá `.bp-harness/`, `bp-workspace/`, las carpetas `bp-*` bajo `.claude/skills/` / `.agents/skills/`, y el bloque `<!-- bp-harness:start -->…<!-- bp-harness:end -->` de `CLAUDE.md`/`AGENTS.md`.

## 5. El archivo `config.yaml`

Vive en `bp-workspace/config.yaml`, validado contra `schemas/bp-config.schema.yaml`. Los campos que de verdad podés querer tocar:

- **`product`** — nombre, dominio de negocio, glosario opcional de términos del dominio que el harness debe usar consistentemente. Sembrado desde sdd-lite cuando está presente; si no, con defaults (editalo — mejor identidad significa mejores entrevistas).
- **`rigor_level`** — la perilla de profundidad:

| Nivel | Budget de análisis | Alternativas | Barra de causa raíz | Entrevista profunda |
|---|---|---|---|---|
| `light` | 1 pasada, ≤ 4 archivos | máx 2 | inferencias permitidas (marcadas) | nunca se sugiere |
| `standard` (default) | 1–2 pasadas, ≤ 8 archivos | 2–3 | inferencia marcada, fact preferido | sugerida con complejidad alta |
| `deep` | ≤ 3 pasadas, ≤ 15 archivos | 3 + descartadas | solo evidencia determinística afirma | sugerida proactivamente |

- **`conventions.chat_language`** — `es` o `en` para la conversación. Los artefactos persistidos son **siempre en inglés** (mantiene los handoffs compatibles y no es configurable).
- **`capabilities`** — lo que detectó `bp-init` (`rg`, `gh`, tooling de AST). Todo degrada con gracia cuando falta; `gh` solo se usa para metadata de PRs y nunca se asume.

## 6. Layout de archivos en runtime

```
bp-workspace/
├── config.yaml                 # configuración (arriba)
├── index.yaml                  # una línea por objetivo — el ancla de resume
├── objectives/{slug}/          # estado + notas de trabajo por objetivo
│   ├── state.yaml              #   fases, checkpoints, decisiones, punteros
│   ├── interview-notes.md      #   lo que le contaste (150–300 palabras)
│   ├── analysis.md             #   facts / inferences / unknowns (300–500)
│   └── alternatives.md         #   opciones + recomendación (300–500)
├── ideas/rfc-{slug}.md         # RFCs finales (400–800 palabras)
├── bugs/bug-{slug}.md          # reportes de bug finales (300–600)
├── audits/audit-{slug}.md      # consultas persistidas (200–400)
└── templates/                  # TUS templates de exportación editables (nunca se pisan)
```

Todo artefacto abre con un digest. Los finales llevan un estado de ciclo de vida en él:

```
draft  →  approved  →  handed-off
                   ↘  superseded
```

`draft → approved` ocurre solo cuando aprobás el artefacto en un checkpoint; `handed-off` solo tras un handoff exitoso. Los audits saltean `draft` — aceptar la oferta de persistir *es* la aprobación.

Los budgets de palabras son topes duros, no sugerencias: fuerzan al sistema a decir menos, mejor. Si un documento se siente corto, subí `rigor_level` en vez de esperar salida más larga.

## 7. Las 7 skills

Nunca las invocás directamente — el orquestador rutea hacia ellas. Saber qué hace cada una ayuda a leer los resúmenes de fase:

| Skill | Qué hace por vos | Escribe |
|---|---|---|
| `bp-init` | Instala y actualiza el harness | solo archivos de setup |
| `bp-context-mapper` | Encuentra *dónde* vive tu tema en el repo (≤ 6 archivos leídos) y revisa tus artefactos locales pasados por solapamientos | nada |
| `bp-analyzer` | Lee la lógica real y devuelve hallazgos marcados `fact` / `inference` / `unknown`, cada uno con prueba `file:line` | nada |
| `bp-diff-parser` | Responde preguntas de "qué cambió" desde la historia de git, congelada en SHAs exactos, sin volcar diffs | nada |
| `bp-strategist` | Convierte evidencia en 2–3 alternativas a nivel arquitectura con riesgos, esfuerzo y una recomendación | nada |
| `bp-doc-exporter` | Llena tu template con la evidencia acumulada y escribe el documento final; también flipea estados de digest tras tus aprobaciones | solo finales |
| `bp-handoff` | Escribe el seed del inbox de sdd-lite desde un artefacto aprobado | solo el seed |

Las reglas de honestidad son el punto: una afirmación sin prueba se degrada a inferencia; evidencia insuficiente se vuelve `unknown`, nunca una adivinanza; las opiniones de estilo quedan fuera de alcance.

## 8. Los tres flujos

Al inicio de una sesión el orquestador pregunta una vez: **`interactive`** (pausa tras cada fase esperando tu OK — default) o **`auto`** (encadena fases, deteniéndose solo en decisiones reales). Los checkpoints requeridos — aprobar un artefacto, el gate de handoff, resolver contexto faltante — nunca se saltean en ningún modo.

### F1 — Triaje de bugs

1. **Entrevista** (en el chat, corta): síntoma, comportamiento esperado, área sospechada, reproducibilidad. Máximo 2 rondas; si ya diste los datos, saltea hacia adelante.
2. **Mapeo**: un worker localiza la superficie afectada.
3. **Análisis**: un worker valida hipótesis contra el código y los logs reales (*archivos* de log o texto que pegues — nada se ejecuta).
4. **Estrategia**: alternativas de resolución con impacto.
5. **Export opcional**: con tu aprobación, `bugs/bug-{slug}.md` — y opcionalmente un handoff si querés que se arregle.

### F2 — Refinamiento de requerimientos

Mismo esqueleto, otras preguntas: objetivo de negocio, flujos afectados, límites de alcance, restricciones. El mapeo también contrasta tus **RFCs locales pasados** para que una propuesta nueva no contradiga una decisión vieja. Termina en `ideas/rfc-{slug}.md` tras tu `artifact_approval`, y opcionalmente el gate de handoff.

### F3 — Consulta de código

El camino liviano. Las preguntas triviales (≤ 3 archivos, sin historia) se responden inline sin workers. Las preguntas de historia pasan primero por el diff-parser (SHAs congelados). Tras la respuesta recibís una oferta **única** de persistirla como audit — decliná y no vuelve a preguntar para ese objetivo.

### La entrevista profunda

Cuando la rúbrica de complejidad puntúa tu tema como complejo (o la pedís), el orquestador sugiere una **sesión paralela dedicada** para una entrevista más larga. Esa sesión formaliza sus conclusiones en el estado del objetivo y cierra; tu sesión principal retoma desde el estado registrado, nunca desde el otro chat. Útil cuando la idea necesita una hora de ida y vuelta que ahogaría la sesión de trabajo.

### Retomar

Todo se retoma desde `bp-workspace/` — `index.yaml`, después el `state.yaml` del objetivo, después los digests. Matá una sesión a mitad de flujo, abrí una nueva, decí "continuá con {slug}" — retoma en el primer ítem sin resolver. La memoria del chat nunca es necesaria.

## 9. Cómo se garantiza el read-only

Tres capas independientes:

1. **Permisos de plataforma** (la más fuerte): el set que ofrece `bp-init` — deny de escrituras fuera de `bp-workspace/`, el inbox de sdd-lite y los paths de setup del propio harness; allow solo de `git log/show/diff/status/blame`; deny de todo comando git que cambie estado. Aplicalo y la garantía es mecánica.
2. **Boundary del envelope**: todo worker recibe la instrucción de solo lectura (o solo-paths-propios) y la prohibición de spawnear sub-agentes.
3. **Verificación post-worker**: el orquestador chequea qué reporta haber escrito cada worker. Un worker de análisis que escribió *cualquier cosa* se trata como incidente — la sesión se detiene y su salida se desconfía.

**No hay mutaciones de git, sin excepciones** — blueprint nunca stagea, commitea, taggea ni pushea. Si lo ves intentar una, eso es un bug: frená y reportalo.

## 10. Ejemplos de uso

### Ejemplo 1 — Diagnosticar un bug de producción

> **Vos:** El login con Google devuelve 500 desde el deploy del viernes. Ayudame a entender por qué — no arregles nada todavía.
> **Agente:** *(hace 2–3 preguntas de entrevista: endpoint exacto, comportamiento esperado, logs disponibles)*
> **Vos:** *(pegás el stack trace)*
> **Agente:** *(mapea la superficie de auth, analiza)* Hipótesis de causa raíz: payload nulo de `verifyIdToken` desreferenciado sin guard en `google.strategy.ts:54` (fact, confirmado por log); el deploy eliminó la opción `audience` (fact); la vinculación es inferencial. Dos opciones de resolución… ¿Exporto el reporte?
> **Vos:** sí
> **Agente:** *(escribe `bugs/bug-google-login-500.md` como draft → aprobás → approved)*

### Ejemplo 2 — RFC con handoff

> **Vos:** Quiero formalizar agregar una capa de caché a las consultas de productos.
> **Agente:** *(entrevista: objetivo, expectativas de escala, alcance)* → *(mapea el repo + encuentra tu viejo `rfc-read-replicas.md`, marca un solapamiento)* → *(presenta alternativas A/B con el trade-off)*
> **Vos:** A. Aprobalo y mandalo a desarrollo.
> **Agente:** *(exporta `ideas/rfc-query-cache-layer.md`, aprobás, gate de handoff)* Seed escrito en `sdd-lite/openspec/inbox/query-cache-layer.md`. Apuntá sdd-lite ahí para arrancar el change.

### Ejemplo 3 — Pregunta de historia, conservada

> **Vos:** ¿Qué cambió en las skills de review en los últimos 10 commits?
> **Agente:** *(diff-parser, congelado en `5f8d83a`)* Resumen: se agregó un subsistema de review completo en un commit… ¿Querés persistir esto como audit?
> **Vos:** sí → `audits/audit-review-skills-evolution.md` (nace approved).

### Ejemplo 4 — Retomar tras un corte

> **Vos (sesión nueva):** Continuá con query-cache-layer.
> **Agente:** *(lee índice + estado)* El RFC está `approved`, el gate de handoff sin resolver. Estabas decidiendo si mandarlo a desarrollo. ¿Sigo?

## 11. Qué NO hacer

- **No le pidas que arregle cosas.** "Arreglá este bug" es de sdd-lite o tuyo; blueprint va a ofrecer la válvula de escalación en vez de obedecer.
- **No pelees contra los budgets.** Si el análisis paró en 8 archivos, eso es el rigor `standard` funcionando. Subí el rigor, no le pidas que "siga leyendo".
- **No esperes memoria compartida.** El workspace es local a tu máquina. El blueprint de un colega no sabe nada del tuyo; compartí los documentos finales exportándolos donde tu equipo guarda docs.
- **No edites `state.yaml` ni `index.yaml` a mano.** El orquestador es su único escritor; los edits manuales rompen el resume. Tu superficie editable es `bp-workspace/templates/` y `config.yaml`.
- **No trates inferencias como hechos.** Las etiquetas existen para distinguirlos; una corrida con rigor `deep` se va a negar a afirmar lo que no puede probar.
- **No saltees la entrevista tirando una spec.** Podés — el smart skip la absorbe — pero respondé las repreguntas: existen para atrapar lo que la spec no dijo.

## 12. Handoff hacia sdd-lite

El único punto de acople entre los dos harnesses, y es deliberadamente pasivo:

1. Aprobás un RFC o reporte de bug (`artifact_approval` → status `approved`).
2. Confirmás el **gate de handoff**.
3. `bp-handoff` escribe un seed autocontenido — problema, boceto de alcance, señal de viabilidad, preguntas abiertas — en `./sdd-lite/openspec/inbox/{slug}.md`, y el artefacto fuente pasa a `handed-off`.
4. **El consumo es manual y tuyo**: decile a sdd-lite que arranque un change desde ese archivo del inbox. Blueprint nunca modifica sdd-lite — sin archivos de estado, sin escrituras en `changes/`, sin patches a sus skills.

Si sdd-lite no está instalado en el repo, el handoff se bloquea con un mensaje claro y no escribe nada. La transición es unidireccional: una vez que arranca el desarrollo, los cambios de alcance ocurren en los artefactos de sdd-lite, no re-editando el RFC (abrí un objetivo nuevo si el descubrimiento genuinamente se reabre).
