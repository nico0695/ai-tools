# Pre-planning — Harness de análisis de logs con IA

Relevamiento completo para un repo que permita a QA, Operaciones y Desarrollo analizar logs de
players de digital signage con asistencia de IA, de forma auditable y acumulativa.

## Documentos

| # | Documento | Qué responde |
|---|---|---|
| 0 | [`00-DISCOVERY.md`](00-DISCOVERY.md) | Dónde estamos, qué dice la evidencia, qué restringe, qué falta decidir |
| 1 | [`01-PRD.md`](01-PRD.md) | Qué se construye: visión, no-objetivos, journeys, RF/RNF, criterios de aceptación, fases |
| 2 | [`02-ARCHITECTURE.md`](02-ARCHITECTURE.md) | Cómo: estructura de repo, modelo de caso, 12 ADRs con alternativas |
| 3 | [`03-SKILLS-AGENTS-SCRIPTS.md`](03-SKILLS-AGENTS-SCRIPTS.md) | Con qué piezas: catálogo y contrato de cada skill, subagente, script y doc |
| 4 | [`04-RISKS-AND-BACKLOG.md`](04-RISKS-AND-BACKLOG.md) | Qué puede salir mal y en qué orden construir |
| 5 | [`05-SOURCES.md`](05-SOURCES.md) | De dónde sale cada afirmación |

## Las 7 ideas que sostienen el diseño

1. **El agente consulta los logs, no los recibe.** Es la decisión de mayor impacto medido:
   3.88% → 11.34% de accuracy en RCA (OpenRCA). El agente nunca lee un archivo completo.
2. **Detección por ausencia como primitiva de primera clase.** Tu caso de referencia se diagnostica
   por lo que *no* está en el log. Ninguna herramienta del estado del arte hace esto. Es el
   diferencial técnico del harness.
3. **Estado derivado, nunca declarado.** El agente deduce dónde está parado de qué archivos
   existen, no de un campo que alguien tiene que mantener a mano.
4. **Histórico append-only.** `attempts.ndjson` no se edita: el agente sólo puede agregar líneas.
   Elimina por construcción la clase de bug donde el modelo reescribe lo que ya se probó.
5. **`history/` privado y gitignorado · `knowledge/` público y commiteado.** La promoción de uno al
   otro es explícita y pasa por PR. Resuelve la tensión entre privacidad y conocimiento compartido.
6. **Identificadores en inglés, prosa en el idioma del usuario.** Carpetas, archivos, comandos,
   claves, estados y slugs son siempre inglés porque son contrato de máquina. Los informes, las
   preguntas y la documentación salen en español por defecto, y el protocolo arranca resolviendo
   el idioma (ADR-011/012).
7. **Cita verificada por script, no por modelo.** Toda afirmación lleva `archivo:línea`, y un script
   determinístico confirma que exista. Sin eso, el informe no se emite.

## Posicionamiento (importante)

`logharness` **no dice qué pasó**. Reduce el espacio de búsqueda, propone hipótesis falsables,
busca evidencia en contra y deja un expediente auditable. La evidencia disponible —11.34% de
accuracy máxima en RCA end-to-end con LLM— hace que cualquier otra promesa sea deshonesta y mala
para la adopción.

## Alcance recomendado

**MVP (2-3 semanas)**: `loga` con `ingest`/`summarize`/`grep`/`window`/`absence`/`status`/
`verify-citations`, 5 skills, 2 subagentes, 1 playbook portado del que ya funciona, y el modelo de
caso mínimo (`case.yaml` + `TLDR.md` + `attempts.ndjson`).

**Criterio de éxito del MVP**: reproducir, con el harness, el veredicto que hoy se obtiene a mano
con la skill `menuboard-fetch-diag` sobre los mismos 10 logs. Si no lo reproduce, no sirve.

## Convención del repo

Identificadores en **inglés** (carpetas, archivos, comandos, flags, claves YAML/JSON, estados,
slugs, nombres de skills y subagentes). Prosa en **español**, con detección de idioma al inicio de
la conversación. Excerpts de log **verbatim, nunca traducidos**. Detalle en `02` ADR-011 y ADR-012.

## Diagramas

Los 8 diagramas de estos documentos están en bloques ```` ```mermaid ````. Renderizan nativamente
en **GitHub, GitLab y Claude**; en **VS Code** hace falta la extensión *Markdown Preview Mermaid
Support*. Para validarlos localmente sin depender del renderer:

```bash
npx -y @mermaid-js/mermaid-cli -i docs/02-ARCHITECTURE.md -o /tmp/out.md
```

Cada diagrama va seguido de un bloque **"Cómo leer el diagrama"** que dice cuál es la afirmación
que sostiene. Si el diagrama y ese párrafo no coinciden, gana el párrafo: el diagrama está mal.

## Próximos pasos

1. Validar los 6 supuestos (`00` §6) y responder las 6 preguntas abiertas (`00` §7).
2. Confirmar o desviar los ADRs (`02` §4).
3. Inventariar con QA/Ops/Dev los patrones de falla ya reconocidos — define el roadmap de playbooks.
4. Arrancar Fase 0.
