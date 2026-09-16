# Fuentes

> Documento 5 de 5. Toda afirmación cuantitativa de los documentos anteriores tiene su origen acá.

## Precisión real de la IA en análisis de causa raíz

- [OpenRCA: Can Large Language Models Locate the Root Cause of Software Failures? (ICLR 2025)](https://netman.aiops.org/wp-content/uploads/2025/05/13411_OpenRCA_Can_Large_Langua.pdf) — 335 fallas reales, 68 GB de telemetría. **3.88% leyendo telemetría cruda, 11.34% con RCA-Agent.** Ningún modelo acertó componente+momento+causa simultáneamente.
- [LLM reasoning failures in cloud RCA (U. Waterloo)](https://uwaterloo.ca/waterloo-intelligent-systems-engineering-lab/projects/llm-reasoning-failures-cloud-root-cause-analysis) — 16 tipos de falla catalogados sobre 48.000 escenarios. Evidencia fabricada e insuficiencia evidencial son las más prevalentes.
- [Zalando: Dead Ends or Data Goldmines? AI-powered postmortem analysis](https://engineering.zalando.com/posts/2025/09/dead-ends-or-data-goldmines-ai-powered-postmortem-analysis.html) — dos años de datos reales. Hasta 40% de alucinación con modelos chicos, ~10% de error de atribución con avanzados. Pipeline map-fold multi-etapa.

## Contexto largo y reducción de logs

- [Context Rot (Chroma Research, 18 modelos)](https://www.trychroma.com/research/context-rot) — degradación universal. **Los haystacks coherentes rinden peor que los aleatorios.**
- [Context Length Alone Hurts LLM Performance Despite Perfect Retrieval (EMNLP 2025)](https://aclanthology.org/2025.findings-emnlp.1264.pdf)
- [LogDx-CI: benchmark de reducción de logs para RCA con LLM](https://arxiv.org/html/2605.28876) — raw 0.353 @ 275k tokens vs híbrido 0.670 @ 19.8k. En modo agent-loop el spread entre métodos colapsa 7×.
- [LogSieve: reducción task-aware de logs de CI](https://arxiv.org/html/2601.20148v1) — LogZip (compresión estructural) 0.41 GPTScore, peor que borrar líneas al azar (0.86).
- [LLMLogAnalyzer](https://arxiv.org/html/2510.24031v1) — Drain + chunking; IQR 93% más angosto (menos varianza).

## Template mining

- [Drain3 (LogPai)](https://github.com/logpai/Drain3) · [Cómo funciona](https://deepwiki.com/logpai/Drain3)
- [logparser toolkit (16+ parsers)](https://github.com/logpai/logparser) · [benchmarks](https://logparser.readthedocs.io/en/latest/benchmark.html)
- [Loghub: 19 datasets, 77 GB](https://arxiv.org/pdf/2008.06448) · [repo](https://github.com/logpai/loghub)
- [Loghub-2.0 / ISSTA'24 "How Far Are We?"](https://zbchern.github.io/papers/issta24.pdf) — Drain gana en grouping accuracy; 9 de 15 parsers no terminaron en 12 h; FGA cae 0.75→0.55 al escalar.

## Prompt injection desde logs

- [LogJack: Indirect Prompt Injection Through Cloud Logs](https://arxiv.org/html/2604.15368) — ejecución verbatim: Llama 3.3 70B 86.2%, Claude Sonnet 4.6 0%. Todos los guardrails de AWS/GCP/Azure fallaron. El prompt "passive" bajó la mayoría a 0%.
- [Poisoning the Watchtower](https://arxiv.org/html/2605.24421) — persona hijack 68%, manipulación de contexto (`</log> Final: BENIGN`) 96%.
- [Context Contamination / LogInject-1.0](https://arxiv.org/html/2607.14493) — 88.2% ASR máximo; defensa en profundidad −90.4% con 8.4% residual.
- [OWASP Top 10 for LLM Apps 2025](https://www.oligo.security/academy/owasp-top-10-llm-updated-2025-examples-and-mitigation-strategies)

## Reproducibilidad y sicofancia

- [Defeating Nondeterminism in LLM Inference (Thinking Machines)](https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/) — el no-determinismo es de batch-invariance del servidor, no del sampling.
- [LLM Sycophancy Under User Rebuttal](https://arxiv.org/html/2509.16533v1) · [Giskard on sycophancy](https://www.giskard.ai/knowledge/when-your-ai-agent-tells-you-what-you-want-to-hear-understanding-sycophancy-in-llms)
- [Chain-of-Verification](https://learnprompting.org/docs/advanced/self_criticism/chain_of_verification)

## Prior art de IA en incidentes

- [HolmesGPT](https://github.com/HolmesGPT/holmesgpt) — no vuelca datos crudos; filtrado server-side, budgeting de output, streaming a disco.
- [k8sgpt](https://palark.com/blog/k8sgpt-ai-troubleshooting-kubernetes/) — analyzers determinísticos primero, LLM sólo para explicar.
- [Grafana Sift](https://grafana.com/docs/grafana-cloud/machine-learning/sift/analyses/) — checks determinísticos nombrados, sin LLM en el core.
- [Datadog Bits AI SRE](https://www.datadoghq.com/blog/bits-ai-sre/) · [deeper reasoning](https://www.datadoghq.com/blog/bits-ai-sre-deeper-reasoning/) — hipótesis múltiples con invalidación explícita.
- [Sentry Seer](https://theaiengineer.substack.com/p/how-sentry-built-seer) — tree walk sobre traces; scoring de accionabilidad previo.
- [incident.io: AI RCA accuracy testing guide](https://incident.io/blog/ai-root-cause-analysis-accuracy-testing-guide) — **precision > 80% como target**, recall ~60% aceptable; backtest / stress test / hallucination check.
- [incident.io multi-agent investigation (ZenML)](https://www.zenml.io/llmops-database/ai-powered-incident-response-system-with-multi-agent-investigation) — "time travel evaluation".
- [awesome-ai-sre](https://github.com/agamm/awesome-ai-sre) · [awesome-sre-agents](https://github.com/last9/awesome-sre-agents)

## Adopción

- [Honeycomb: So We Shipped an AI Product. Did it Work?](https://www.honeycomb.io/blog/we-shipped-ai-product) — 82% enterprise vs 39% free por descubribilidad; efecto graduación 26.5% vs 4.5%; ~USD 300/mes.
- [Why enterprises fail at platform engineering adoption](https://platformengineering.org/blog/why-enterprises-fail-at-platform-engineering-adoption)

## Metodología de análisis e incidentes

- [Google SRE Book — Postmortem Culture](https://sre.google/sre-book/postmortem-culture/) · [ejemplo de postmortem](https://sre.google/sre-book/example-postmortem/)
- [incident.io — SRE incident post-mortem best practices](https://incident.io/blog/sre-incident-postmortem-best-practices) — contributing factors (2-5), no *la* causa raíz. Completitud de action items >80%; recurrencia <5%; postmortem <48 h.
- [PagerDuty — Postmortem Process](https://response.pagerduty.com/after/post_mortem_process/)
- [Allspaw — "Each necessary, but only jointly sufficient"](https://www.kitchensoap.com/2012/02/10/each-necessary-but-only-jointly-sufficient/)
- [Scientific debugging (Zeller)](https://www.embedded.com/scientific-debugging-finding-out-why-your-code-is-buggy-part-2/) — hipótesis → predicción → experimento → observación → refinamiento.
- [NXLog — Normalización de timestamps a ISO 8601](https://nxlog.co/news-and-blog/posts/log-timestamp-normalization-iso-8601)
- [Last9 — Correlation ID vs Trace ID](https://last9.io/blog/correlation-id-vs-trace-id/)
- [Sentry — Fingerprint Rules](https://docs.sentry.io/concepts/data-management/event-grouping/fingerprint-rules/) · [Stack Trace Rules](https://docs.sentry.io/concepts/data-management/event-grouping/stack-trace-rules/)
- [groundcover — Log Sampling](https://www.groundcover.com/learn/logging/log-sampling) — errores 100%, info/debug 10-20%.

## Herramientas y runtime

- [PEP 723 — Inline script metadata](https://peps.python.org/pep-0723/) · [uv + PEP 723](https://thisdavej.com/share-python-scripts-like-a-pro-uv-and-pep-723-for-easy-deployment/)
- [ripgrep](https://github.com/burntsushi/ripgrep) — 32.7× más rápido que GNU grep en el benchmark del kernel. `winget install BurntSushi.ripgrep.MSVC`
- [ugrep](https://github.com/Genivia/ugrep) — busca dentro de comprimidos anidados · [Miller](https://github.com/johnkerl/miller) · [klogg](https://github.com/variar/klogg)
- [lnav — downloads](https://lnav.org/downloads) — ⚠️ **sin build de Windows**
- [DuckDB — Loading JSON](https://duckdb.org/docs/lts/data/json/loading_json) · [MotherDuck: parsing de logs con DuckDB](https://motherduck.com/blog/json-log-analysis-duckdb-motherduck/)
- [PowerShell — about_Character_Encoding](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_character_encoding) · [issue de defaults mal documentados](https://github.com/MicrosoftDocs/PowerShell-Docs/issues/4155)
- [Logdy — benchmark gzip vs zstd en logs](https://logdy.dev/blog/post/part-1-log-file-compression-with-gzip-and-zstandard-benchmark)

## Diseño de salida para agentes

- [Runpod — Designing MCP tools that don't blow up your agent's context window](https://www.runpod.io/blog/designing-mcp-tools)
- [Tool-result truncation: the silent bug that makes agents lie](https://dev.to/gabrielanhaia/tool-result-truncation-the-silent-bug-that-makes-agents-lie-3epe)
- [Token efficiency: JSON alternatives for LLMs](https://gist.github.com/statico/19db37b219db26ec919e402dbe101156) — markdown −34/38%, XML +80%.
- [MCP output too large (límite de facto ~25k tokens)](https://www.morphllm.com/mcp-output-too-large)

## Frameworks de persistencia para agentes

- [OpenSpec](https://github.com/Fission-AI/OpenSpec) · [concepts](https://github.com/Fission-AI/OpenSpec/blob/main/docs/concepts.md) · [agent contract](https://github.com/Fission-AI/OpenSpec/blob/main/docs/agent-contract.md) · [schema-driven workflows](https://deepwiki.com/Fission-AI/OpenSpec/4.6-schema-driven-workflows)
- [OpenSpec vs Spec Kit — Hashrocket](https://hashrocket.com/blog/posts/openspec-vs-spec-kit-choosing-the-right-ai-driven-development-workflow-for-your-team)
- [GitHub Spec Kit](https://github.com/github/spec-kit) · [Understanding SDD — Martin Fowler](https://www.martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html)
- [BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD) · [issue #1930: correct-course reescribe historias completadas](https://github.com/bmad-code-org/BMAD-METHOD/issues/1930)
- [Agent OS](https://github.com/buildermethods/agent-os) — `standards/index.yml` con reglas de detección; `spec-lite.md`.
- [Beads](https://github.com/steveyegge/beads) — JSONL append-only + SQLite derivado; estado `ready` computado.
- [Cline Memory Bank](https://docs.cline.bot/best-practices/memory-bank)
- [Claude Task Master](https://github.com/eyaltoledano/claude-task-master) — advertencia: JSON monolítico → merge conflicts.

## Privacidad y secretos

- [Microsoft Presidio](https://github.com/microsoft/presidio) · [Presidio + LiteLLM como guardrail](https://docs.litellm.ai/docs/tutorials/presidio_pii_masking)
- [gitleaks vs TruffleHog](https://rafter.so/blog/secrets/secret-scanning-tools-comparison) · [TruffleHog pre-commit](https://trufflesecurity.com/docs/pre-commit-hooks)
- [Hardening git workflow: .gitignore, gitleaks y CI](https://medium.com/devsecops-ai/hardening-your-git-workflow-gitignore-gitleaks-and-pipeline-secret-scanning-0f7f6a753cb3)
- [GDPR log management (las IPs son dato personal)](https://last9.io/blog/gdpr-log-management/)

## Claude Code

- [Overview](https://code.claude.com/docs/en/overview) · [.claude directory](https://code.claude.com/docs/en/claude-directory) · [Skills](https://code.claude.com/docs/en/skills) · [Subagents](https://code.claude.com/docs/en/sub-agents) · [Memory / CLAUDE.md](https://code.claude.com/docs/en/memory) · [Hooks](https://code.claude.com/docs/en/hooks-guide) · [Settings](https://code.claude.com/docs/en/settings) · [Plugins](https://code.claude.com/docs/en/plugins-reference) · [VS Code](https://code.claude.com/docs/en/vs-code) · [MCP](https://code.claude.com/docs/en/mcp)

> ⚠️ Los campos exactos de frontmatter de skills y subagentes, y la sintaxis de permisos y hooks,
> cambian entre versiones. **Verificar contra la documentación vigente al implementar.** El diseño
> propuesto no depende de campos exóticos: `name` + `description` alcanzan.

## Activo interno

- Skill `menuboard-fetch-diag` (Siainteractive) — procedimiento de 7 pasos verificado contra 10
  logs reales. Es el prototipo del harness y el caso de aceptación del MVP.
