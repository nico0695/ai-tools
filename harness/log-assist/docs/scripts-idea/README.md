# Análisis de logs de Dex Player

Guía práctica para leer, interpretar y automatizar el análisis de logs del player.
Consolida cuatro relevamientos previos (`MVP_PLAN`, `MVP_PLAN_CODEX`, `ANALYZER_SECTIONS`) y **valida todo contra 178.415 líneas de logs reales**.

> **Leé primero [`../log-format.md`](../log-format.md).**
> Este relevamiento se midió sobre un corpus de 14 archivos, **9 webOS y 5 Tizen**, de 5 grupos sync.
> `log-format.md` verificó un segundo corpus de 157.100 líneas, **100 % Tizen y de una sola pantalla**,
> y encontró 18 divergencias con lo que está acá: parte son alcance de plataforma (los stack traces y
> `[Webos Storage Manager]` no existen en Tizen) y parte son números que no se reproducen (el piso de
> RAM de 648 Mb, el pico de CPU de 98 %, el intervalo entre PLAY, el 25 % de split-brain).
>
> Para el parser de `loga_core` manda `log-format.md`. Este documento sigue siendo la referencia más
> amplia de patrones y flujos, y la única que cubre webOS — pero sus cifras valen para su corpus, no
> como umbrales universales.

---

## TL;DR

**Qué es esto.** 99 patrones con su regex, 10 flujos multi-línea y las reglas para leerlos. Todo verificado: ningún patrón del catálogo quedó sin apariciones en los logs reales, y se encontraron 15 patrones nuevos que ninguna documentación previa tenía.

**Las 7 cosas que hay que saber antes de tocar un log:**

1. **El formato es único y perfecto.** `YYYY-MM-DD HH:MM:SS.dd NIVEL [Componente] texto`, con 2 decimales siempre. Las 178.415 líneas parsean sin excepción. Los niveles son 5 y uno se llama `WARNING`, no `WARN`.

2. **Para contar reinicios, contá `Dex Player <versión>`.** El banner de arranque (53 signos `=`) se parece al bloque del cluster (54 signos `=`). Confundirlos infla los reinicios un **404 %**.

3. **La pantalla negra son 5 líneas en 100 milisegundos:** falla el parseo del JSON, falla la carga, falla la reproducción, y ahí aparece `Clearing current playlist`. Esa es la marca del negro, **no** `Playlist stopped`, que es parte del ciclo normal.

4. **El split-brain se ve en una sola línea:** contá los `[Master]` en la línea `Members:`. Más de uno es split-brain, cero es un grupo sin coordinación. En el corpus, **el 25 % de los snapshots mostró un cluster mal formado**.

5. **El intervalo entre comandos PLAY es la duración del medio, no una cadencia.** Usarlo como señal de split-brain, que es lo que proponía la documentación previa, da falso positivo permanente.

6. **Los umbrales dependen de la plataforma.** webOS reporta recursos cada 300 segundos y usa 1.064–1.288 Mb de RAM; Tizen reporta cada 60 segundos y usa 648–885 Mb. Un umbral único falla seguro.

7. **El 60 % del log son 20 mensajes repetidos.** Sin filtrar el ruido no se ve nada. Pero **ocultar no es lo mismo que no contar**: varios mensajes ruidosos son valiosos justamente por su ausencia.

**Sorpresas del corpus:** no hubo ninguna fuga de memoria · los 159 timeouts miden exactamente 50.000 ms, así que medir su duración no informa nada · los archivos `(1)` no son duplicados sino pantallas distintas · `[Global Error Handler]`, un módulo con 362 errores de reproducción, no estaba en ninguna documentación previa · los stack traces son el 20 % de las líneas ERROR y no son eventos.

---

## Índice

### Generales — aplican a cualquier log

| # | Sección | Qué responde |
|---|---|---|
| **[01](01-LECTURA-BASE.md)** | **Lectura base** | Formato de línea, identidad de la pantalla, manejo del tiempo, las 3 trampas que arruinan las cuentas. **Empezá acá** |
| [02](02-GENERAL-sesiones-reinicios.md) | Sesiones y reinicios | ¿Cuántas veces arrancó? ¿Fue programado o se cayó? ¿Cuánto uptime? |
| [03](03-GENERAL-recursos.md) | Recursos | ¿Está escalando la RAM? ¿Hay fuga? ¿La CPU está saturada? |
| [04](04-GENERAL-contenido-playlists.md) | Contenido y playlists | ¿Qué playlist hay? ¿Cambió? **¿Por qué se quedó en negro?** |
| [05](05-GENERAL-red-servidor.md) | Red y servidor | ¿Ve al servidor? ¿Está registrado? ¿Cuántas fallas de red? |
| [06](06-GENERAL-ruido.md) | Ruido | Cómo pasar de 178.000 líneas a las 50 que importan |

### Específicas — según qué subsistema use esa pantalla

| # | Sección | Qué responde |
|---|---|---|
| [07](07-SYNC-cluster.md) | **Cluster / Sync Group** | ¿Quién es el master? ¿Están todas en la misma playlist? ¿Hay split-brain? |
| [08](08-TEMPLATES.md) | Templates y menuboards | ¿El menuboard carga? ¿Los precios están actualizados? |
| [09](09-STORAGE-archivos.md) | Storage y archivos | ¿Faltan archivos? ¿Se bajó el contenido? |
| [10](10-PANTALLA-politicas-screenshots.md) | Pantalla y configuración | ¿Está encendida? ¿Se apagó por política o por falla? |

### Referencia

| # | Sección | Contenido |
|---|---|---|
| [11](11-CATALOGO.md) | **Catálogo** | Tabla resumen, patrones por criticidad, los 10 flujos, parámetros medidos |
| [12](12-PENDIENTES.md) | Pendientes | Errores corregidos de la doc previa, decisiones que dependen del producto, trazabilidad |

---

## Por dónde empezar según el problema

| Te reportan… | Mirá |
|---|---|
| "La pantalla está en negro" | [04 §4.7](04-GENERAL-contenido-playlists.md) |
| "Se reinicia sola" | [02 §2.4](02-GENERAL-sesiones-reinicios.md) y [03 §3.4](03-GENERAL-recursos.md) |
| "No actualiza el contenido" | [05 §5.7](05-GENERAL-red-servidor.md) |
| "Las pantallas están descoordinadas" | [07 §7.7](07-SYNC-cluster.md) |
| "El menú tiene precios viejos" | [08 §8.4](08-TEMPLATES.md) |
| "Falta contenido" | [09 §9.8](09-STORAGE-archivos.md) |
| "La pantalla está apagada" | [10 §10.5](10-PANTALLA-politicas-screenshots.md) |
| No sé qué pasa | [01 §1.4](01-LECTURA-BASE.md) |

---

## Convenciones

- **Todas las regex se aplican al `message`**, es decir a lo que queda después del nivel. No incluyen el timestamp. La gramática base que separa la línea está en [01 §1.1](01-LECTURA-BASE.md).
- ⚠️ **Al copiar una regex desde una tabla, reemplazá `\|` por `|`.** Markdown obliga a escapar la barra vertical dentro de tablas, pero en una regex `\|` significa una barra literal y `|` significa alternancia. Las regex que están en bloques de código no tienen este problema.
- **Los ejemplos van enmascarados:** `<IP>`, `<RUTA>`, `<URL>`, `<MAC>`.
- **Los números son medidos**, no estimados. Salen de scripts reproducibles en `temp/scripts/`.
- Cuando algo no se puede saber desde el log, está dicho explícitamente en vez de inventar un valor.

---

## Base de evidencia

| | |
|---|---|
| Líneas analizadas | 178.415 |
| Archivos | 14 (9 webOS, 5 Tizen) |
| Período | Septiembre 2025 a febrero 2026 |
| Grupos sync | 5 |
| Formas de mensaje distintas | 573 |
| Componentes | 44 |
| Fuentes documentales consolidadas | 35 documentos, 289 secciones |
