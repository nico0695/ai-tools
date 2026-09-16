# Corpus B — Catálogo de formas de mensaje (Dex Player, ARROYO SECO 2 MBV 01)

## 0. Alcance y método

- **10 archivos**, `DexPlayer-20260904-0.log` .. `-20260910-0.log` y `DexPlayer-20260820-0.log` .. `-20260822-0.log`.
- **157.100 líneas**, **348 formas de mensaje distintas** (normalizadas).
- Plataforma **Tizen** — `[Main] Initializing Dex Player. Platform "tizen"` (`DexPlayer-20260904-0.log:3198`).
- Player `Dex Player 6.4.2408.2600` (18 arranques) · Dex Sync `1.6.21`.
- Este nodo es el **MASTER** del grupo (2.386 `Sending command PLAY burst to all members`).

Formato de línea: `YYYY-MM-DD HH:MM:SS.cc LEVEL <mensaje>` — **centésimas**, no milisegundos.

Niveles observados:

INFO 116.913 (74,42 %) · SUCCESS 23.360 (14,87 %) · **DEBUG 16.589 (10,56 %)** · ERROR 172 (0,11 %) · WARNING 66 (0,04 %).

> **DEBUG no está documentado en ningún archivo de referencia** y es el 10,6 % del corpus. Ver §8.

Enmascarado aplicado: `<MACHINE>` (nombre de pantalla/grupo), `<IP>`, `<MAC>`, `<PATH>`, `<MEDIA>`, `<PLAYLIST>`, `<URL>`. Estructura, corchetes, espaciado y puntuación se conservan verbatim (incluidos los **dobles espacios** donde existen).

---

## 1. Recursos / telemetría

### Forma única

```
2026-09-04 00:00:48.00 INFO [System Manager] CPU: 8.00%. Used RAM: 815.25 Mb
```
`DexPlayer-20260904-0.log:57`

Regex: `^\[System Manager\] CPU: (?<cpu>[\d.]+)%\. Used RAM: (?<ram>[\d.]+) Mb$` — **11.605 líneas (7,39 %)**, una sola forma. Coincide 1:1 con `03-GENERAL-recursos.md §3.1`.

Existe una **segunda** fuente de CPU/RAM no documentada, dentro del bloque de estado (§5), 17 apariciones, sin prefijo de componente y con `CPU usage:` en vez de `CPU:`:
`2026-09-04 18:04:51.11 INFO CPU usage: 8.00%. Used RAM: 777.43 Mb` — `DexPlayer-20260904-0.log:12971`.

### Cadencia medida (delta entre muestras consecutivas, dentro de cada archivo)

60 s → 11.458 (98,82 %) · 59 s → 62 (0,53 %) · 61 s → 60 (0,52 %) · resto (47–55 s, 63–120 s) → 15 (0,13 %).

n = 11.595 deltas. **Cadencia real = 60 s**, exactamente lo que `03` declara para Tizen. Los días completos traen **1.440 muestras exactas** (= 24 h × 60).

### Muestras faltantes

Prácticamente ninguna. Sólo **5 deltas > 65 s** en todo el corpus, y los 5 caen en la ventana de reinicio programado de las 04:00:

96 s en `DexPlayer-20260905-0.log:3292`, 79 s en `DexPlayer-20260906-0.log:3167`, 91 s en `DexPlayer-20260909-0.log:2950`.
El máximo (120 s, `DexPlayer-20260820-0.log:4450`) equivale a **1 sola muestra perdida**.

Hueco real, pero **entre archivos**, no dentro: `DexPlayer-20260906-0.log` termina su telemetría a las `14:56:43.46` y `DexPlayer-20260907-0.log` la retoma a las `22:33:58.84` → **~31,6 h sin telemetría** (el archivo `20260907` tiene sólo 1.107 líneas y 86 muestras).

### Rangos observados

CPU: 1,00 % – **54,00 %**, promedio 7,47 %. RAM: **564,64 Mb** – 866,50 Mb, promedio 729,5 Mb.

- **1.465 de 11.605 muestras (12,6 %) están por debajo del piso de 648 Mb** que `03 §3.3` declara para Tizen. Ninguna supera el techo de 885 Mb.
- **Ninguna muestra supera 90 % de CPU.** El pico post-arranque documentado ("98 % en los primeros 30 s") **no aparece**: el máximo absoluto es 54,00 %, y ocurre justamente a +2,7 s del handshake (`DexPlayer-20260904-0.log:3227`, `CPU: 54.00%. Used RAM: 654.02 Mb`).

---

## 2. Red / servidor

### Handshake (secuencia real, 17 ocurrencias — una por arranque con red)

```
2026-09-04 04:00:42.90 INFO [Server Manager] Sending Handshake
2026-09-04 04:00:43.19 INFO [System Manager] CPU: 54.00%. Used RAM: 654.02 Mb
2026-09-04 04:00:43.21 INFO [Server Manager] Hostname: <IP> <MAC>
2026-09-04 04:00:43.36 INFO [System Manager] The player has connectivity with the server
2026-09-04 04:00:45.57 SUCCESS [Server Manager] Handshake received. Code "LICOK"
2026-09-04 04:00:45.58 INFO [Server Manager] Machine: <MACHINE>
2026-09-04 04:00:45.58 INFO [Server Manager] Machine HB Interval: 60 seconds
```
`DexPlayer-20260904-0.log:3226-3232`

| Forma | Nivel | Conteo |
|---|---|---:|
| `[Server Manager] Fetching dex config on <URL>` | INFO | 17 |
| `[Server Manager] Sending Handshake` | INFO | 17 |
| `[Server Manager] Hostname: <IP> <MAC>` | INFO | 17 |
| `[Server Manager] No tenant code found in dex_config.xml` | WARNING | 17 |
| `[Server Manager] Handshake received. Code "LICOK"` | SUCCESS | 17 |
| `[Server Manager] Machine: <MACHINE>` / `Machine HB Interval: 60 seconds` | INFO | 17 |
| `[Server Manager] New Tags saved ["<TAG>",…]` | INFO | **1** |

- `Code "LICOK"` es el **único** código observado (17/17). Confirma `05 §5.1`.
- `No tenant code found in dex_config.xml` en los 10 archivos (`DexPlayer-20260908-0.log:2905`). Confirma `05 §5.1`.
- **18 arranques pero sólo 17 handshakes**: `DexPlayer-20260820-0.log` tiene 2 `Dex Player 6.4.2408.2600` y 1 solo `Sending Handshake`.
- `New Tags saved` aparece **1 sola vez** en todo el corpus (`DexPlayer-20260909-0.log:12658`), no una por handshake.

### Heartbeat

```
2026-09-04 04:00:49.00 SUCCESS [Server Manager] Heartbeat received from server      (DexPlayer-20260904-0.log:61)
2026-09-06 02:09:55.57 ERROR [Server Manager] Heartbeat Sync failed. Status: Error: Network Error   (DexPlayer-20260906-0.log:1668)
```

| Forma | Nivel | Conteo | % del total |
|---|---|---:|---:|
| `[Server Manager] Heartbeat received from server` | SUCCESS | **11.464** | 7,30 % |
| `[Server Manager] Heartbeat Sync failed. Status: Error: Network Error` | ERROR | **145** | 0,09 % |

Tasa de falla = 145 / 11.609 = **1,25 %**.

**Sólo existe una causa de falla en este corpus: `Error: Network Error`. Cero timeouts** (`grep -c 'timeout of' = 0`).

Distribución por archivo y racha máxima de fallas consecutivas:

`DexPlayer-20260909-0.log` 70 (racha máx. 15) · `-20260908-0.log` 40 (14) · `-20260906-0.log` 29 (15) · `-20260820-0.log` 4 (2) · `-20260821-0.log` 2 (2) · los otros 5 archivos, 0.

### Cadencia real del heartbeat vs la declarada

Declarada: `Machine HB Interval: 60 seconds` (17/17).
Medida sobre `received` + `failed` juntos, n = 11.599 deltas:

60 s → 11.030 (95,09 %) · 59 s → 240 (2,07 %) · 61 s → 239 (2,06 %) · resto 30–90 s → 88 (0,76 %) · **> 120 s → 2**.

**Confirma los 60 s declarados.** Los dos huecos grandes están ambos en `DexPlayer-20260820-0.log`: uno de **2.088 s (~35 min)** que termina a las `04:33:59.71` y otro artefacto de salto de reloj a las `04:01:41.43` (ver §8, timestamps 1969).

### Otras señales de red / salida

| Forma | Nivel | Conteo | Cita |
|---|---|---:|---|
| `[Screenshots Manager] Tizen Screenshot API called` | INFO | 762 | `DexPlayer-20260904-0.log:58` |
| `[Screenshots Manager] Screenshot Uploaded to <PATH>` | INFO | 762 | `DexPlayer-20260904-0.log:59` |
| `[Logs Manager] Logs uploaded to <URL>` | INFO | 96 | `DexPlayer-20260904-0.log:12987` |
| `[Player] Socket not initialized for report` | WARNING | 33 | `DexPlayer-20260908-0.log:9752` |

Cadencia de screenshots: **900 s exactos** (93 de 94 deltas en `DexPlayer-20260904-0.log`), consistente con `Screenshots Interval: 900` del bloque de estado.

---

## 3. Contenido / playlists

### Formas del ciclo de vida presentes

| Forma | Nivel | Conteo | Cita |
|---|---|---:|---|
| `[Player] [Sync] PLAY Command received. Media "<MEDIA>"` | INFO | 2.494 | `DexPlayer-20260904-0.log:39` |
| `[Player] Playlist ended.` | INFO | 573 | `DexPlayer-20260904-0.log:4293` |
| `[Player] Reported playlist to change is not trigger. Processing state.` | INFO | 61 | — |
| **`[Player] Playing Playlist "<PLAYLIST> [<TS>]"`** | SUCCESS | **56** | `DexPlayer-20260908-0.log:2961` |
| `[Node] [Sync] PLAYLIST ID = <N>` | INFO | 56 | — |
| `[Player] [Sync] Executing scheduled change of playlist` | INFO | 40 | `DexPlayer-20260904-0.log:1` |

### Formas del ciclo de vida AUSENTES (conteo = 0)

`Clearing current playlist` · `Channel removed` · `preloadNextMedia` · `playNextMedia: Transitioning media` · `[Node] [Sync] Playlist stopped` · `Fail parsing JSON` · `Global Error Handler` · `Missing Content` · `Check integrity from heartbeat fail.` · `Read operation completed for path` · `[Webos Storage Manager]` / `[WebOS Storage]` · `Cannot download image` · `Error downloading file`.

**Este corpus no puede ejercitar la cascada de pantalla negra de `04 §4.4` ni el ciclo `preload/playNext` de `04 §4.2`.** Ver §8.

### Secuencia real de cambio de playlist (12 líneas, verbatim, enmascarada)

`DexPlayer-20260908-0.log:3841-3852`

```
2026-09-08 05:00:12.74 INFO [MENUBOARD_TPL] [INFO] STOP_TPL received
2026-09-08 05:00:13.01 SUCCESS [Player] Processing State Sync
2026-09-08 05:00:13.19 SUCCESS [Player] Playing Playlist "<PLAYLIST> [2026-08-27T14:46:31.027Z]"
2026-09-08 05:00:13.28 INFO [MENUBOARD_TPL] [INFO] Clean media managers on unload
2026-09-08 05:00:13.28 INFO [Node] [Sync] PLAYLIST ID = 6065
2026-09-08 05:00:13.29 INFO [Node] [Sync] New Playlist received
2026-09-08 05:00:13.41 INFO [Player] Schedule time: LOCAL
2026-09-08 05:00:13.42 INFO [Player] End date: Tue Sep 08 2026 11:00:00 GMT-0300. Now: Tue Sep 08 2026 05:00:13 GMT-0300
2026-09-08 05:00:13.43 INFO [Player] Next Playlist in 359 minutes
2026-09-08 05:00:13.43 INFO [Player] Playing Schedule
2026-09-08 05:00:15.25 INFO [Node] [Sync] Sending command PLAY burst to all members
2026-09-08 05:00:16.20 INFO [Player] [Sync] PLAY Command received. Media "<MEDIA>"
```

### Cadencia de reproducción

`PLAY Command received` en `DexPlayer-20260904-0.log` (n = 305 deltas):

240 s ×184 · 480 s ×67 · 80 s ×26 · 241 s ×15. **p50 = 240 s (4 min).** `Playlist ended.` en el mismo archivo: **480 s** en 61 de 71 deltas.

**Hay un solo medio en todo el corpus**: `PLAY Command received. Media "tpl-menuboard.<N>.<N>.<N>.<N>-store"` — 2.494 de 2.494. Es un template, no un video.

---

## 4. Errores

### Top de formas ERROR (son **sólo 6** en todo el corpus; 172 líneas = 0,11 %)

| # | Forma (verbatim, normalizada) | Conteo | Cita |
|---:|---|---:|---|
| 1 | `[Server Manager] Heartbeat Sync failed. Status: Error: Network Error` | 145 | `DexPlayer-20260906-0.log:1668` |
| 2 | `[Player] Checking playlist failed  Cannot read property 'message' of undefined` | 15 | `DexPlayer-20260908-0.log:9681` |
| 3 | `[Player] While updating content. Error listing files for schedules/<PLAYLIST>.json. PLATFORM ERROR other` | 3 | `DexPlayer-20260908-0.log:9672` |
| 4 | `[Player] CheckInternalIntegrity. Downloading MachineFiles Cannot read property 'message' of undefined Cannot read property 'message' of undefined` | 3 | `DexPlayer-20260908-0.log:9682` |
| 5 | `Dir failed schedules` | 3 | `DexPlayer-20260908-0.log:9699` |
| 6 | `Dir failed playlists` | 3 | `DexPlayer-20260908-0.log:9698` |

> (Se piden 10; **no existen 10**. El corpus tiene exactamente 6 formas ERROR distintas.)

Nótese el **doble espacio** en la forma #2, entre `failed` y `Cannot` — hay que preservarlo.

### Stack traces sobre ERROR

- Líneas sin prefijo de timestamp (continuaciones): **0**
- Líneas que matchean `^\s+at\s`: **0**
- Líneas que contienen un frame estilo `at fn (…)`: **0**

**Porcentaje de líneas ERROR que son continuación de stack trace: 0,00 % (0 de 172).**

Todos los mensajes de este corpus son de **una sola línea**. No hay multilínea de ningún tipo.

### Error real con su contexto (verbatim, 10 líneas)

`DexPlayer-20260908-0.log:9691-9700` — no hay stack trace que transcribir; lo que sigue al error es el reinicio y los `Dir failed` del arranque:

```
2026-09-08 13:36:47.74 WARNING [Tizen Storage] The storage is locked. Cannot write playlists/<PLAYLIST>.json.lock
2026-09-08 13:36:47.74 ERROR [Player] Checking playlist failed  Cannot read property 'message' of undefined
2026-09-08 13:36:47.75 WARNING [Tizen Storage] The storage is locked. Cannot write playlists/<PLAYLIST>.json.lock
2026-09-08 13:36:47.76 ERROR [Player] Checking playlist failed  Cannot read property 'message' of undefined
2026-09-08 13:36:51.68 INFO [Dex Player] System will reboot. Reason: SOFT_CLEAN_COMMAND
1969-12-31 21:00:17.65 INFO =====================================================
1969-12-31 21:00:17.66 INFO Dex Player 6.4.2408.2600
1969-12-31 21:00:17.66 INFO =====================================================
1969-12-31 21:00:18.21 ERROR Dir failed playlists
1969-12-31 21:00:18.21 ERROR Dir failed schedules
```

### WARNING (4 formas, 66 líneas)

| Forma | Conteo | Cita |
|---|---:|---|
| `[Player] Socket not initialized for report` | 33 | `DexPlayer-20260908-0.log:9752` |
| `[Server Manager] No tenant code found in dex_config.xml` | 17 | `DexPlayer-20260908-0.log:2905` |
| `[Tizen Storage] The storage is locked. Cannot write playlists/<PLAYLIST>.json.lock` | 15 | `DexPlayer-20260908-0.log:9680` |
| `[Sync Channel Manager] Controller is not initialized` | 1 | `DexPlayer-20260908-0.log:3854` |

---

## 5. Sync / cluster — **SÍ está presente**

| Elemento | Conteo |
|---|---:|
| Bloques `SYNC GROUP INFO` | **17** |
| Líneas `Version: … - Group: … - Members: …` | **18** |
| Marcas `[Master]` en línea `Members:` | 17 (17 líneas con 1, 1 línea con 0) |
| Filas `(MASTER)` dentro de bloques | 16 |
| `[Node] [Sync] Sending command PLAY burst to all members` | **2.386** |
| `[Player] [Sync] PLAY Command received` | 2.494 |

**No hay split-brain en este corpus**: 16 bloques con 3 filas y exactamente 1 `(MASTER)`; 1 bloque de 1 sola fila con 0 `(MASTER)` (el arranque de `DexPlayer-20260907-0.log`, cuando todavía no descubrió a nadie).

### Bloque completo verbatim (enmascarado)

`DexPlayer-20260904-0.log:12980-12984`

```
2026-09-04 18:04:51.12 INFO ======================================================
2026-09-04 18:04:51.14 INFO [Player] [Sync] Version: 1.6.21 - Group: <MACHINE> - Members: <IP> [Master] <IP> <IP> 
2026-09-04 18:04:51.19 INFO ===================SYNC GROUP INFO====================
2026-09-04 18:04:51.19 INFO <IP> | PLAYING | Playlist: 6065 [2026-08-27T14:46:31.027Z] | Schedule: 238 [2026-08-27T14.46.45.703] | Playlist To Change: [<PLAYLIST>.json,<PLAYLIST>.json,<PLAYLIST>.json,<PLAYLIST>.json]  (MASTER)
2026-09-04 18:04:51.19 INFO <IP> | PLAYING | Playlist: 6065 [2026-08-27T14:46:31.027Z] | Schedule: 238 [2026-08-27T14.46.45.703] | Playlist To Change: [<PLAYLIST>.json,<PLAYLIST>.json,<PLAYLIST>.json,<PLAYLIST>.json] 
2026-09-04 18:04:51.19 INFO <IP> | PLAYING | Playlist: 6065 [2026-08-27T14:46:31.027Z] | Schedule: 238 [2026-08-27T14.46.45.703] | Playlist To Change: [<PLAYLIST>.json,<PLAYLIST>.json,<PLAYLIST>.json,<PLAYLIST>.json] 
2026-09-04 18:04:51.20 INFO ======================================================
```

Notas de parsing verificadas:
- La línea `Members:` **termina en un espacio en blanco**, y cada fila de miembro sin `(MASTER)` también.
- La fila `(MASTER)` va precedida de **dos espacios**.
- Delimitador del bloque: **54 `=`**. Banner de arranque: **53 `=`**. Confirmado (53 líneas de 54 signos, 36 de 53).

### Estados y `Schedule` observados en filas de miembro (49 filas)

Estados: `PLAYING` 47 · `NEW` 1 · `DOWNLOAD` 1 · `READY` **0**.
Formas de `Schedule`: `Schedule: <id> [<ts>]` **48** · `Schedule:  []` (vacío) **1**.

Fila con `Playlist: undefined` y estado `NEW` (única, y a la vez la única con `Schedule` vacío):

```
2026-09-07 22:34:05.42 INFO <IP> | NEW | Playlist: undefined [] | Schedule:  [] | Playlist To Change: [undefined] 
```
`DexPlayer-20260907-0.log:84`. Fila `DOWNLOAD` (`DexPlayer-20260908-0.log:12061`):
```
2026-09-08 16:43:29.53 INFO <IP> | DOWNLOAD | Playlist: 6065 [2026-08-27T14:46:31.027Z] | Schedule: 238 [2026-08-27T14.46.45.703] | Playlist To Change: [<PLAYLIST>.json]
```

### Descubrimiento y elección de master

`DexPlayer-20260904-0.log:3238-3255`

```
2026-09-04 04:00:45.84 INFO [Node] [Sync] Joining multicast group
2026-09-04 04:00:48.13 INFO [Node] [Sync] New member discovered: <IP> | State: PLAYING | Channel: 3 | Is Master: false | MachineId: 3059
2026-09-04 04:00:48.13 INFO [Node] [Sync] Channels empty
2026-09-04 04:00:48.14 INFO [Node] [Sync] Master false | memberInfo false | masterDetermined false
2026-09-04 04:01:10.84 INFO [Node] [Sync] This Machine is Master
```

| Forma `[Node] [Sync]` | Conteo |
|---|---:|
| `[SyncShouldPlay] Don't play '<MEDIA>' from: <HH:MM:SS> - to: <HH:MM:SS>` | 4.463 |
| `Sending command PLAY burst to all members` | 2.386 |
| `Member <IP> is ready to change Playlist` | 201 |
| **`This Machine is Master`** | **12** |

**Formas nuevas no documentadas en `07`**: `[SyncShouldPlay] Don't play …` (la forma más voluminosa del dominio SYNC, 4.463), `This Machine is Master`, `Joined to group. Member <IP> is Master`, `START PLAYER CALLED`, `No media to play`, `Emit joined playerWebSocket`, `<IP> IS Triggering playlist:change to all members`, `Maximum common between the players …`, `"<IP>" : [<lista>]`.

`MachineId` en este corpus es de **4 dígitos** (3057, 3058, 3059), no de 5. `Channel` toma 1, 2, 3.

**Ausentes**: `Member <IP> is not active` (0), `Next candidates check in <N> seconds` (0), `[Player] [Sync] Error checking group content` (0), `Node server not Running` (0), `NodeJs service is running` (0).

---

## 6. Ruido — top 20 formas por volumen

Normalización: `<URL>`, `<IP>`, `<MAC>`, `"<S>"` (contenido entre comillas), `<JSON>` (llaves), `<N>` (todo número o número punteado).

| # | Forma (nivel + mensaje normalizado) | Líneas | % de 157.100 |
|---:|---|---:|---:|
| 1 | `INFO [System Manager] CPU: <N>%. Used RAM: <N> Mb` | 11.605 | 7,39 % |
| 2 | `SUCCESS [Input Manager] Panel Unlocked` | 11.574 | 7,37 % |
| 3 | `INFO [System Manager] Device will reboot in <N> minutes` | 11.574 | 7,37 % |
| 4 | `INFO [Input Manager] Remote Control Enabled` | 11.574 | 7,37 % |
| 5 | `INFO [Hardware Policies] Processing policies` | 11.574 | 7,37 % |
| 6 | `INFO [Hardware Policies] Next Display State policy: NONE` | 11.574 | 7,37 % |
| 7 | `SUCCESS [Server Manager] Heartbeat received from server` | 11.464 | 7,30 % |
| 8 | `INFO [Node] [Sync] [SyncShouldPlay] Don't play '<MEDIA>' from: <N>:<N>:<N> - to: <N>:<N>:<N>` | 4.463 | 2,84 % |
| 9 | `INFO [MENUBOARD_TPL] [INFO] ip received: <IP>` | 2.562 | 1,63 % |
| 10 | `INFO [MENUBOARD_TPL] [INFO] [StoreDataManager] TPL Mode: STORE ` | 2.562 | 1,63 % |
| 11 | `INFO [MENUBOARD_TPL] [INFO] [DataManager] SKUs found in configs:  <N>` | 2.562 | 1,63 % |
| 12 | `INFO [MENUBOARD_TPL] [INFO] [DataManager] Local Storage found: <N> prices \| <N> outages \| <N> combos` | 2.562 | 1,63 % |
| 13 | `INFO [MENUBOARD_TPL] [INFO] Metadata <JSON>` | 2.495 | 1,59 % |
| 14 | `INFO [Player] [Sync] PLAY Command received. Media "<MEDIA>"` | 2.494 | 1,59 % |
| 15-20 | 6 formas `INFO [MENUBOARD_TPL] [INFO] …` de 2.494 c/u: `[OffsetsManager] userAgent: <UA>`, `[OffsetsManager] userAgent WK: AppleWebKit/<N>`, `[OffsetsManager] platform: QM`, `[OffsetsManager] Found <N> offsets in file.`, `On Load TPL`, `Loaded fonts: ["<S>",…]` | 14.964 | 9,52 % |

Cobertura acumulada:

top 10 = 90.526 (**57,62 %**) · top 20 = 115.603 (**73,58 %**) · top 30 = 85,30 % · top 50 = 94,65 % · top 100 = 98,49 %

**La regla "~20 mensajes ≈ 60 % del volumen" se cumple y se supera**: con **10** formas ya se llega al 57,6 %, y con 20 al 73,6 %. En este corpus el ruido está **más** concentrado que lo que dice `06 §6.1`.

Nótese que las 7 primeras formas tienen todas ~11.570 líneas: son **siete latidos de 60 s** emitidos en el mismo tick (telemetría + políticas + input + countdown + heartbeat).

`[MENUBOARD_TPL]`: ~29.500 líneas totales ≈ **18,8 %** del corpus. Coincide con el ~17 % declarado en `06 §6.1`.

---

## 7. Eventos de ausencia (los que importan por faltar)

Cadencias medidas en ESTE corpus:

| Evento | Forma | Cadencia medida | Base |
|---|---|---|---|
| Telemetría | `[System Manager] CPU: <N>%. Used RAM: <N> Mb` | **60 s** (98,8 % de los deltas) | 11.595 deltas |
| Heartbeat servidor | `[Server Manager] Heartbeat received from server` | **60 s** (95,1 %) | 11.599 deltas |
| Política de display | `[Hardware Policies] Processing policies` + `Next Display State policy: NONE` | **60 s** (11.574 c/u) | conteo |
| Input | `[Input Manager] Remote Control Enabled` + `Panel Unlocked` | **60 s** (11.574 c/u) | conteo |
| Countdown | `[System Manager] Device will reboot in <N> minutes` | **60 s**, decreciente | conteo |
| Screenshots | `[Screenshots Manager] Tizen Screenshot API called` | **900 s** (93/94 deltas) | `20260904` |
| Rotación de medio | `[Player] [Sync] PLAY Command received. Media "<MEDIA>"` | p50 **240 s** (moda 240 s, secundaria 480 s) | 305 deltas |
| Vuelta de playlist | `[Player] Playlist ended.` | **480 s** (61/71 deltas) | `20260904` |
| Bloque de cluster | `===================SYNC GROUP INFO====================` | **esporádico**, 17 en 10 archivos — no periódico | conteo |

**`Next Display State policy` vale `NONE` en 11.574 de 11.574 casos.** No hay ni un `ON` ni un `OFF`, y **`[Screen Manager] Screen state :` no existe** en el corpus.

Huecos reales que un log sintético debería reproducir:
1. `DexPlayer-20260906-0.log` → `DexPlayer-20260907-0.log`: **~31,6 h** sin ninguna línea.
2. `DexPlayer-20260820-0.log`: **2.088 s (~35 min)** sin heartbeat, terminando a las `04:33:59.71`.
3. Ventana de reinicio de las 04:00: 1 muestra de telemetría perdida (delta 120 s máximo).

---

## 8. Contradicciones con la documentación de referencia

> Lo más valioso del reporte. Todo verificado por conteo sobre los 10 archivos.

### C1 — `03 §3.3`: el piso de RAM de Tizen (648 Mb) es falso para esta pantalla
Declarado: Tizen 648 – 885 Mb. Medido: **564,64 – 866,50 Mb**, con **1.465 muestras (12,6 %) por debajo de 648**.
`DexPlayer-20260904-0.log:57` (`815.25 Mb`) y el mínimo global `564.64 Mb`. Un umbral basado en 648 daría 1.465 falsos positivos.

### C2 — `03 §3.5`: el pico de CPU de 98 % post-arranque no ocurre
Declarado: "CPU 98 % en los primeros 30 s tras el arranque. Verificado en Tizen a +9,3 s del boot".
Medido: **máximo absoluto de CPU en todo el corpus = 54,00 %**, cero muestras > 90 %. La muestra post-handshake es `CPU: 54.00%. Used RAM: 654.02 Mb` (`DexPlayer-20260904-0.log:3227`). **La regla de "descartar los primeros 30 s" no tiene sustento aquí.**

### C3 — `05 §5.2/§5.3`: no hay timeouts, sólo `Network Error`
Declarado: dos causas, `timeout of 50000ms exceeded` (115) y `Network Error` (81); y 159 timeouts en total.
Medido: **145 fallas, 145 `Error: Network Error`, 0 timeouts**. `grep -c 'timeout of' = 0`. Cita: `DexPlayer-20260906-0.log:1668`.
También: `[Events Manager] Uploading events` **no existe** (0) y `[Screenshots Manager] Screenshot upload failed` **no existe** (0), pese a estar declarados con 138 y 135 ocurrencias.

### C4 — `06 §6.4`: los stack traces no son el 20 % de las líneas ERROR, son el **0 %**
Declarado: "Stack traces (`^\s+at\s`) … son el 20 % de las líneas ERROR".
Medido: **0 líneas** matchean `^\s+at\s`; **0 líneas** sin prefijo de timestamp. Todas las 157.100 líneas son atómicas. La regla de plegado del filtro mínimo (`06 §6.7` paso 2) es **inaplicable** a este corpus.

### C5 — `04 §4.2/§4.3/§4.4`: falta todo el ciclo de canal y la cascada de pantalla negra
Conteo = **0** para: `Clearing current playlist`, `Channel removed`, `preloadNextMedia`, `playNextMedia: Transitioning media`, `[Node] [Sync] Playlist stopped`, `Fail parsing JSON`, `[Global Error Handler]`, `Missing Content`, `Check integrity from heartbeat fail.`, `[Download Manager] Error downloading file`, `Cannot download image`.
El cambio de playlist real (`DexPlayer-20260908-0.log:3841-3852`) pasa por `STOP_TPL received` → `Processing State Sync` → `Playing Playlist` → `Clean media managers on unload` → `PLAYLIST ID` → `New Playlist received`. **Ninguna de esas 6 líneas figura en la secuencia de `04 §4.3`.**

### C6 — `06 §6.3`: el nombre de los mensajes de Input Manager está mal
Declarado: `^\[Input Manager\] (Remote Control|Panel) enabled$`.
Real: `[Input Manager] Remote Control Enabled` (**E** mayúscula, INFO) y `[Input Manager] Panel Unlocked` (**no** "Panel enabled", y nivel **SUCCESS**). 11.574 cada uno. `DexPlayer-20260904-0.log:19-20`. **El regex documentado no matchea ninguna línea de este corpus.**

### C7 — `07 §7.3`: `NEW` sí aparece, y además existe `DOWNLOAD`
Declarado: "Observados: `PLAYING` (105) y `READY` (4). La documentación previa incluía `NEW`, que nunca apareció."
Medido: `PLAYING` 47, **`NEW` 1** (`DexPlayer-20260907-0.log:84`), **`DOWNLOAD` 1** (`DexPlayer-20260908-0.log:12061`), `READY` 0. **`DOWNLOAD` no está en ninguna documentación.**

### C8 — `07 §7.3`: la proporción de `Schedule` está invertida
Declarado: vacío 105 filas, con id 4 filas.
Medido: **con id 48 filas, vacío 1 fila.** La forma dominante aquí es `Schedule: 238 [2026-08-27T14.46.45.703]`. Además el timestamp del `Schedule` usa **puntos** (`14.46.45.703`) y **no lleva `Z`**, a diferencia del ejemplo del doc (`[2025-09-19T…Z]`) y a diferencia del timestamp de `Playlist:` en la misma fila, que sí usa dos puntos y `Z` (`[2026-08-27T14:46:31.027Z]`). **Dos formatos distintos en la misma línea.**

### C9 — `07 §7.2`: no hay split-brain en este corpus
Declarado: "el 25 % de los snapshots del corpus mostró un cluster mal formado".
Medido: **17 de 18 líneas `Members:` tienen exactamente 1 `[Master]`**; la restante tiene 0 y es el arranque de `DexPlayer-20260907-0.log` antes de descubrir miembros. **0 % de split-brain.** Si el log sintético tiene que ejercitar el caso, hay que fabricarlo.

### C10 — `07 §7.4`: `Member <IP> is not active` y `Next candidates check` no existen
Conteo = 0 para ambos, pese a estar declarados con 60 casos y como patrón de referencia. Tampoco hay `[Player] [Sync] Error checking group content`, `Node server not Running` ni `NodeJs service is running`.

### C11 — `04 §4.2` / `07 §7.2`: el intervalo entre PLAY es de 4 minutos, no de 4,4–60 s
Declarado: "el p50 va de 4,4 s a 60 s según la pantalla".
Medido: **p50 = 240 s**, moda 240 s (184/305), segunda moda 480 s. Este player emite **0,25 PLAY por minuto**, no 4. Un umbral de "más de 4 PLAY por minuto" no sólo daría falso positivo en otras pantallas: acá **nunca** dispararía.

### C12 — El nivel DEBUG no está documentado en ningún archivo
16.589 líneas (**10,56 %**) son DEBUG y ningún doc de referencia lo menciona. Formas de mayor volumen (910 c/u): `[Player] hbMetadata: <JSON>`, `[Player] [State] Schedule fields …`, `[Player] [HB] Schedule fields …`, `[Download Manager] Downloading false`, `[Pending Downloads] Already checked pending downloads once, not checking again.`, `[System Manager] TimeOffset : <N>`, `[Player] [Sync] All group members have the same content`. Un parser que sólo conozca INFO/SUCCESS/WARNING/ERROR descarta una décima parte del log.

### C13 — Timestamps de época cero tras cada reinicio (no documentado)
**286 líneas con fecha `1969-12-31`**, en 9 de 10 archivos (hasta 109 en `DexPlayer-20260908-0.log`). Aparecen entre el `System will reboot` y la sincronización de reloj:
```
2026-09-08 13:36:51.68 INFO [Dex Player] System will reboot. Reason: SOFT_CLEAN_COMMAND
1969-12-31 21:00:17.66 INFO Dex Player 6.4.2408.2600
```
`DexPlayer-20260908-0.log:9691,9694`.
Consecuencias: **(a)** cualquier ordenamiento o delta por timestamp se rompe (produjo el delta espurio de 84.462 s en `DexPlayer-20260820-0.log:04:01:41`); **(b)** la regla de `06 §6.6` para `Dir failed` ("ruido si cae dentro de los 5 s de un arranque") **no se puede evaluar contra el reloj de pared**, porque el arranque y el `Dir failed` viven en 1969 mientras el resto del archivo vive en 2026. Los 6 `Dir failed` del corpus están todos en líneas `1969-12-31`.

### C14 — `05 §5.1`: `New Tags saved` no acompaña al handshake
Declarado como parte del bloque de handshake. Medido: **1 aparición en todo el corpus** (`DexPlayer-20260909-0.log:12658`) contra 17 handshakes. Además la línea del handshake declara `Machine Tags:` en el bloque de estado, con una lista **sin comillas y separada por coma-espacio**, que es otra forma distinta.

### C15 — Segunda fuente de CPU/RAM, contra `03 §3.1` ("es la única fuente")
`INFO CPU usage: 8.00%. Used RAM: 777.43 Mb` (`DexPlayer-20260904-0.log:12971`), sin prefijo de componente, 17 apariciones, dentro del bloque de estado que precede a `SYNC GROUP INFO`. El regex de `03 §3.1` no la matchea.

### C16 — `06 §6.3`: `Read operation completed for path` (el 10 % del volumen declarado) no existe
Conteo = 0. Tampoco existe `[Webos Storage Manager]` ni `File does not exist at path:`. Son específicos de webOS; este corpus es Tizen y usa `[Tizen Storage]`. **La tabla de ruido de `06 §6.1` no es portable entre plataformas** — 3 de sus 11 filas (storage reads, preload, playNext) tienen conteo 0 acá.

---

## 9. Mínimo que debe contener el log sintético

1. El **tick de 60 s de 7 líneas** (CPU/RAM, `Processing policies`, `Next Display State policy: NONE`, `Device will reboot in <N> minutes` decreciente, `Remote Control Enabled`, `Panel Unlocked`, `Heartbeat received from server`) — es el 52 % del volumen.
2. Un **arranque completo**: banner de 53 `=`, timestamps `1969-12-31`, `Dir failed playlists`/`schedules`, handshake `LICOK`, `Machine HB Interval: 60 seconds`, `No tenant code found` (WARNING), unión al multicast.
3. Un **bloque de estado + `SYNC GROUP INFO`**: delimitadores de 54 `=`, `Members:` con 1 `[Master]` y espacio final, 3 filas `PLAYING` con `Schedule: <id> [<ts con puntos>]`, una con `(MASTER)` precedida de dos espacios. Más la variante corta de 1 fila `NEW` / `Playlist: undefined []` / `Schedule:  []`.
4. Un **cambio de playlist** con la secuencia real de §3 (sin `Clearing current playlist`).
5. Una **racha de ~15 `Heartbeat Sync failed. Status: Error: Network Error`** con recuperación.
6. El **cluster de storage bloqueado**: `[Tizen Storage] The storage is locked…` (WARNING) alternando con `[Player] Checking playlist failed  Cannot read property 'message' of undefined` (ERROR, doble espacio), cerrando con `System will reboot. Reason: SOFT_CLEAN_COMMAND`.
7. **Líneas DEBUG** (~10 % del volumen) y **un hueco** de varias horas entre archivos.
8. **Ningún** stack trace, **ninguna** línea multilínea, **ningún** `Clearing current playlist`.
