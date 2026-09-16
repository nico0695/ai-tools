# 12 — Pendientes y decisiones abiertas

> Lo que el relevamiento **no** pudo cerrar, y por qué. Nada de esto bloquea usar la documentación: son afinaciones.

---

## 12.1 Errores de la documentación previa (ya corregidos acá)

Vale dejarlos anotados porque estaban en los catálogos originales y, si alguien vuelve a esos documentos, los va a encontrar:

| Lo que decía | Lo que dicen los logs |
|---|---|
| El banner de arranque es cualquier línea de `=` | Son 53 signos; el bloque sync usa 54. Sin distinguirlos, los reinicios se inflan un **404 %** |
| `Heartbeat Sync failed` es la caída del nodo sync local | Lo emite `[Server Manager]` en el **100 %** de los 196 casos: es el servidor |
| El split-brain se detecta por la tasa de PLAY (≥4/min) | **Falso positivo permanente.** Un player sano con clips de 15 s emite 4/min. La señal real es contar `[Master]` |
| `Playlist stopped` marca el cese de reproducción | Es parte del ciclo **normal** de update: 144 apariciones en operación sana |
| `Next Display State policy` no aparece en los ejemplos | **5.864 apariciones** en 12 de 14 archivos |
| `Node server not Running` no aparece en los ejemplos | 14 apariciones en 9 archivos |
| La fila del cluster exige un id numérico de playlist | Existe `Playlist: undefined`. La regex estricta **borra al miembro** del análisis |
| El estado del miembro es `NEW\|READY\|PLAYING` | `NEW` **nunca apareció**. Dejá el enum abierto |
| `[TEMPLATE] Metadata received` con la palabra `content` | **Ese texto no existe.** El real es `[MENUBOARD_TPL] Metadata {…}` |
| El timestamp puede traer de 0 a 3 decimales | **Siempre 2**, sin excepción |
| El nivel es `WARN` | Es `WARNING` |
| Alertar por p95 del timeout ≥ 50.000 ms | Los 159 timeouts **miden exactamente 50.000 ms**: la alerta estaría siempre encendida |
| Los archivos `(1)` son duplicados a deduplicar | Comparten 1 y 3 líneas: son **pantallas distintas** |

---

## 12.2 Decisiones que dependen del producto

No las resuelve ningún log: hay que definirlas.

| # | Decisión | Por qué importa |
|---|---|---|
| 1 | **Umbrales de RAM y CPU por plataforma** | Los rangos medidos son 1.064–1.288 Mb en webOS y 648–885 Mb en Tizen, pero cuál es el techo aceptable es criterio del producto |
| 2 | **Qué pendiente de RAM define una fuga** | Referencia: lo normal va de −21 a +6,4 Mb/h y cambia de signo |
| 3 | **Qué significa "reiterado" o "si persiste"** | Varias alertas heredadas usan estas palabras sin número |
| 4 | **Escala de severidad** | Hay 5 niveles nativos en el log; el mapeo a crítico/importante/ruido es una convención |
| 5 | **Precedencia entre patrones solapados** | Una línea puede matchear varios patrones. Si los KPIs son conteos, hay doble conteo |
| 6 | **Lista de archivos críticos** | Define si un `File does not exist` es ruido o incidente |
| 7 | **Horario de tienda esperado** | Sin él, no se puede distinguir un apagado programado de una caída |
| 8 | **Clasificación de motivos de reinicio** | Cuáles cuentan como falla y cuáles como mantenimiento |

---

## 12.3 Lo que no se puede saber desde el log

| Limitación | Impacto |
|---|---|
| **No hay zona horaria en la línea** | Comparar relojes entre pantallas es una suposición. En Tizen hay una pista: `[Tizen App] Device time: … -05:00` |
| **No existe el motivo del reinicio** | El log no dice por qué se reinició. Solo se puede inferir por lo que pasó antes |
| **No hay línea base de espacio en disco** | Solo 39 menciones y ningún caso de disco lleno |
| **`Channel` y `MachineId` no están documentados** | Existen (`Channel: 5`, `MachineId: 98309`) pero su semántica exacta no se puede deducir |
| **Un log es la visión de un nodo** | El split-brain sí se ve con un archivo, pero confirmar qué muestra cada pantalla necesita los logs del grupo |
| **No hay logs de Android** | El corpus tiene 9 webOS y 5 Tizen. Android no está verificado |

---

## 12.4 Cobertura del relevamiento

| Métrica | Valor |
|---|---|
| Líneas analizadas | 178.415 |
| Archivos | 14 (9 webOS, 5 Tizen) |
| Formas de mensaje distintas | 573 |
| Componentes distintos | 44 |
| Patrones catalogados | 99 (+15 nuevos hallados en los logos) |
| Patrones con 0 apariciones | **0** |

**Qué quedó fuera de la verificación:**
- Algunos patrones existen en pocos archivos, así que su comportamiento en otros contextos no está confirmado: `Dir failed` (6), `All tasks were finished` (3), `Player lost Internet connection` (4), `HTTP status` (5).
- Los 4 grupos sync del corpus son chicos (de 2 a 10 miembros). Grupos más grandes pueden comportarse distinto.
- El corpus cubre jornadas de 8 a 16 horas. No hay logs de varios días seguidos para ver tendencias largas de RAM.

---

## 12.5 Trazabilidad

Todo el trabajo intermedio está en `temp/`:

| Archivo | Contenido |
|---|---|
| `00_PLAN_ANALISIS.md` | Plan y decisiones metodológicas |
| `01_inventario_fuentes.md` | Triage de 289 secciones de 35 documentos |
| `02a`–`02d_extract_*.md` | Extracción por fuente, con `archivo:línea` |
| `03_catalogo_unificado.md` | 216 patrones → 99 deduplicados |
| `03_heuristicas_ruido.md` | Heurísticas, ruido, casos borde, umbrales |
| `03_conflictos.md` | Índice de los 80 conflictos |
| `04_validacion_regex.md` | Validación contra logs, con veredictos |
| `05_heuristicas_flujos.md` | Heurísticas corregidas y taxonomía final |
| `scripts/` | Scripts reproducibles y salidas crudas |

Para rehacer las mediciones:

```bash
cd CONSOLIDATION/temp/scripts
python3 profile.py      # gramática, formas, componentes, perfil por archivo
python3 conflicts.py    # conteos por patrón y capturas
python3 flows.py        # cadencias, RAM, duplicados
python3 sequences.py    # secuencias reales de cada flujo
```

---

**Anterior:** [11 — Catálogo](11-CATALOGO.md) · **Volver al** [índice](README.md)
