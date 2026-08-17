# Guía de uso de sdd-lite-evals

## Qué evalúa

`sdd-lite-evals` revisa la copia de sdd-lite que ya está configurada dentro de un
proyecto. No toma automáticamente el paquete hermano `sdd-lite` ni ejecuta
`sddl-init`. Esto permite validar exactamente lo que Codex, Claude u OpenCode ven
en ese proyecto.

Los datos de un proyecto viven en:

```text
sdd-lite-evals/workspaces/<proyecto>/
```

El directorio está ignorado por Git. Los proyectos y tareas no forman parte del
paquete genérico.

## Primera configuración

Abrir el CLI en el proyecto evaluado y pedirle que lea explícitamente:

```text
/ruta/a/sdd-lite-evals/skills/sddl-eval-init/SKILL.md
```

La skill detecta antes de preguntar:

- raíz del proyecto
- proveedor activo
- Git y working copy
- instalación y bootstrap de sdd-lite
- wrappers y skills instaladas
- idioma de trabajo

Después pregunta únicamente lo que falte y crea el workspace. Si se usarán tres
CLIs, ejecutar el init una vez desde cada uno. El mismo workspace se actualiza con
el nuevo provider y no reemplaza casos o campañas existentes.

La instalación de las skills de evaluación puede ser por symlink o copia. No se
inyecta ningún wrapper adicional en `CLAUDE.md` o `AGENTS.md`.

## Nivel 1: siempre primero

Invocar `sddl-eval-level-1` o ejecutar:

```bash
python3 scripts/sddl_eval.py level1 --workspace slow
```

No usa modelos. Comprueba estructura, schemas, runtime, lazy modules, ruta
principal, skills, templates, wrapper versionado, worker bypass e instalación por
provider.

- `PASS`: se puede continuar.
- `WARN`: revisar si la advertencia afecta el caso elegido.
- `FAIL`: corregir antes de ejecutar pruebas con modelos.
- `BLOCKED`: sdd-lite o el fixture no están utilizables.

## Nivel 2: comportamiento por CLI

Primero ejecutar el preview sin `--execute`:

```bash
python3 scripts/sddl_eval.py level2 \
  --workspace slow \
  --case main-flow-example \
  --provider codex \
  --profile smoke
```

El preview informa cuántas sesiones hijas y qué probes se ejecutarán. Después de
aceptar el costo, repetir agregando `--execute`.

`smoke` cubre activación explícita, near-miss, oferta para trabajo sustancial,
worker bypass, approval gate y carga del hot runtime. `full` agrega los probes
adicionales del caso, incluyendo bootstrap incompleto y routing desde estado.

Cada probe usa un fixture y un proceso nuevo. Los eventos crudos están disponibles,
pero el reporte humano muestra assertions y evidencia normalizada. El CLI activo
completa `analysis-template.yaml` con riesgos específicos de su plataforma y lo
adjunta con:

```bash
python3 scripts/sddl_eval.py analyze \
  --workspace slow --run-id <run-id> --analysis-file <analysis.yaml>
```

Esto regenera el reporte y hace que las conclusiones semánticas participen del
historial y las comparaciones.

## Nivel 3: flujo principal

Preview:

```bash
python3 scripts/sddl_eval.py level3 \
  --workspace slow \
  --case main-flow-example \
  --provider codex
```

Después de confirmar, agregar `--execute`. La primera sesión corre sólo proposal,
spec, design y plan. Si no se modificó código y los artefactos son válidos, el run
queda `awaiting_approval`.

La continuación requiere aprobación humana posterior al plan:

```bash
python3 scripts/sddl_eval.py level3 \
  --workspace slow \
  --resume-run <run-id> \
  --approve-stage <stage>
```

Ese comando también es preview. Agregar `--execute` sólo después de confirmar el
stage mostrado. Cada continuación abre un proceso limpio y recupera el cambio desde
los archivos persistidos. Repetir el ciclo si aparece otro gate.

El flujo termina en QA final. 4R, Judgment Day, delivery y archive quedan fuera de
la campaña estándar.

## Proyectos, casos y campañas

`project.yaml` describe dónde está el proyecto y qué providers fueron preparados.
Para cada provider distingue `skill_dir` —donde se instalan las skills del
evaluador— de `sdd_skill_dirs`, las ubicaciones completas de skills de sdd-lite que
las sesiones hijas deben poder descubrir.

Un caso define:

- tarea
- estado inicial requerido
- artefactos y lifecycle esperados
- protocolos opcionales prohibidos
- probes y assertions
- comandos de calidad

Una campaña agrupa casos y providers. El modelo no se fija: se usa el default del
CLI y se registra el valor observado. Por esa razón un cambio de modelo aparece
como confounder en las comparaciones.

Para modificar el caso de ejemplo, copiarlo con otro id dentro de `cases/`. No
editar los templates genéricos para una necesidad exclusiva de `slow`.

## Reportes y baseline

Reconstruir un reporte:

```bash
python3 scripts/sddl_eval.py report --workspace slow --campaign level2
```

Comparar dos runs explícitos:

```bash
python3 scripts/sddl_eval.py report \
  --workspace slow \
  --campaign runtime-refactor \
  --candidate-run <candidate> \
  --baseline-run <baseline>
```

El comparador nunca selecciona el último run automáticamente. Informa diferencias
de provider, caso, proyecto y modelo, además de findings nuevos, persistentes,
resueltos o agravados.

## Política de costo

- Nivel 1 no usa modelos.
- Nivel 2 usa una sesión por probe.
- Nivel 3 usa una sesión por checkpoint aprobado.
- El default es una repetición.
- No hay límite automático de tokens o dinero.
- Los comandos con costo son dry-run salvo que se agregue `--execute`.

Si una campaña parece inestable, repetir sólo el caso sospechoso. No ejecutar dos o
tres repeticiones de toda la suite por defecto.
