# Corpus A — Caracterización de FORMATO (Dex Player / Tizen)

**Corpus:** 10 archivos, 157.100 líneas, ~14,4 MB.
- Carpeta A: `Logs-3057-ARROYO SECO 2 MBV 01/` → 7 archivos (20260904 … 20260910)
- Carpeta B: `Logs-3057-ARROYO SECO 2 MBV 01 (1)/` → 3 archivos (20260820 … 20260822)

**Enmascarado aplicado:** `<MACHINE>` (nombre de pantalla), `<IP>`, `<MAC>`, `<SERIAL>`,
`<SERVER>` (host del DexManager), `<GROUP>`, `<TENANT>`, `<MACHINE_ID>`, `<TAGS>`, `<PATH>`.
Todo lo demás (espaciado, corchetes, comillas, puntuación, espacios dobles y finales) es **verbatim**.

## 1. Formato de línea — CONFIRMADO al 100 %

Regex verificada:
```
^(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}:\d{2})\.(\d{2}) (INFO|SUCCESS|ERROR|DEBUG|WARNING) (.*)$
```

Medido sobre **los 10 archivos completos** (no solo 2), 157.100 líneas en total:
**0 líneas no matchean. 0,0000 % en cada uno de los 10 archivos.**
(Conteos por archivo en la tabla de §7.)

**No hay ejemplos de líneas que no matcheen: no existe ninguna.** Tampoco hay líneas en blanco (0),
ni líneas con `message` vacío (0), ni continuaciones multilínea.

Detalles del separador que hay que replicar exactamente:
- Exactamente **un** espacio entre fecha/hora, entre hora y nivel, y entre nivel y mensaje. No hay padding del nivel.
- Los centésimos son siempre 2 dígitos (`.00` … `.99`).
- Todos los archivos terminan con `\n` (último byte `0x0a`).

## 2. Niveles — distribución real

Por archivo (3 archivos, uno de cada régimen):

| Archivo | INFO | SUCCESS | DEBUG | ERROR | WARNING |
|---|---:|---:|---:|---:|---:|
| DexPlayer-20260904-0.log | 83,25 % | 16,75 % | 0 % | 0 % | 0,01 % |
| DexPlayer-20260820-0.log | 83,52 % | 16,45 % | 0 % | 0,02 % | 0,01 % |
| DexPlayer-20260909-0.log | 60,08 % | 11,81 % | 27,81 % | 0,29 % | 0,00 % |

Corpus completo (157.100 líneas) — real vs. lo que declara doc 01 §1.1:
INFO 116.913 / **74,42 %** (doc 92,1 %) · SUCCESS 23.360 / **14,87 %** (doc 6,2 %) ·
DEBUG 16.589 / **10,56 %** (doc 0,71 %) · ERROR 172 / **0,11 %** (doc 0,84 %) ·
WARNING 66 / **0,04 %** (doc 0,12 %).

Los 5 niveles existen. Es `WARNING`, no `WARN` — confirmado.
**El reparto porcentual del doc no se reproduce en este corpus** (ver §9).

**DEBUG no es "solo builds de QA":** aparece únicamente en 20260909 (6.667) y 20260910 (9.922),
y arranca en `DexPlayer-20260909-0.log:12653` (`2026-09-09 17:52:44.08`), **6 centésimos antes** de
`DexPlayer-20260909-0.log:12658`, que es la única línea `New Tags saved` del corpus y la que incluye
el tag `"Debug"`. Es decir: **DEBUG se activa por tag remoto en caliente, sin reinicio.**

## 3. Componentes

Top 15 por volumen (corpus completo, prefijo `[A]` o `[A] [B]`):

| # | Componente | Líneas |
|---:|---|---:|
| 1 | `[MENUBOARD_TPL] [INFO]` | 41.981 |
| 2 | `[System Manager]` | 30.495 |
| 3 | `[Input Manager]` | 23.217 |
| 4 | `[Hardware Policies]` | 23.165 |
| 5 | `[Server Manager]` | 11.894 |
| 6 | `[Node] [Sync]` | 8.145 |
| 7 | `[Player]` | 5.430 |
| 8 | `[Player] [Sync]` | 3.700 |
| 9 | `[Screenshots Manager]` | 3.067 |
| 10 | `[Pending Downloads]` | 932 |
| 11 | `[Download Manager]` | 911 |
| 12 | `[Player] [State]` | 910 |
| 13 | `[Player] [HB]` | 910 |
| 14 | *(sin componente)* | 765 |
| 15 | `[ShouldPlay]` | 525 |

Cola: `[Screen Manager]` 436, `[Tizen App]` 180, `[Logs Manager]` 136, `[BackgroundManager]` 68,
`[Node Server Manager]` 54, `[Main]` 54, `[Schedule Manager]` 24, `[Dex Player]` 18,
`[Input Source]` 17, `[Tizen Storage]` 15, `[Machine Files Reporter]` 14, `[Events Manager]` 12,
`[User Settings]` 6, `[Player] [allToPlaying]` 6, `[Media Library]` 4,
`[Sync Channel Manager] [Sync]` 3, `[Playlist Manager]` 3, `[Storage Manager]` 2,
`[Sync Channel Manager]` 1.

**¿Componentes de dos niveles?** Sí: `[Node] [Sync]`, `[Player] [Sync]`, `[Player] [State]`,
`[Player] [HB]`, `[Player] [allToPlaying]`, `[Sync Channel Manager] [Sync]`, `[MENUBOARD_TPL] [INFO]`.

**Hay TRES niveles de corchete** (el doc solo prevé dos):

| Prefijo de 3 corchetes | Líneas |
|---|---:|
| `[MENUBOARD_TPL] [INFO] [OffsetsManager]` | 9.976 |
| `[MENUBOARD_TPL] [INFO] [DataManager]` | 5.490 |
| `[Node] [Sync] [SyncShouldPlay]` | 4.463 |
| `[MENUBOARD_TPL] [INFO] [StoreDataManager]` | 3.657 |

**Trampa de parsing crítica:** el sub-componente de `[MENUBOARD_TPL]` es literalmente `[INFO]`,
o sea un **token con nombre de nivel dentro del mensaje**. Cualquier heurística que busque el nivel
por texto (y no por posición) va a duplicar el conteo de INFO en ~42.000 líneas.

**Líneas sin componente:** 765 (0,487 % del corpus). No empiezan con `[`. Tres formas
(máx. 3 ejemplos, verbatim, enmascaradas):

```
2026-09-04 00:00:00.25 INFO Next period: 1788490800000 (Fri Sep 04 2026 00:00:00 GMT-0300) - 1788508800000 (Fri Sep 04 2026 05:00:00 GMT-0300) ID: 6060
2026-09-04 18:04:51.19 INFO <IP> | PLAYING | Playlist: 6065 [2026-08-27T14:46:31.027Z] | Schedule: 238 [2026-08-27T14.46.45.703] | Playlist T…
2026-09-04 18:04:51.08 INFO Player Version: 6.4.2408.2600
```
(cita: `DexPlayer-20260904-0.log:6`, `:12972`, `:12958`)

## 4. Banner de arranque — la distinción 53 / 54 `=` EXISTE y es exacta

Conteo exacto sobre el corpus completo (aplicado al `message`, después del nivel):

| Forma | Líneas |
|---|---:|
| `^={53}$` (banner de arranque) | **36** |
| `^={54}$` | **53** |
| `^={19}SYNC GROUP INFO={20}$` (largo total 54) | **17** |

- `36 / 2 = 18` = exactamente la cantidad de `^Dex Player [\d.]+$` del corpus. **La regla ÷2 se confirma.**
- Se confirma por archivo, sin excepción: `banner53 == 2 × dexplayer` en los 10 archivos.

**Corrección al doc 01 §1.5:** las 53 líneas de 54 `=` **no** son solo del bloque `SYNC GROUP INFO`.
Se descomponen en `2×18 = 36` (apertura + cierre de un **bloque de info de dispositivo**, sin título)
+ `17` (cierre del bloque `SYNC GROUP INFO`, cuya **apertura lleva título embebido** y por eso no
matchea `^={54}$`). Ver §9.

### Secuencia VERBATIM de un arranque

Fuente: `DexPlayer-20260904-0.log:3195-3210` (líneas 1-16 del arranque).
Nótese que el banner arranca con timestamp de época (ver §8).

```
1969-12-31 21:00:18.20 INFO =====================================================
1969-12-31 21:00:18.21 INFO Dex Player 6.4.2408.2600
1969-12-31 21:00:18.21 INFO =====================================================
1969-12-31 21:00:18.21 INFO [Main] Initializing Dex Player. Platform "tizen"
1969-12-31 21:00:18.21 INFO Device UserAgent: Mozilla/5.0 (SMART-TV; LINUX; Tizen 4.0) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 TV Safari/537.36
1969-12-31 21:00:27.05 INFO [Main] Player files checked
1969-12-31 21:00:29.27 INFO [Node Server Manager] Starting node as service
1969-12-31 21:00:29.27 INFO [Node Server Manager] Node server file: server2018.js
1969-12-31 21:00:29.85 INFO [Tizen App] Device time: Wed Dec 31 1969 21:00:29 -03:00
1969-12-31 21:00:29.86 INFO [Tizen App] Device time with timezone applied: Wed Dec 31 1969 21:00:29 -03:00
1969-12-31 21:00:29.86 INFO [Tizen App] Waiting for system date time
1969-12-31 21:00:29.89 SUCCESS [Node Server Manager] Node server started
1969-12-31 21:00:30.57 INFO [Main] Player playlists and schedules files format checked
1969-12-31 21:00:31.86 INFO [Tizen App] Device time: Wed Dec 31 1969 21:00:31 -03:00
1969-12-31 21:00:31.86 INFO [Tizen App] Device time with timezone applied: Wed Dec 31 1969 21:00:31 -03:00
1969-12-31 21:00:31.86 INFO [Tizen App] Waiting for system date time
```

Continuación del mismo arranque, ya con reloj sincronizado (`DexPlayer-20260904-0.log:3211-3234`):
`[Tizen App] Device time:` con año real → `[System Manager] Server time offset: 1042 milliseconds. Time zone: -3  hs Screen Time zone:  -03:00`
→ `[Screenshots Manager] Started with 15 minutes interval` → `[Server Manager] Fetching dex config on <PATH>`
→ `[Server Manager] Sending Handshake` → `[System Manager] CPU: 54.00%. Used RAM: 654.02 Mb`
→ `SUCCESS [Server Manager] Handshake received. Code "LICOK"` → `Machine:` → `Machine HB Interval:`.

Nota de formato: `Time zone: -3  hs` y `Screen Time zone:  -03:00` llevan **doble espacio**.

### Bloque de info de dispositivo (54 `=`) — `DexPlayer-20260904-0.log:12956-12981` (recortado)

```
2026-09-04 18:04:51.07 INFO ======================================================
2026-09-04 18:04:51.08 INFO Player Version: 6.4.2408.2600
2026-09-04 18:04:51.09 INFO Serial Number: <SERIAL>
2026-09-04 18:04:51.09 INFO Webview Version: 
2026-09-04 18:04:51.09 INFO Server: https://<SERVER>:443
… (Firmware Version, Android Version, Machine time zone offset, CPU usage, Free space, Time: …)
2026-09-04 18:04:51.09 INFO Client IP: <IP>
2026-09-04 18:04:51.10 INFO Machine ID: <MACHINE_ID>
2026-09-04 18:04:51.11 INFO Machine Tags: <TAGS>
2026-09-04 18:04:51.11 INFO Tenant ID: 3. Tenant Name: <TENANT>
2026-09-04 18:04:51.12 INFO Machine Sync ID:  1
2026-09-04 18:04:51.12 INFO Multicast IP:  <IP>
2026-09-04 18:04:51.12 INFO Device will reboot at: 2021-04-30T04:00:00
2026-09-04 18:04:51.12 INFO ======================================================
```

Rarezas a replicar: `Webview Version: ` termina en espacio; `Machine Sync ID:  1` y
`Multicast IP:  <IP>` llevan **dos espacios** después de los dos puntos.
Inmediatamente después viene la línea `[Player] [Sync] Version: … - Group: … - Members: …`
y luego el bloque `SYNC GROUP INFO`:

```
2026-09-04 18:04:51.19 INFO ===================SYNC GROUP INFO====================
2026-09-04 18:04:51.19 INFO <IP> | PLAYING | Playlist: 6065 [2026-08-27T14:46:31.027Z] | Schedule: 238 [2026-08-27T14.46.45.703] | Playlist T…
2026-09-04 18:04:51.20 INFO ======================================================
```

## 5. Identidad — líneas verbatim (enmascaradas)

| Dato | Línea verbatim | Cita |
|---|---|---|
| Machine | `2026-09-04 04:00:45.58 INFO [Server Manager] Machine: <MACHINE>` | `DexPlayer-20260904-0.log:3231` |
| Hostname | `2026-09-04 04:00:43.21 INFO [Server Manager] Hostname: <IP> <MAC>` | `DexPlayer-20260904-0.log:3228` |
| Platform | `1969-12-31 21:00:18.21 INFO [Main] Initializing Dex Player. Platform "tizen"` | `DexPlayer-20260904-0.log:3198` |
| Versión player | `1969-12-31 21:00:18.21 INFO Dex Player 6.4.2408.2600` | `DexPlayer-20260904-0.log:3196` |
| HB Interval | `2026-09-04 04:00:45.58 INFO [Server Manager] Machine HB Interval: 60 seconds` | `DexPlayer-20260904-0.log:3232` |
| New Tags saved | `2026-09-09 17:52:44.14 INFO [Server Manager] New Tags saved ["<TAG>","<TAG>","Debug","<TAG>","<TAG>","<TAG>","<TAG>","SYNC01","<TAG>"]` | `DexPlayer-20260909-0.log:12658` |
| Group / Members | `2026-09-04 18:04:51.14 INFO [Player] [Sync] Version: 1.6.21 - Group: <GROUP> - Members: <IP> [Master] <IP> <IP> ` | `DexPlayer-20260904-0.log:12981` |

Notas de forma: `New Tags saved [...]` es un array JSON **sin espacio tras la coma**.
La línea `Group: … - Members: …` **termina en espacio**; los miembros van separados por espacio
y el master lleva ` [Master]` justo después de su IP (3 variantes de orden en 18 ocurrencias).
`Machine:` aparece 17 veces contra 18 `Dex Player <ver>` → **un arranque no llegó a handshake**.
`Device UserAgent:` 18, `Player files checked` 18, `Handshake received` 17.

## 6. ¿Las dos carpetas son la misma pantalla? — SÍ, con certeza

Evidencia por contenido, no por nombre de carpeta:

`Machine:`, `Hostname:` (IP + MAC), `Serial Number:`, `Machine ID:` y `Client IP:` tienen
**un único valor en todo el corpus y es el mismo en las dos carpetas**. Plataforma `tizen` y
versión `6.4.2408.2600` idénticas. Ninguno de esos campos tiene un segundo valor en ningún archivo.

Citas: `DexPlayer-20260904-0.log:3231` y `DexPlayer-20260820-0.log:4442` (`Machine Name:`),
`DexPlayer-20260820-0.log` bloque de las 18:01:46.

Los rangos de fechas son **disjuntos** (agosto 20-22 vs septiembre 04-10), así que no hay
solapamiento de líneas. **El `(1)` acá marca una segunda descarga de la MISMA pantalla en otro
rango de fechas, no otra pantalla** (ver contradicción C-6 en §9).

## 7. Cobertura temporal por archivo

| Archivo | Líneas | Primera línea | Última línea | Arranques (`^Dex Player [\d.]+$`) |
|---|---:|---|---|---:|
| DexPlayer-20260904-0.log | 17.322 | `2026-09-04 00:00:00.00 INFO` | `2026-09-04 23:59:46.15 SUCCESS` | 1 |
| DexPlayer-20260905-0.log | 17.588 | `2026-09-05 00:00:00.00 INFO` | `2026-09-05 23:59:25.57 SUCCESS` | 4 |
| DexPlayer-20260906-0.log | 10.950 | `2026-09-06 00:00:00.00 INFO` | `2026-09-06 14:56:45.25 SUCCESS` | 1 |
| DexPlayer-20260907-0.log | 1.107 | `2026-09-07 22:33:36.72 INFO` | `2026-09-07 23:59:01.09 SUCCESS` | 1 |
| DexPlayer-20260908-0.log | 16.995 | `2026-09-07 23:59:58.63 INFO` | `2026-09-08 23:59:19.59 INFO` | 4 |
| DexPlayer-20260909-0.log | 23.970 | `2026-09-09 00:00:00.00 INFO` | `2026-09-09 23:59:43.62 DEBUG` | 1 |
| DexPlayer-20260910-0.log | 16.750 | `2026-09-10 00:00:00.00 DEBUG` | `2026-09-10 09:01:48.77 INFO` | 1 |
| DexPlayer-20260820-0.log | 17.715 | `2026-08-19 23:59:56.93 INFO` | `2026-08-20 23:59:40.87 SUCCESS` | 2 |
| DexPlayer-20260821-0.log | 17.332 | `2026-08-21 00:00:00.00 INFO` | `2026-08-21 23:59:48.46 SUCCESS` | 1 |
| DexPlayer-20260822-0.log | 17.371 | `2026-08-22 00:00:00.00 INFO` | `2026-08-22 23:59:22.51 SUCCESS` | 2 |
| **TOTAL** | **157.100** | | | **18** |

Observaciones:
- **El nombre del archivo no delimita el día exactamente**: `20260908` empieza el `2026-09-07 23:59:58`
  y `20260820` empieza el `2026-08-19 23:59:56`. Hay spill de ~1-4 segundos del día anterior.
- **Hueco de cobertura real**: entre `20260906` (fin 14:56:45) y `20260907` (inicio 22:33:36) faltan
  ~31,6 h. `20260907` es el único archivo chico (1.107 líneas) y arranca con el banner en la línea 1.
- El nombre de archivo tiene prefijo `DexPlayer-` (`DexPlayer-YYYYMMDD-N.log`), no la forma `YYYYMMDD-N.log` del doc.

## 8. Pendiente X-11 (timestamps de época) — CONFIRMADO, 286 líneas

| Prefijo | Líneas |
|---|---:|
| `1969-12-31` | **286** |
| `1970-…` | **0** |

`1969-12-31 21:00:xx` = epoch 0 visto en `-03:00`. Distribución por archivo:
20260904 16 · 20260905 16 · 20260906 16 · 20260907 **0** · 20260908 **109** ·
20260909 25 · 20260910 25 · 20260820 41 · 20260821 19 · 20260822 19.

**Sí aparecen cerca de un arranque — de hecho, SIEMPRE dentro del arranque.** Verificado
programáticamente: no hay ninguna línea `1969-` a más de 200 líneas del banner más cercano
(las únicas "lejanas" son la propia primera línea `=` del banner, que precede a `Dex Player`).
**13 de los 18 arranques** tienen el par banner + `Dex Player <ver>` estampado en 1969;
los otros 5 (`20260905:2533`, `20260905:9014`, `20260905:10926`, `20260907:2`, `20260822:12714`)
tienen timestamp real.

Tres ejemplos con contexto (±2 líneas):

**(a) `DexPlayer-20260908-0.log:2877-2881`** — reinicio programado:
```
2026-09-08 04:00:00.00 INFO [Dex Player] System will reboot. Reason: Scheduled reboot
2026-09-08 04:00:00.06 INFO [Input Source] clear() success.
1969-12-31 21:00:17.63 INFO =====================================================
1969-12-31 21:00:17.64 INFO Dex Player 6.4.2408.2600
1969-12-31 21:00:17.64 INFO =====================================================
```

**(b) `DexPlayer-20260820-0.log:4412-4416`** — reinicio por cambio de offset horario:
```
2026-08-20 04:00:58.08 INFO [Dex Player] System will reboot. Reason: TIME_OFFSET_CHANGED
2026-08-20 04:00:58.10 INFO [Input Source] clear() success.
1969-12-31 21:00:18.73 INFO =====================================================
1969-12-31 21:00:18.74 INFO Dex Player 6.4.2408.2600
1969-12-31 21:00:18.74 INFO =====================================================
```

**(c) `DexPlayer-20260904-0.log:3208-3212`** — salida de la ventana de época:
```
1969-12-31 21:00:31.86 INFO [Tizen App] Waiting for system date time
2026-09-04 04:00:38.86 INFO [Tizen App] Device time: Fri Sep 04 2026 04:00:38 -03:00
2026-09-04 04:00:38.87 INFO [Tizen App] Device time with timezone applied: Fri Sep 04 2026 04:00:38 -03:00
```

**Mecanismo (verificado, no inferido):** en Tizen el player arranca antes de que el sistema tenga
hora NTP. La ventana de época dura desde el banner hasta la primera
`[Tizen App] Device time:` con año real, y se cierra con `[Tizen App] Waiting for system date time`
repetida. Duración observada: entre ~14 y ~31 segundos de reloj interno.

**Implicancia para el log sintético:** el bloque de época es **la forma normal del arranque en
este corpus**, no una anomalía rara. Hay que replicarlo.

## 9. Contradicciones con `01-LECTURA-BASE.md` / `02-GENERAL-sesiones-reinicios.md`

**C-1 — Distribución de niveles muy distinta.** Doc 01 §1.1 declara INFO 92,1 % / SUCCESS 6,2 % /
ERROR 0,84 % / DEBUG 0,71 % / WARNING 0,12 %. Acá: INFO 74,42 % / SUCCESS 14,87 % / DEBUG 10,56 % /
ERROR 0,11 % / WARNING 0,04 %. SUCCESS está 2,4× por encima y DEBUG 15× por encima.
Los porcentajes del doc no son universales: dependen de la plataforma y de los tags activos.

**C-2 — "DEBUG aparece solo en builds de QA" es falso.** Doc 01 §1.1. En este corpus DEBUG se
enciende en producción por tag remoto: `DexPlayer-20260909-0.log:12653` (primer DEBUG,
`17:52:44.08`) vs `DexPlayer-20260909-0.log:12658` (`New Tags saved [… "Debug" …]`, `17:52:44.14`).
Mismo binario, mismo arranque, sin reinicio.

**C-3 — Los componentes tienen hasta TRES niveles de corchete.** Doc 01 §1.1 da la regex
`^\[(componente)\](?:\s*\[(sub)\])?\s*(texto)$`, que solo captura dos. Acá hay 23.586 líneas con tres:
`[MENUBOARD_TPL] [INFO] [OffsetsManager]` (9.976), `[MENUBOARD_TPL] [INFO] [DataManager]` (5.490),
`[Node] [Sync] [SyncShouldPlay]` (4.463), `[MENUBOARD_TPL] [INFO] [StoreDataManager]` (3.657).
Cita: `DexPlayer-20260904-0.log:21` (`[MENUBOARD_TPL] [INFO] [OffsetsManager] userAgent: …`).

**C-4 — El sub-componente de MENUBOARD es `[INFO]`, no `[DataManager]`.** Doc 01 §1.1 nombra
`[MENUBOARD_TPL] [DataManager]`; acá el segundo corchete es **siempre** `[INFO]` (41.981/41.981) y
`[DataManager]` es el tercero. Un token con nombre de nivel dentro del mensaje: cualquier parser
que busque el nivel por texto en vez de por posición se rompe acá.

**C-5 — Las líneas de 54 `=` no son solo del bloque sync.** Doc 01 §1.5 dice que `^={54}$` es
"apertura o cierre del bloque `SYNC GROUP INFO`". En este corpus las 53 líneas `^={54}$` son
36 de apertura/cierre de un bloque de **info de dispositivo** (`Player Version:`, `Firmware Version:`,
`Machine Tags:` …) + 17 de **cierre** del bloque sync. La **apertura** del bloque sync es
`===================SYNC GROUP INFO====================` (54 caracteres, pero con título embebido),
que no matchea `^={54}$`. Cita: `DexPlayer-20260904-0.log:12956` (info dispositivo) vs
`DexPlayer-20260904-0.log:12982` (apertura sync). La regla ÷2 del banner de 53 `=` **sí se confirma**.

**C-6 — El `(1)` acá es del directorio y es la MISMA pantalla.** Doc 01 §1.6 describe pares de
archivos que son "pantallas distintas del mismo grupo y del mismo día". Acá el `(1)` cuelga de la
**carpeta** y sus 3 archivos son la misma pantalla en un rango de fechas **disjunto**. La regla
"no deduplicar" se sostiene; la explicación del doc no aplica a este caso.

**C-7 — Ningún stack trace.** Doc 01 §1.5 (Trampa 2) afirma que las continuaciones `^\s+at\s` son
"el 20 % de todas las líneas ERROR". En este corpus hay **0** líneas de ese tipo sobre 172 ERROR.
Es un fenómeno de webOS, no de Tizen.

**C-8 — Componentes documentados que NO existen acá:** `[Global Error Handler]` (0),
`[Webos Storage Manager]` (0, esperable), `[Channel Manager]` (0; existe `[Sync Channel Manager]`, 4).
El "recorrido de 5 minutos" (doc 01 §1.4) falla en 2 de 7 pasos: `Clearing current playlist` (0)
y `NodeJs service is running` (0).

**C-9 — `NodeJs service is running` / `Node server not Running` no existen.** Doc 02 §2.6 los da
como patrones de referencia. Acá el equivalente es
`[Player] Dex Sync v1.6.21 is Running` (`DexPlayer-20260904-0.log:3247`) y
`SUCCESS [Node Server Manager] Node server started` (`DexPlayer-20260904-0.log:3206`).

**C-10 — El countdown de reinicio es 15× más frecuente de lo documentado.** Doc 02 §2.3 dice
"749 líneas en el corpus". Acá `Device will reboot in N minutes` tiene **11.574** líneas
(7,4 % de todo el corpus, ~1 por minuto). El diseño del log sintético tiene que reflejar esa densidad.

**C-11 — `All tasks were finished` es prácticamente inexistente.** Doc 02 §2.4/§2.6 lo propone como
señal de cierre ordenado. Acá aparece **1 vez** en 157.100 líneas, así que no sirve para distinguir
programado vs inesperado en este corpus. Lo que sí sirve y el doc no menciona:
`[Dex Player] System will reboot. Reason: <RAZON>` (razones observadas: `Scheduled reboot`,
`TIME_OFFSET_CHANGED`) y `[Dex Player] Player will reload in 2 seconds. Reason: INPUT_COMMAND`.

**C-12 — Los saltos hacia atrás son 14, no 3, y son de ~56 años.** Doc 01 §1.3 dice
"solo hubo 3 saltos hacia atrás; el mayor fue de ~2 horas". Acá hay **14** saltos hacia atrás:
13 de ellos son la entrada a la ventana de época (2026 → 1969, ~56 años) y 1 es una línea suelta
de un mes atrás: `DexPlayer-20260820-0.log:4406` →
`2026-07-20 04:33:59.71 SUCCESS [Server Manager] Heartbeat received from server`,
intercalada entre dos líneas de `2026-08-20 04:00:42.83` y `2026-08-20 04:00:56.05`. Es **una sola
línea** con fecha vieja (heartbeat con reloj todavía inconsistente), no un reinicio.

**C-13 — No es contradicción, pero importa:** el corpus es 100 % Tizen con una sola versión
(`6.4.2408.2600`, sí listada en doc 02 §2.1). No ejercita ningún camino webOS del doc.

**C-14 — Nombre de archivo:** doc 01 §1.2 lista dos familias; acá hay una tercera,
`DexPlayer-YYYYMMDD-N.log`, con prefijo fijo.

**No verificado:** qué dispara el bloque de info de dispositivo (54 `=`). Hay 18 bloques y 18 arranques,
pero al menos uno (`DexPlayer-20260904-0.log:12956`, 18:04:51) **no** está en un arranque (el arranque
de ese archivo fue a las 04:00). No tengo evidencia suficiente para afirmar la causa.

## 10. Encoding y rarezas de formato

- **BOM:** no. Los 10 archivos empiezan con `32 30 32` (`"202"`).
- **Finales de línea:** LF puro. 0 apariciones de `\r`.
- **Newline final:** presente en los 10 (último byte `0x0a`).
- **No-ASCII:** 0 en los 10 archivos (`grep -c '[^ -~]'` = 0). Todo ASCII imprimible.
- **Líneas en blanco:** 0. **Líneas con espacio final:** 2.631 (1,7 %).

**Máximo de caracteres por línea:** 325 en 8 de los 10 archivos (904, 905, 906, 907, 908,
820, 821, 822). **5.681** en `DexPlayer-20260909-0.log` y **4.865** en `DexPlayer-20260910-0.log`
— los dos archivos con DEBUG activo.

El techo de 325 es sospechosamente estable: sugiere **truncado del player a 325 caracteres**
(no verificado como truncado explícito, pero 8 de 10 archivos dan exactamente el mismo máximo).
Las líneas largas de 20260909/20260910 son todas DEBUG con JSON crudo embebido, p. ej.
`DexPlayer-20260909-0.log` a las `17:53:47.21`:
`DEBUG [Machine Files Reporter] this.machineFilesArray Updated [{"MachineFileId":…}]` (5.681 chars).
**Es decir: el modo Debug también rompe el techo de 325.** Cualquier parser o viewer que asuma
líneas cortas se va a encontrar con líneas 17× más largas cuando el tag `Debug` esté activo.

**Espacios dobles internos** (parte del formato, hay que replicarlos literalmente):
`Machine Sync ID:  1`, `Multicast IP:  <IP>`, `Time zone: -3  hs`, `Screen Time zone:  -03:00`,
`[Player] Checking playlist failed  Cannot read property 'message' of undefined`.
