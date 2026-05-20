# sdd-lite — Guia rapida

Workflow liviano para cambios acotados (features, bugs, refactors) con trazabilidad, aprobaciones por etapa y estado persistido en archivos.

---

## Que es y para que sirve

sdd-lite estructura el trabajo de un agente AI en etapas: propuesta, especificacion, diseno, plan, ejecucion y QA. Cada etapa genera un artefacto persistido (markdown/yaml) y requiere aprobacion antes de tocar codigo. Todo vive en `./sdd-lite/` — no depende de la memoria del chat.

---

## Inicio rapido

### 1. Inicializar el proyecto

> "Install sdd-lite in this repo and configure it for Claude Code"

Esto ejecuta `sddl-init`: escanea el proyecto, detecta stack y AI, instala skills y genera los archivos base en `./sdd-lite/`.

### 2. Usar sdd-lite en un cambio

Pedirlo explicitamente. Palabras clave: `"con sdd"`, `"use sdd-lite"`, `"sddl"`, `"hacerlo con sdd"`.

No se activa automaticamente para preguntas simples o fixes triviales.

---

## Flujo estandar

```
sddl-init (bootstrap, una sola vez)
  -> sddl-proposal   (consolida la idea, exploracion liviana opcional)
  -> sddl-spec       (formaliza scope y criterios de aceptacion)
  -> sddl-design     (diseno tecnico: arquitectura y areas afectadas)
  -> sddl-plan       (plan de ejecucion por etapas)
  -> sddl-executor   (ejecuta UNA etapa aprobada)
  -> sddl-qa-review  (revision por etapa o final)
```

Cada etapa necesita tu aprobacion antes de avanzar. El executor nunca avanza solo a la siguiente etapa.

---

## El orquestador

El orquestador es un coordinador liviano. No implementa, no ejecuta tests, no modifica codigo. Solo lee el estado minimo necesario, decide la ruta y delega el trabajo a la skill correcta.

**Que hace:**
- Verifica que el bootstrap este listo antes de arrancar
- Evalua complejidad y elige la ruta (flujo normal, macro-plan, o escalar)
- Arma el handoff compacto para cada skill delegada
- Mantiene `state.yaml` actualizado para poder retomar en cualquier momento

**Que se le puede pedir:**
- Iniciar un cambio nuevo: `"Con sdd-lite, agregar validacion al formulario de login"`
- Retomar un cambio existente: `"Retoma el cambio feat-login-validation"`
- Solo planificar: `"Con sdd-lite y objetivo planner, planifica la separacion de modulos"`
- Investigar antes de actuar: si detecta incognitas, delega a `sddl-deep-explorer` automaticamente
- Avanzar a la siguiente etapa: `"Apruebo, continua con la siguiente etapa"`
- Revisar o cerrar: `"Hace la QA final del cambio"`

**Que NO hace:**
- No edita archivos del repo directamente
- No hace commits, stash ni ninguna operacion git
- No avanza sin tu aprobacion en etapas que tocan codigo
- No depende de lo que dijiste antes en el chat — siempre lee de `state.yaml` y los artefactos

---

## Ejemplos de uso

**Agregar un endpoint:**
> "Con sdd-lite, agregar un endpoint GET /users/me que devuelva el usuario autenticado"

Resultado: propuesta -> spec -> diseno -> plan con etapas (ej: S1 controller, S2 tests) -> ejecucion etapa por etapa -> QA final.

**Bug con causa incierta:**
> "Con sddl: el login a veces falla con 500, no se por que"

Resultado: primero `sddl-deep-explorer` investiga (read-only) -> con la evidencia continua el flujo normal.

**Solo planificar, sin ejecutar:**
> "Con sdd-lite y objetivo planner, planifica migrar logs a JSON estructurado"

Resultado: propuesta -> spec -> diseno -> plan -> se detiene sin ejecutar.

**Retomar un cambio:**
> "Retoma el cambio feat-users-me"

Lee `state.yaml` y retoma desde donde quedo.

---

## Las 8 skills

| Skill | Que hace |
|---|---|
| `sddl-init` | Bootstrap: escanea proyecto, configura AI, genera archivos base |
| `sddl-proposal` | Consolida la idea del cambio con exploracion liviana opcional |
| `sddl-spec` | Formaliza scope, comportamiento esperado y criterios de aceptacion |
| `sddl-design` | Diseno tecnico: arquitectura, patrones y areas afectadas |
| `sddl-plan` | Plan de ejecucion por etapas con dependencias y validacion |
| `sddl-executor` | Ejecuta UNA etapa aprobada. No hace commits ni modifica git |
| `sddl-deep-explorer` | Analisis read-only para resolver incognitas antes de disenar |
| `sddl-qa-review` | Revision por etapa (`stage`) o cierre final (`final`) |

---

## Recomendaciones

- **No saltear etapas.** No ir directo al executor sin propuesta, spec, diseno y plan.
- **Aprobar etapa por etapa.** Revisar lo que propone antes de dejar que ejecute.
- **Retomar siempre desde el orquestador.** El resume se reconstruye de `state.yaml`, no del chat.
- **Escalar si crece.** Si el cambio se vuelve demasiado grande, no forzarlo en sdd-lite.
- **Los artefactos se persisten en ingles.** El chat puede ser en espanol.

---

## Archivos generados

```
./sdd-lite/
  project-context.md          # contexto del repo (stack, comandos, convenciones)
  skill-catalog.md            # registro de standards
  openspec/
    config.yaml               # configuracion del proyecto
    changes/{nombre}/
      state.yaml              # estado actual del cambio
      proposal.md             # problema y factibilidad
      spec.md                 # scope y criterios de aceptacion
      design.md               # diseno tecnico
      plan.md                 # plan de ejecucion por etapas
      execution-log.md        # registro de ejecucion
      qa-report.md            # hallazgos y cierre
```

---

## Seccion extra: preferencias de usuario

Archivo opcional `./sdd-lite/user-prefs.yaml`. Se configura en `sddl-init` o editando el archivo directo.

**Presets disponibles:**

| Preset | Comportamiento |
|---|---|
| `autonomous` | Menos checkpoints, ejecuta acciones reversibles sin preguntar |
| `balanced` (default) | Pregunta en cambios materiales, validacion proporcional |
| `cautious` | Checkpoints frecuentes, explicaciones detalladas, validacion completa |

Knobs configurables: idioma del chat, profundidad de explicaciones, frecuencia de validacion, nivel de autonomia. Ver `schemas/user-prefs.schema.yaml` para el detalle completo.
