# 11 — Catálogo: tabla resumen

> Vista breve de cómo quedó segmentado el relevamiento. El detalle de cada patrón está en su sección.

---

## 11.1 Cómo se segmentó

| # | Sección | Tipo | Dominio | Patrones | Qué responde |
|---|---|---|---|---:|---|
| [01](01-LECTURA-BASE.md) | Lectura base | General | `FMT` | 9 | Cómo se lee una línea, identidad, tiempo, trampas |
| [02](02-GENERAL-sesiones-reinicios.md) | Sesiones y reinicios | General | `SYS`, `SYS.VER` | 13 | Cuántas veces arrancó, programado o caída, uptime |
| [03](03-GENERAL-recursos.md) | Recursos | General | `TEL` | 1 | CPU, RAM, fugas de memoria |
| [04](04-GENERAL-contenido-playlists.md) | Contenido y playlists | General | `CNT`, `CNT.PLAY`, `CNT.DL` | 18 | Qué playlist hay, updates, **pantalla negra** |
| [05](05-GENERAL-red-servidor.md) | Red y servidor | General | `NET` | 17 | Handshake, heartbeats, timeouts, conectividad |
| [06](06-GENERAL-ruido.md) | Ruido | General | `NOISE` | 14 reglas | Cómo pasar de 178.000 líneas a 50 |
| [07](07-SYNC-cluster.md) | Cluster / Sync Group | Específica | `SYNC` | 18 | Master, consistencia, **split-brain** |
| [08](08-TEMPLATES.md) | Templates y menuboards | Específica | `TPL` | 14 | Menuboards, precios, faltantes |
| [09](09-STORAGE-archivos.md) | Storage y archivos | Específica | `STO`, `CNT.DL`, `DIR` | 13 | Archivos faltantes, descargas, JSON corrupto |
| [10](10-PANTALLA-politicas-screenshots.md) | Pantalla y config | Específica | `POL`, `SCR`, `SCH`, `CFG` | 17 | Display encendido, capturas, calendarios |

**Criterio de corte:** las secciones **generales** aplican a cualquier log, de cualquier pantalla. Las **específicas** aplican solo si ese log tiene ese subsistema (no todas las pantallas están en un grupo sync, no todas usan menuboards).

---

## 11.2 Patrones por señal de diagnóstico

### 🔴 Críticos — mirá estos primero

| Patrón | Sección | Por qué |
|---|---|---|
| `Fail parsing JSON. File:` | [09](09-STORAGE-archivos.md) | Inicia la cascada de pantalla negra |
| `Unexpected end of JSON input` | [04](04-GENERAL-contenido-playlists.md) | Playlist ilegible |
| `Clearing current playlist` **tras ERROR** | [04](04-GENERAL-contenido-playlists.md) | **El momento exacto del negro** |
| `IO_ERROR: Failed to open the file` | [04](04-GENERAL-contenido-playlists.md) | Medio ilegible |
| Más de un `[Master]` en `Members:` | [07](07-SYNC-cluster.md) | **Split-brain** |
| `Node server not Running` | [05](05-GENERAL-red-servidor.md) | Sync local caído |
| `Heartbeat Sync failed` en racha | [05](05-GENERAL-red-servidor.md) | Corte de conectividad |
| `Member <IP> is not active` | [07](07-SYNC-cluster.md) | Nodo del cluster caído |
| `Missing Content: N files` | [04](04-GENERAL-contenido-playlists.md) | Contenido incompleto |
| 3 o más `Dex Player <ver>` en un día | [02](02-GENERAL-sesiones-reinicios.md) | Ciclo de reinicios |

### 🟢 Hitos — confirman que algo funciona

| Patrón | Sección |
|---|---|
| `Dex Player <versión>` | [02](02-GENERAL-sesiones-reinicios.md) |
| `Handshake received. Code "LICOK"` | [05](05-GENERAL-red-servidor.md) |
| `Playing Playlist "<nombre>"` | [04](04-GENERAL-contenido-playlists.md) |
| `Heartbeat received from server` | [05](05-GENERAL-red-servidor.md) |
| `Machine: <nombre>` | [01](01-LECTURA-BASE.md) |
| `Sending command PLAY burst to all members` | [07](07-SYNC-cluster.md) |
| `Screenshot Uploaded to …` | [10](10-PANTALLA-politicas-screenshots.md) |

### ⚪ Ruido — el 60 % del volumen

`Read operation completed`, `preloadNextMedia`, `playNextMedia`, `Playlist ended.`, `Remote Control enabled`, `Panel enabled`, `Processing policies`, `Next Display State policy: NONE`, bloque `[MENUBOARD_TPL]`, `Device will reboot in N minutes`, `NodeJs service is running`, `Playlist stopped`, stack traces. Ver [06](06-GENERAL-ruido.md).

---

## 11.3 Los 10 flujos

Secuencias donde varias líneas juntas cuentan una historia. Todas verificadas contra logs reales.

| ID | Flujo | Cómo lo reconocés | Sección |
|---|---|---|---|
| F1 | Arranque en frío | `={53}` → `Dex Player <ver>` → `Initializing … Platform` | [02](02-GENERAL-sesiones-reinicios.md) |
| F2 | Registro con el servidor | `Sending Handshake` → `Code "LICOK"` → `Machine:` → `HB Interval` | [05](05-GENERAL-red-servidor.md) |
| F3 | Reinicio programado | Countdown que baja → corte → F1 | [02](02-GENERAL-sesiones-reinicios.md) |
| F4 | Reinicio inesperado | Corte seco **sin countdown previo** | [02](02-GENERAL-sesiones-reinicios.md) |
| F5 | Ciclo de reproducción | `preloadNextMedia` → `PLAY Command` → `Playlist ended.` | [04](04-GENERAL-contenido-playlists.md) |
| F6 | Update de playlist | `Playlist stopped` → `PLAYLIST ID` → `New Playlist received` → `Playing Playlist` | [04](04-GENERAL-contenido-playlists.md) |
| F7 | **JSON corrupto → negro** | `Fail parsing JSON` → 2 ERROR más → `Clearing current playlist` | [04](04-GENERAL-contenido-playlists.md) |
| F8 | Snapshot del cluster | `={54}` → `Members:` → header → filas → `={54}` | [07](07-SYNC-cluster.md) |
| F9 | Rol en el cluster | `Joining multicast` → `New member discovered` → `PLAY burst` si es master | [07](07-SYNC-cluster.md) |
| F10 | Caída y recuperación de red | `Heartbeat Sync failed` ×n → `Heartbeat received` | [05](05-GENERAL-red-servidor.md) |

---

## 11.4 Parámetros medidos

Valores obtenidos de los logs, no supuestos.

| Parámetro | Valor | Cómo se obtuvo |
|---|---|---|
| Decimales del timestamp | Siempre 2 | 178.415 de 178.415 líneas |
| Niveles | 5: INFO, SUCCESS, ERROR, DEBUG, WARNING | Conteo completo |
| Banner de arranque | 53 signos `=` | Conteo |
| Bloque sync | 54 signos `=` | Conteo |
| Intervalo de heartbeat | 60 s | Declarado por el log **y** medido |
| Telemetría en webOS | 300 s | Medido |
| Telemetría en Tizen | 60 s | Medido |
| RAM en webOS | 1.064 – 1.288 Mb | Medido |
| RAM en Tizen | 648 – 885 Mb | Medido |
| Timeout HTTP | 50.000 ms, siempre | 159 de 159 |
| Intervalo de screenshots | 30 min | Declarado por el log |
| Intervalo entre PLAY | 4,4 a 60 s | **Es la duración del medio, no una cadencia** |
| Bloques `SYNC GROUP INFO` | De 4 min a 6,4 h | **Esporádicos, no periódicos** |

---

## 11.5 Sin umbral definido

Estos valores **no están en ninguna fuente ni se pueden deducir de los logos**. Requieren criterio del producto:

RAM y CPU absolutos por plataforma · pendiente que define una fuga · qué cuenta como error "reiterado" o que "persiste" · ventana para dar un reinicio por completado · tolerancia de desfase entre versiones de playlist · espacio libre mínimo · lista de archivos críticos · horario de tienda esperado.

Ver [12 — Pendientes](12-PENDIENTES.md).

---

**Anterior:** [10 — Pantalla y config](10-PANTALLA-politicas-screenshots.md) · **Siguiente:** [12 — Pendientes](12-PENDIENTES.md)
