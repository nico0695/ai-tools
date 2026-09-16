# 01 — Lectura base: cómo se lee un log de Dex Player

> Sección **General**. Todo lo de acá aplica a cualquier log, de cualquier pantalla y plataforma.
> Dominio `FMT`. Empezá siempre por acá.

---

## 1.1 Formato de línea

**Todas** las líneas, sin excepción (verificado sobre 178.415 líneas), tienen esta forma:

```
2026-02-22 11:10:52.68 INFO [Server Manager] Heartbeat received from server
└────────┬────────┘ └┬┘ └─┬┘ └──────┬──────┘ └────────────┬──────────────┘
      fecha        hora  nivel   componente              texto
                  +2 dec
```

**Regex base** (la única que necesitás para partir cualquier línea):

```regex
^(?<fecha>\d{4}-\d{2}-\d{2}) (?<hora>\d{2}:\d{2}:\d{2})\.(?<cs>\d{2}) (?<nivel>INFO|SUCCESS|ERROR|DEBUG|WARNING) (?<message>.*)$
```

> **Importante:** todas las regex de esta documentación se aplican sobre `message`, es decir sobre lo que queda **después** del nivel. No incluyen el timestamp.

Y para separar el componente:

```regex
^\[(?<componente>[^\]]+)\](?:\s*\[(?<sub>[^\]]+)\])?\s*(?<texto>.*)$
```

Hay componentes de dos niveles, como `[Player] [Sync]`, `[Node] [Sync]` y `[MENUBOARD_TPL] [DataManager]`.

### Los 5 niveles

| Nivel | Frecuencia | Qué significa en la práctica |
|---|---:|---|
| `INFO` | 92,1 % | Operación normal. La mayoría es ruido. |
| `SUCCESS` | 6,2 % | Confirmación de algo que salió bien (heartbeat, handshake, playlist cargada). |
| `ERROR` | 0,84 % | **Empezá por acá.** Ojo: incluye stack traces y errores benignos (ver §1.5). |
| `DEBUG` | 0,71 % | Aparece solo en builds de QA. |
| `WARNING` | 0,12 % | El nivel más raro y a menudo el más informativo. |

> Es `WARNING`, no `WARN`. Si tu filtro busca `WARN` exacto, no encuentra nada.

---

## 1.2 De dónde sale cada dato de identidad

| Dato | Dónde está | Ejemplo |
|---|---|---|
| **Nombre de la pantalla** | `[Server Manager] Machine: <nombre>` | `Machine: TimHortonsTransistmicaP3` |
| **IP y MAC** | `[Server Manager] Hostname: <IP> <MAC>` | `Hostname: <IP> <MAC>` |
| **Tags** | `[Server Manager] New Tags saved [<tags>]` | `New Tags saved ["SYNC03"]` |
| **Plataforma** | `[Main] Initializing Dex Player. Platform "<plat>"` | `"webos"` o `"tizen"` |
| **Versión del player** | `Dex Player <x.y.z.w>` | `Dex Player 6.7.2601.2300` |
| **Versión de Dex Sync** | `[Player] [Sync] Version: <x.y.z>` | `Version: 1.9.1` |
| **Intervalo de heartbeat** | `[Server Manager] Machine HB Interval: <n> seconds` | `60 seconds` |
| **Grupo sync** | `[Player] [Sync] … - Group: <grupo> - Members: …` | `Group: 6DIC \| 6 DE DICIEMBRE \| 4V UL3J` |

**Regla práctica:** la identidad autoritativa es `Machine:`, no el nombre del archivo. Pero el nombre del archivo suele coincidir y a veces trae información extra (por ejemplo `...P4 MASTER.log` marca el rol).

### Nombre del archivo

Dos familias:

| Forma | Ejemplo | Fecha |
|---|---|---|
| Estándar | `20260222-0.log` | Del nombre: `YYYYMMDD` |
| Estándar con sufijo | `20260222-0 (1).log` | Del nombre. **El `(1)` NO es un duplicado** (ver §1.6) |
| Libre | `PJ - 6DIC 2.log`, `QMC32 QA 1.log` | **Solo del contenido** |

---

## 1.3 El tiempo: qué podés y qué no podés asumir

- **Los timestamps no traen zona horaria.** Comparar relojes entre pantallas distintas es una suposición, no un hecho. En Tizen hay una pista: `[Tizen App] Device time: Fri Sep 19 2025 16:24:25 -05:00`.
- **El orden es cronológico**, salvo en los reinicios. En el corpus analizado solo hubo 3 saltos hacia atrás; el mayor fue de ~2 horas, justo en un reinicio.
- **Un salto hacia atrás grande casi siempre significa reinicio.** Verificalo buscando el banner cerca.
- **Un hueco sin líneas no siempre es un problema.** Puede ser la pantalla apagada por política horaria.

---

## 1.4 Por dónde empezar a leer un log

Este es el recorrido que responde el 80 % de las preguntas en 5 minutos:

```
1. ¿Cuántas veces arrancó?        → contar  ^Dex Player [\d.]+$
2. ¿Qué es y dónde está?          → buscar  Machine:  /  Platform  /  Group:
3. ¿Hay errores graves?           → filtrar nivel ERROR, excluyendo "    at file://"
4. ¿Está reproduciendo?           → buscar  Playing Playlist  y  Playlist ended.
5. ¿Ve al servidor?               → contar  Heartbeat received  vs  Heartbeat Sync failed
6. ¿Está sano el cluster?         → buscar la línea  Members:  y contar  [Master]
7. ¿Se quedó en negro?            → buscar  Clearing current playlist  precedido de ERROR
```

---

## 1.5 Tres trampas que arruinan las cuentas

### Trampa 1: el banner de arranque y el bloque de sync son casi idénticos

Las dos son una línea de puros `=`. **Se distinguen por la cantidad:**

| Línea | Signos `=` | Qué es |
|---|---:|---|
| `INFO ====…` | **53** | **Banner de arranque.** Vienen de a dos, envolviendo la versión |
| `INFO ====…` | **54** | **Apertura o cierre del bloque `SYNC GROUP INFO`** |

Si contás todas las líneas de `=` como arranques, el error es enorme: en el corpus analizado darían 116 arranques en vez de 23, un **404 % de inflación** que se propaga a los reinicios diarios y al uptime.

```regex
^={53}$        ← banner de arranque (dividí el conteo por 2)
^={54}$        ← delimitador de bloque sync
```

**Alternativa más segura:** contá `^Dex Player [\d.]+$`, que da exactamente un match por arranque.

### Trampa 2: los stack traces son nivel ERROR pero no son errores

```
ERROR     at file:///media/cryptofs/apps/.../main.js:1:123
ERROR     at onFailure (file://<RUTA>:<N>:<N>)
```

Son **el 20 % de todas las líneas ERROR**. Siempre siguen a un error real. Filtralos:

```regex
^\s+at\s          ← continuación de stack trace, agrupar con el error anterior
```

### Trampa 3: no todo lo que dice ERROR está roto

- `Dir failed playlists` en los primeros 5 segundos de un arranque Tizen es **normal**: el player crea los directorios.
- `Failed to play video … interrupted by a new load request` es una **carrera benigna**: se recupera solo, en menos de 2 segundos.
- `CPU: 98.00%` en los primeros 30 segundos post-arranque es **el pico de inicialización**, no un problema.

---

## 1.6 Archivos `(1)`: no son duplicados

Cuando ves `20260222-0.log` y `20260222-0 (1).log`, la tentación es deduplicar. **No lo hagas.**

| Par | Líneas A | Líneas B | Líneas en común |
|---|---:|---:|---:|
| `20260222-0` vs `(1)` | 35.351 | 42.853 | **1** |
| `20260223-0` vs `(1)` | 5.469 | 5.468 | **3** |

Son **pantallas distintas del mismo grupo y del mismo día**. Es exactamente el material que necesitás para comparar miembros de un cluster.

---

## 1.7 Qué tan grande es el vocabulario

Es más chico de lo que parece: **573 formas de mensaje distintas** en 178.415 líneas. Los 20 mensajes más frecuentes son el 60 % del volumen, y casi todos son ruido. El catálogo de esta documentación cubre lo que importa.

Los componentes que más hablan:

| Componente | Líneas | Nota |
|---|---:|---|
| `[MENUBOARD_TPL]` (+ sub) | ~69.000 | Templates. Casi todo ruido |
| `[Webos Storage Manager]` | 18.042 | Solo webOS. Casi todo ruido |
| `[Channel Manager]` | 15.293 | Transiciones de medio |
| `[Player] [Sync]` | 14.985 | Comandos PLAY |
| `[Hardware Policies]` | 12.558 | Políticas de display |
| `[Input Manager]` | 11.604 | Ruido puro |
| `[Server Manager]` | 6.255 | **Alta señal:** heartbeats, handshake, identidad |
| `[Node] [Sync]` | 2.006 | **Alta señal:** topología del cluster |
| `[Global Error Handler]` | 364 | **Alta señal:** fallas de reproducción |

---

**Siguiente:** [02 — Sesiones y reinicios](02-GENERAL-sesiones-reinicios.md)
