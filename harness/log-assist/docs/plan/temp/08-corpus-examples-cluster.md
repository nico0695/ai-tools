# Examples B — Cluster, pantallas y casos con problema conocido

Corpus: 14 archivos en `<PATH>/logs_examples/`, 178.415 líneas.
Todo número de acá sale de un comando; los comandos están al pie de cada sección.
Enmascarado: `<MACHINE>` nombre de pantalla, `<GROUP>` grupo sync, `<IPn>` último octeto real, `<MAC>`, `<PATH>`.

`<IPn>` conserva el último octeto real: `<IP1>`…`<IP7>` = grupo A (.101–.107), `<IP101>`…`<IP171>`
= grupo B, `<IP10>`…`<IP13>` = C, `<IP73>`/`<IP147>` = D, `<IP24>`…`<IP207>` = E.

---

## 1. Topología de pantallas

**Hallazgo de método (no está en la doc):** en webOS no hay línea `Hostname:`, así que la IP
propia no se escribe nunca. Pero `New member discovered:` **nunca lista la IP propia**: la
diferencia `Members:` − `New member discovered:` da un candidato único en 11 de 14 archivos.
Verificado contra los 3 archivos Tizen que sí traen `Hostname:` — coincide en los 3.

| Archivo | `Machine:` | Plataforma | Grupo | IP propia | ¿`[Master]` en su IP? | `PLAY burst` |
|---|---|---|---|---|---|---:|
| `20260219-0.log` | `<MACHINE-A1>` (…:25984) | webos | `<GROUP-A>` | `<IP7>` | No (…:32891) | 0 |
| `20260222-0.log` | `<MACHINE-A1>` (…:431) | webos | **`undefined`** (…:133) | `<IP7>` (inferida) | — sin grupo | 0 |
| `20260220-0.log` | `<MACHINE-A2>` (…:14985) | webos | `<GROUP-A>` | `<IP6>` | No (…:19764) | **157** |
| `20260222-0 (1).log` | `<MACHINE-A2>` (…:46) | webos | `<GROUP-A>` | `<IP6>` | No (…:3670) | 0 |
| `20260223-0.log` | `<MACHINE-B2>` (…:51) | webos | `<GROUP-B>` | `<IP102>` | No (…:2467) | 0 |
| `20260223-0 (1).log` | `<MACHINE-B3>` (…:51) | webos | `<GROUP-B>` | `<IP105>` | No (…:2471) | 0 |
| `PJ - 6DIC 2.log` | `<MACHINE-C2>` (…:55) | webos | `<GROUP-C>` | `<IP11>` | No (…:3020) | 0 |
| `PJ - 6DIC 3.log` | `<MACHINE-C3>` (…:53) | webos | `<GROUP-C>` | `<IP12>` | No (…:3247) | 0 |
| `PJ - 6DIC 4.log` | `<MACHINE-C4>` (…:55) | webos | `<GROUP-C>` | `<IP13>` | No (…:3009) | 0 |
| `QMC32 QA 1.log` | `<MACHINE-D1>` (…:32) | tizen | `<GROUP-D>` | `<IP73>` (`Hostname:` …:31) | **Sí** (…:803) | **57** |
| `QMC32 QA 2.log` | `<IP147> <MAC>` (…:32) | tizen | `<GROUP-D>` | `<IP147>` | No (…:1139) | 0 |
| `TimHortonsTransistmicaP1.log` | `<MACHINE-E1>` (…:36) | tizen | `<GROUP-E>` (sin línea `Members:`) | `<IP26>` (`Hostname:`) | — | 0 |
| `TimHortonsTransistmicaP3.log` | `<MACHINE-E3>` (…:35) | tizen | `<GROUP-E>` | `<IP207>` (`Hostname:`) | No (…:203) | 0 |
| `TimHortonsTransistmicaP4 MASTER.log` | `<MACHINE-E4>` (…:36) | tizen | `<GROUP-E>` (sin línea `Members:`) | `<IP24>` (`Hostname:`) | Sí, por evidencia externa* | **479** |

\* `P4` no emite ninguna línea `Members:` propia, pero su IP aparece como `[Master]` en
`TimHortonsTransistmicaP3.log:203` y emite 479 `PLAY burst`. Es el master del grupo E.

**Anomalía de identidad:** en `QMC32 QA 2.log:32` el valor de `Machine:` **no es un nombre sino
`<IP> <MAC>`** — el mismo texto de `Hostname:`. Un parser que asuma "Machine = nombre legible"
produce una fila basura acá. Es 1 de 14 archivos.

### Mapa

- **Misma pantalla, dos archivos:** `20260219-0.log` + `20260222-0.log` (`<MACHINE-A1>`);
  `20260220-0.log` + `20260222-0 (1).log` (`<MACHINE-A2>`).
- **Pantallas distintas del mismo grupo:** grupo A, 7 miembros / 2 con log (`<MACHINE-A1>`,
  `<MACHINE-A2>`); grupo B, 6 / 2 (`<MACHINE-B2>`, `<MACHINE-B3>`, mismo día); grupo C, 4 / 3
  (`PJ - 6DIC 2/3/4`, mismo día, falta el log del master); grupo D, 2 / 2 (`QMC32 QA 1/2`,
  **grupo completo**); grupo E, 5 / 3 (`P1`, `P3`, `P4`, mismo día).
- **Sueltas:** ninguna. Los 14 archivos pertenecen a algún grupo sync.
- **Confirmado de `01 §1.6`:** los pares `(1)` son pantallas distintas, no duplicados.

```sh
for f in *.log; do echo "== $f"; grep -o 'Machine: .*' "$f" | sort -u; grep -o ' - Group: .*' "$f" | sort -u; done
comm -23 <(grep -m1 -o 'Members: .*' "$f" | grep -oE '([0-9]{1,3}\.){3}[0-9]{1,3}' | sort -u) \
         <(grep -o 'New member discovered: [0-9.]*' "$f" | awk '{print $4}' | sort -u)
```
## 2. Split-brain — `07 §7.2` es reproducible al dígito

24 líneas `Members:` en el corpus. Distribución de `[Master]`:

**0 masters → 1 línea · 1 master → 18 · 2 masters → 2 · 3 masters → 3.** Las cuatro celdas
coinciden con la tabla de `07 §7.2`. 6 de 24 = **25 % de snapshots mal formados**: reproducible.

Las 6 líneas anómalas: `20260222-0.log:133` (0 masters), `20260220-0.log:19764` y `:34398`
(2 masters), `20260219-0.log:32891` y `:33200`, `20260222-0 (1).log:3670` (3 masters).

### Bloque verbatim — 3 masters · cita `20260219-0.log:32890-32901`

```
2026-02-19 10:54:49.79 INFO ======================================================
2026-02-19 10:54:49.81 INFO [Player] [Sync] Version: 1.9.1 - Group: <GROUP-A> - Members: <IP1> [Master] <IP7> <IP6> <IP3> <IP4> <IP5> [Master] <IP2> [Master] 
2026-02-19 10:54:51.73 INFO ===================SYNC GROUP INFO====================
2026-02-19 10:54:51.73 INFO <IP1> | PLAYING | Playlist: 67161 [2026-02-16T17:05:57.217Z] | Schedule:  [] | Playlist To Change: [67161_2026-02-12T14.42.26.450.json,67161_2026-02-12T14.43.00.867.json,67161_2026-02-12T14.43.43.763.json,67161_2026-02-16T17.05.57.217.json]  (MASTER)
2026-02-19 10:54:51.73 INFO <IP7> | PLAYING | Playlist: 67161 [2026-02-16T17:05:57.217Z] | Schedule:  [] | Playlist To Change: [67161_2026-02-12T14.42.26.450.json,67161_2026-02-12T14.43.00.867.json,67161_2026-02-12T14.43.43.763.json,67161_2026-02-16T17.05.57.217.json] 
2026-02-19 10:54:51.73 INFO <IP6> | PLAYING | Playlist: 67161 [2026-02-16T17:05:57.217Z] | Schedule:  [] | Playlist To Change: [67161_2026-02-10T20.54.51.390.json,67161_2026-02-12T14.42.26.450.json,67161_2026-02-12T14.43.43.763.json,67161_2026-02-16T17.05.57.217.json] 
2026-02-19 10:54:51.73 INFO <IP3> | PLAYING | Playlist: 67161 [2026-02-16T17:05:57.217Z] | Schedule:  [] | Playlist To Change: [67161_2026-02-10T20.54.51.390.json,67161_2026-02-12T14.42.26.450.json,67161_2026-02-12T14.43.43.763.json,67161_2026-02-16T17.05.57.217.json] 
2026-02-19 10:54:51.73 INFO <IP4> | PLAYING | Playlist: 67161 [2026-02-16T17:05:57.217Z] | Schedule:  [] | Playlist To Change: [67161_2026-02-12T14.42.26.450.json,67161_2026-02-12T14.43.00.867.json,67161_2026-02-12T14.43.43.763.json,67161_2026-02-16T17.05.57.217.json] 
2026-02-19 10:54:51.73 INFO <IP5> | PLAYING | Playlist: 67161 [2026-02-16T17:05:57.217Z] | Schedule:  [] | Playlist To Change: [67161_2026-02-10T20.54.51.390.json,67161_2026-02-12T14.42.26.450.json,67161_2026-02-12T14.43.43.763.json,67161_2026-02-16T17.05.57.217.json]  (MASTER)
2026-02-19 10:54:51.74 INFO <IP2> | PLAYING | Playlist: 67161 [2026-02-16T17:05:57.217Z] | Schedule:  [] | Playlist To Change: [67161_2026-02-10T20.54.51.390.json,67161_2026-02-12T14.42.26.450.json,67161_2026-02-12T14.43.43.763.json,67161_2026-02-16T17.05.57.217.json]  (MASTER)
2026-02-19 10:54:51.74 INFO ======================================================
```

Notas de formato que la firma tiene que respetar:
- la línea `Members:` **termina en un espacio**; cada `[Master]` va precedido de un espacio.
- las filas tienen **dos espacios** antes de `(MASTER)` y **un espacio final** cuando no lo tienen.
- `Schedule:` vacío se escribe `Schedule:  []` con **dos espacios**.
- el `[Master]` de la línea `Members:` y el `(MASTER)` de la fila son **dos marcas distintas**;
  en este bloque coinciden, pero la firma debería contar la de `Members:` (existe en los 13
  archivos con grupo, mientras que la tabla falta en 13 de 35 bloques).

### Bloque verbatim — 2 masters · cita `20260220-0.log:19764`

```
2026-02-20 10:02:54.76 INFO [Player] [Sync] Version: 1.9.1 - Group: <GROUP-A> - Members: <IP6> <IP5> <IP2> [Master] <IP1> [Master] <IP4> <IP7> <IP3> 
```

Su bloque (`:19765-19773`) muestra exactamente 2 filas `(MASTER)`, `<IP2>` y `<IP1>`, todas las
filas en `Playlist: 67161 [2026-02-16T17:05:57.217Z]`. Los dos masters son justamente los dos
que arrastran 4 archivos en `Playlist To Change` contra 1 del resto.

### Caso de 0 masters · cita `20260222-0.log:133`

```
2026-02-22 11:11:01.38 INFO Multicast IP:  undefined
2026-02-22 11:11:01.40 INFO ======================================================
2026-02-22 11:11:01.42 INFO [Player] [Sync] Version: 1.9.1 - Group: undefined - Members: 
```

No es "grupo sin master": es **el nodo sin grupo** (`Group: undefined`, `Members:` vacío,
`Multicast IP:  undefined` con dos espacios). Ese mismo archivo sí descubre 6 miembros más tarde:
el estado se recupera. La firma "sin master" tiene que distinguir los dos casos.

```sh
for f in *.log; do grep -n 'Members:' "$f" | while IFS= read -r l; do
  n=$(printf '%s' "$l" | grep -o '\[Master\]' | wc -l); echo "$n|$f:${l%%:*}"; done; done \
| cut -d'|' -f1 | sort -n | uniq -c
```

---

## 3. Cascada de pantalla negra — existe, y hay **dos** variantes

`grep -c 'Clearing current playlist'` da 161 líneas repartidas en 9 archivos; **la inmensa mayoría
es el update normal de `04 §4.3`**. Filtrando por "ERROR en las 3 líneas previas" quedan 12, y de
esas 11 son cascada real (1 es falso positivo, ver abajo).

### Variante 1 — JSON corrupto (la de `04 §4.4`): 5 archivos, 5 casos

Cita `20260222-0.log:28-45` (las 10 líneas previas, la cascada y las 3 posteriores):

```
2026-02-22 11:10:53.46 INFO [Webos Storage Manager] Read operation completed for path: config/tags.json
2026-02-22 11:10:53.46 INFO [Webos Storage Manager] Read operation completed for path: config/server.json
2026-02-22 11:10:53.48 INFO [Webos Storage Manager] Read operation completed for path: settings.json
2026-02-22 11:10:53.48 INFO [Webos Storage Manager] Read operation completed for path: events.log
2026-02-22 11:10:53.51 INFO [Node Server Manager] Starting node as service
2026-02-22 11:10:53.64 WARNING [Webos Storage Manager] File does not exist at path: logs/20260222-0.log
2026-02-22 11:10:56.30 INFO [Player] Schedule check
2026-02-22 11:10:56.31 SUCCESS [Player] Processing State
2026-02-22 11:10:56.36 WARNING [Webos Storage Manager] File does not exist at path: timezoneChanged.json
2026-02-22 11:10:56.42 INFO [Webos Storage Manager] Read operation completed for path: playlists/67161_2026-02-16T17.05.57.217.json
2026-02-22 11:10:56.43 ERROR [WebOS Storage] Fail parsing JSON. File: playlists/67161_2026-02-16T17.05.57.217.json
2026-02-22 11:10:56.43 ERROR [Playlist Manager] Loading playlist 67161_2026-02-16T17.05.57.217.json Unexpected end of JSON input
2026-02-22 11:10:56.44 ERROR [Player] Playing playlist 67161 Unexpected end of JSON input
2026-02-22 11:10:56.44 INFO [Playlist Manager] Clearing current playlist
2026-02-22 11:10:56.45 INFO [Player] Error Message: Unexpected end of JSON input. PlaylistId: 67161
2026-02-22 11:10:56.53 INFO [Webos Storage Manager] Read operation completed for path: playlists/67484_2026-02-09T21.17.30.950.json.lock
2026-02-22 11:10:56.53 INFO [Webos Storage Manager] Read operation completed for path: playlists/67180_2026-02-02T20.05.32.293.json.lock
2026-02-22 11:10:56.55 INFO [Webos Storage Manager] Read operation completed for path: playlists/58850_2026-02-16T17.05.57.010.json.lock
```

**Duración real medida: 20 ms** (11:10:56.43 → .45), no "menos de 100 ms" — el doc es correcto
pero holgado por 5×. Las 5 cascadas duran 20 ms, 20 ms, 30 ms, 30 ms y 20 ms.

`04 §4.4` dice "apareció durante un arranque, a +3,7 s del banner": banner en `:2` a 11:10:52.68,
cascada a 11:10:56.43 → **+3,75 s**. ✅ Reproducible.

Las 5 ocurrencias y su causa (nótese que hay **dos textos de causa**, no uno):

`20260220-0.log:15004`, `20260222-0.log:38` (playlist `67161_…json`), `20260223-0.log:70` y
`20260223-0 (1).log:70` (playlist `67148_…json`) → causa `Unexpected end of JSON input`.
`PJ - 6DIC 2.log:96` (playlist `62654_…json`) → causa **`Unexpected token t in JSON at position 10240`**:
son dos textos de causa, no uno.

### Variante 2 — **no documentada**: IO_ERROR de lectura. 6 casos

Misma forma de 5 pasos, pero el paso 1 viene de **otro componente y otro texto**:

```
2026-02-19 07:30:45.10 ERROR [Webos Storage Manager] Read operation failed for path: playlists/67161_2026-02-16T17.05.57.217.json {"returnValue":false,"errorCode":"IO_ERROR","errorText":"Failed to read data"}
2026-02-19 07:30:45.10 ERROR [Playlist Manager] Loading playlist 67161_2026-02-16T17.05.57.217.json IO_ERROR]: Failed to read data
2026-02-19 07:30:45.11 ERROR [Player] Playing playlist 67161 IO_ERROR]: Failed to read data
```
(cita `20260219-0.log:26002-26005`; cierra con `Clearing current playlist` + `Error Message: IO_ERROR]: Failed to read data. PlaylistId: 67161`)

Dos trampas para la firma:
1. El componente es **`[Webos Storage Manager]`** (minúscula "os"), no `[WebOS Storage]`. En el
   corpus conviven las dos grafías: 5 líneas con `[WebOS Storage]`, 9 con `[Webos Storage Manager]
   Read operation failed`. Un regex anclado a una sola grafía pierde la mitad de los casos.
2. La causa se escribe **`IO_ERROR]: Failed to read data`**, con un `]` huérfano. Es un bug de
   formateo del player, y hay que tolerarlo tal cual.

Ocurrencias: `20260219-0.log:26005`, `20260222-0 (1).log:67`/`:8280`/`:8452`,
`20260223-0.log:2236`, `20260223-0 (1).log:2231`.

### Falso positivo de la heurística "ERROR antes"

`20260223-0.log:4112-4115` matchea "hay un ERROR en las 3 líneas previas" pero **no es negro**:

```
2026-02-23 14:57:51.79 ERROR [Server Manager] Heartbeat Sync failed. Status: Error: timeout of 50000ms exceeded
2026-02-23 14:57:52.09 INFO [Player] Received playlist:change from node
2026-02-23 14:57:52.10 INFO [Playlist Manager] Clearing current playlist
```
La firma no puede ser "cualquier ERROR cerca": tiene que exigir la tripleta
`Loading playlist … ` + `Playing playlist … ` inmediatamente anterior.

```sh
grep -n 'Clearing current playlist' "$f" | cut -d: -f1 | while read ln; do
  sed -n "$((ln-3)),$((ln-1))p" "$f" | grep -q ' ERROR ' && sed -n "$((ln-3)),${ln}p" "$f"; done
```

---

## 4. Reinicios

23 arranques (`^Dex Player [\d.]+$`), que coincide con `01 §1.5`. `={53}`÷2 = 23 ✅,
`={54}`÷2 = 35 bloques sync ✅.

Arranques por archivo: `20260222-0 (1).log` **5**; `20260222-0.log`, `20260223-0.log`,
`20260223-0 (1).log`, `…P3.log`, `…P4 MASTER.log` **2** c/u; los otros 8 archivos **1** c/u.

**12 de los 23 arranques son la primera línea del archivo** (`…:2`): no tienen sesión previa en el
log, así que no se pueden clasificar. Quedan **11 reinicios observables**:

| Cita del arranque | Razón | Cita de la razón | Distancia |
|---|---|---|---:|
| `20260219-0.log:25924` | `Scheduled reboot` | `:25921` | 3 líneas |
| `20260220-0.log:14933` | `Scheduled reboot` | `:14925` | 8 líneas |
| `20260223-0 (1).log:2160` | `COMMAND` | `:2158` | 2 líneas |
| `20260223-0.log:2164` | `COMMAND` | `:2155` | 9 líneas |
| `20260222-0 (1).log:8211` | — | — | inesperado |
| `20260222-0 (1).log:8348` | — | — | inesperado |
| `20260222-0 (1).log:8385` | — | — | inesperado |
| `20260222-0 (1).log:8672` | — | — | inesperado |
| `20260222-0.log:379` | — | — | inesperado |
| `TimHortonsTransistmicaP3.log:2722` | — | — | inesperado |
| `TimHortonsTransistmicaP4 MASTER.log:3166` | — | — | inesperado |

**4 programados / 7 inesperados.**

**Corrección a la pregunta:** la ventana de "5 líneas previas" **no alcanza**: dos de las cuatro
razones están a 8 y 9 líneas. El script tiene que mirar **al menos 10 líneas** antes del
`Dex Player`, o mejor, buscar hacia atrás hasta el `={53}` y una línea más.

### Formas de "razón" en este corpus — sólo dos valores

```
2026-02-19 07:29:59.27 INFO [Dex Player] System will reboot. Reason: Scheduled reboot
2026-02-23 12:04:05.21 INFO [Dex Player] System will reboot. Reason: COMMAND
```
`Scheduled reboot` ×2 (`20260219-0.log:25921`, `20260220-0.log:14925`),
`COMMAND` ×2 (`20260223-0.log:2155`, `20260223-0 (1).log:2158`).

Líneas de apoyo que acompañan la razón:

| Forma | Nivel | Ocurrencias | Cita |
|---|---|---:|---|
| `[Server Manager] Reboot command received` | INFO | 2 | `20260223-0.log:2153` |
| `[Server Manager] Reboot command received. Device will reboot` | **WARNING** | 2 | `20260223-0.log:2154` |
| `[Dex Player] All tasks were finished before reboot.` | INFO | 3 | `20260219-0.log:25922` |

Sólo 3 de los 4 reinicios con razón traen `All tasks were finished` (falta en
`20260223-0 (1).log`), así que **no sirve como señal por sí sola**.

### El countdown NO sirve para clasificar — corrección a `02 §2.3`

`Device will reboot in N minutes` aparece 749 veces (coincide con el doc). Pero el doc afirma que
"un reinicio programado real se reconoce porque el countdown llega a valores bajos". **En este
corpus no pasa nunca:** el mínimo observado en todo el corpus es **909 minutos**
(`TimHortonsTransistmicaP4 MASTER.log`), y en los dos reinicios `Scheduled reboot` el último
countdown antes del corte marcaba **1439** y **1437** minutos. El único indicador válido es la
línea explícita `System will reboot. Reason:`.

Rango por archivo: `…P3.log` n=261 [913,1175]; `…P4 MASTER.log` n=238 [909,1183];
`…P1.log` n=235 [949,1183]; los otros 9 archivos n=1–3, rango global [987,1439].

---

## 5. Huecos entre timestamps

| Archivo | Hueco máx | Citas | ¿En un reinicio? |
|---|---:|---|---|
| `20260223-0.log` | **7201,21 s (2,00 h)** | `:33` → `:34` | No — corrección de reloj en pleno arranque |
| `TimHortonsTransistmicaP4 MASTER.log` | **2176,50 s (36,3 min)** | `:3164` → `:3165` | **Sí** — `:3165` es el banner |
| `20260222-0.log` | 62,76 s | `:377` → `:378` | **Sí** — `:378` es el banner |
| `PJ - 6DIC 2.log` | 59,94 s | `:289` → `:290` | No — corte de heartbeat |
| `PJ - 6DIC 4.log` | 58,91 s | `:275` → `:276` | No — corte de heartbeat |
| `PJ - 6DIC 3.log` | 58,49 s | `:277` → `:278` | No — corte de heartbeat |
| `20260223-0 (1).log` | 54,95 s | `:251` → `:252` | No |
| `20260222-0 (1).log` | 48,00 s | `:8383` → `:8384` | **Sí** — `:8384` es el banner |
| `20260220-0.log` | 46,69 s | `:17633` → `:17634` | No |
| `20260219-0.log` | 43,65 s | `:30803` → `:30804` | No |
| `TimHortonsTransistmicaP3.log` | 31,67 s | `:135` → `:136` | No |
| `TimHortonsTransistmicaP1.log` | 30,13 s | `:585` → `:586` | No |
| `QMC32 QA 1.log` | 28,87 s | `:747` → `:748` | No |
| `QMC32 QA 2.log` | 21,62 s | `:943` → `:944` | No |

Los dos huecos grandes, verbatim:

```
2026-02-23 06:48:58.51 WARNING [Webos Storage Manager] File does not exist at path: logs/20260223-0.log
2026-02-23 08:48:59.72 INFO [Main] Player playlists and schedules files format checked
```
```
2025-09-19 20:11:29.06 INFO [Player] [Sync] PLAY Command received. Media "<MEDIA>"
2025-09-19 20:47:45.56 INFO =====================================================
```

**Conclusión operativa:** salvo 3 casos, el hueco máximo de cada archivo está entre 21 y 63 s, o
sea del orden del intervalo de heartbeat (60 s). Un umbral de hueco útil tiene que estar por
encima de ~90 s, no en el minuto.

### Saltos hacia atrás — `01 §1.3` dice 3, hay **6**

| Cita | Salto | Contexto |
|---|---:|---|
| `20260223-0.log:2162→2163` | **−7168,20 s** | Reinicio `COMMAND`: el banner vuelve a 10:04 |
| `QMC32 QA 1.log:14→15` | −10,48 s | tras `Server time offset: -10487 milliseconds` |
| `20260222-0 (1).log:8723→8724` | −1,00 s | tras `Server set to …`, antes del handshake |
| `TimHortonsTransistmicaP3.log:2734→2735` | −0,53 s | tras `Server time offset: -531 milliseconds` |
| `QMC32 QA 2.log:14→15` | −0,23 s | tras `Server time offset: -238 milliseconds` |
| `PJ - 6DIC 3.log:37→38` | −0,09 s | tras `Server time offset: -94 milliseconds` |

**Patrón nuevo:** 4 de los 6 son la línea inmediatamente posterior a
`[System Manager] Server time offset: <N> milliseconds`, y el salto **es exactamente el offset
reportado** — el player corrige el reloj contra el servidor al arrancar. Un script de huecos que no
conozca esto reporta 6 anomalías donde hay 1 sola real (`20260223-0.log`) más 5 correcciones NTP.

El hueco de +2 h y el salto de −2 h del mismo archivo son el mismo fenómeno: `<MACHINE-B2>`
arranca con el reloj 2 h atrasado, lo corrige a los 7 s (`:33→:34`), y al reiniciar por `COMMAND`
vuelve a arrancar atrasado (`:2162→:2163`). Se confirma contra su hermana `20260223-0 (1).log:2`,
que arranca 08:48:51 mientras `20260223-0.log:2` dice 06:48:52.
## 6. Matriz `loga_compare`

### Grupo D (`QMC32`) — el único grupo **completo** del corpus

| Métrica | `QMC32 QA 1.log` | `QMC32 QA 2.log` |
|---|---|---|
| Versión player | `6.4.2408.2600` (`:2`) | `6.4.2408.2600` (`:2`) |
| Plataforma | `tizen` (`:4`) | `tizen` (`:4`) |
| Arranques | 1 (`:2`) | 1 (`:2`) |
| Primera línea | `2025-10-09 12:00:57.44` (`:1`) | `2025-10-09 12:00:42.82` (`:1`) |
| Última línea | `2025-10-09 12:14:02.39` (`:808`) | `2025-10-09 12:13:58.84` (`:1144`) |
| Líneas ERROR | 2 | **73** |
| Heartbeat recv / fail | 19 / 0 | 19 / 0 |
| Playlist | `"<PL-1> [2025-09-16T20:13:08.85Z]"` y `"<PL-2> [2025-10-09T15:04:08.51Z]"` (`:125`) | sólo `"<PL-2> [2025-10-09T15:04:08.51Z]"` (`:745`) |
| Rol sync | **Master** — `[Master]` en su IP (`:803`) y 57 `PLAY burst` (`:133`) | Miembro — 0 bursts |

🔴 **Divergencia:** las 73 líneas ERROR de `QA 2` son 48 `Missing Content` + 12 descargas
fallidas (`:57`: `Missing Content: 2 files. Media: <MEDIA>, <MEDIA>`). El master está sano,
el miembro no tiene el contenido.

### Grupo E (`Tim Hortons`) — 3 de 5 miembros

Común a los tres: `6.4.2408.2600` / `tizen` (`:2`, `:4`), 8 líneas ERROR, **0 fallas de heartbeat**
(237 / 264 / 241 recibidos), misma playlist `"<PL-E> [2025-09-18T14:50:17.88Z]"` →
`"…[2025-09-19T22:45:26.713Z]"` (`P1:116`, `P3:256`, `P4:129`).

| Métrica | `…P1.log` | `…P3.log` | `…P4 MASTER.log` |
|---|---|---|---|
| Arranques | 1 (`:2`) | 2 (`:2`, `:2722`) | 2 (`:2`, `:3166`) |
| Primera / última | `16:14:59.84` / `20:11:29.09` (`:2599`) | `16:24:22.46` / `20:47:09.82` (`:3188`) | `16:14:59.00` / `20:51:31.68` (`:3277`) |
| Rol sync | Miembro, 0 bursts, **sin línea `Members:`** | Miembro (`:203`) | **Master**: 479 bursts (`:138`) |
| Contenido faltante | `Missing Content: 1 files` ×5 | `Missing Content: 8 files` (`:64`) | `Missing Content: 1 files` ×5 |

🟡 `P3:205` es la **única fila `Playlist: undefined`** del corpus, y está en estado `READY` —
exactamente la trampa nº 1 de `07 §7.3`. ✅ Reproducible.
🟡 `P1` y `P4` no emiten ninguna línea `Members:`: `loga_cluster` debe tolerar que 2 de 14 archivos
no tengan snapshot de grupo.

### Grupo C (`6DIC`) — 3 de 4 miembros, el master no tiene log

Los tres son idénticos salvo en dos celdas. Versión `6.7.2508.0100` / `webos` / 1 arranque (`:2`)
en los tres; playlist `"<PL-C1> [2025-11-19T13:46:41.147Z]"` → `"<PL-C2> [2025-11-19T13:47:08.547Z]"`
(`PJ - 6DIC 2.log:110`, `3.log:86`, `4.log:96`); rol miembro en los tres (`:3020`, `:3247`, `:3009`);
heartbeat **273/2, 272/2, 274/2** — las 2 fallas son **simultáneas** (`2.log:290` 11:42:00,
`3.log:278` 11:41:58, `4.log:276` 11:41:59).

| Métrica | `PJ - 6DIC 2.log` | `PJ - 6DIC 3.log` | `PJ - 6DIC 4.log` |
|---|---|---|---|
| Primera / última | `11:30:07.36` / `16:04:15.62` (`:3455`) | `11:30:06.01` / `16:04:13.98` (`:3666`) | `11:30:06.53` / `16:05:14.95` (`:3497`) |
| Líneas ERROR | 10 | 5 | 7 |
| Pantalla negra | **Sí** (`:96`, JSON corrupto) | No | No |

### Grupos A y B (pares del mismo día)

Los cuatro: `6.7.2601.2300` / `webos`, y los cuatro tienen pantalla negra.

| Métrica | `20260222-0.log` (A1) | `20260222-0 (1).log` (A2) | `20260223-0.log` (B2) | `20260223-0 (1).log` (B3) |
|---|---|---|---|---|
| Arranques | 2 | **5** | 2 | 2 |
| Primera / última | `11:10:52.68` / `23:59:45.64` | `08:54:52.91` / `23:59:46.47` | `06:48:52.70` / `17:09:54.44` | `08:48:51.41` / `17:09:52.88` |
| Líneas ERROR | 8 | 46 | **137** | 8 |
| HB recv / fail | 782 / 0 | 918 / 0 | 417 / **85** | 501 / 0 |
| Playlist | `[2026-02-16T17:05:57.217Z]` | idem | `[2026-02-12T14:43:43.763Z]` | idem |
| Rol sync | **sin grupo** (`:133`) | miembro, 3 masters (`:3670`) | miembro (`:2467`) | miembro (`:2471`) |
| Pantalla negra | `:38` (JSON) | IO_ERROR ×3 (`:67`,`:8280`,`:8452`) | `:70` (JSON) | `:70` (JSON) |

---

## 7. Las 6 firmas del catálogo v1

| # | Firma | ¿Ejemplo real? | Cita y líneas que la caracterizan |
|---|---|---|---|
| 1 | **Pantalla negra** | ✅ **Sí, 11 casos, 2 variantes** | `20260222-0.log:38-42` (JSON corrupto) y `20260219-0.log:26002-26006` (IO_ERROR). La firma son 3 ERROR consecutivos + `Clearing current playlist` + `Error Message: … PlaylistId: <id>`, en ≤30 ms |
| 2 | **Loop de reinicios** | ✅ **Sí, 1 caso claro** | `20260222-0 (1).log`: 4 arranques en 4 min 44 s — `:8211` 11:10:55, `:8348` 11:11:24, `:8385` 11:12:15, `:8672` 11:15:39, ninguno con línea de razón |
| 3 | **Split-brain** | ✅ **Sí, 5 snapshots** | 3 masters: `20260219-0.log:32891`, `:33200`, `20260222-0 (1).log:3670`. 2 masters: `20260220-0.log:19764`, `:34398` |
| 4 | **Sin master** | ⚠️ **Sólo en su forma degenerada** | `20260222-0.log:133` es `Group: undefined - Members: ` (vacío) + `Multicast IP:  undefined` (`:128`). **No hay ningún caso de un grupo poblado con 0 `[Master]`.** La firma debe cubrir "sin grupo"; "grupo con miembros y sin master" no tiene ejemplo en este corpus |
| 5 | **Outage de heartbeat** | ✅ **Sí, 2 magnitudes** | Grande: `20260220-0.log:20122-23726`, 98 fallas consecutivas, **1 h 37 min 48 s**, recupera en `:23948`. Chico y simultáneo en 3 pantallas: `PJ - 6DIC 2.log:290`, `3.log:278`, `4.log:276`, 2 fallas / 40 s cada una |
| 6 | **Contenido faltante** | ✅ **Sí, 7 archivos** | `QMC32 QA 2.log:57` (`Missing Content: 2 files`), `TimHortonsTransistmicaP3.log:64` (`8 files`), `TimHortonsTransistmicaP1.log` (`1 files` ×5). 3 formas de mensaje distintas: `Checking playlist failed  Missing Content:` (dos espacios), `Error checkIntegrity Missing Content:` y `CheckInternalIntegrity. Downloading MachineFiles Missing Content:` (que **repite** el fragmento dos veces en la misma línea) |

Adicionales con material real: `Node server not Running` (14 líneas, 9 archivos),
`Member <IP> is not active` (60 líneas exactas, coincide con `07 §7.4`), `Fail over disabled`
(los 14 archivos — el failover está apagado en todo el parque), y
`[Player] [Sync] Error checking group content Cannot read property 'indexOf' of undefined`
(7 líneas, sólo en el par A).

---

## 8. Casos candidatos para la validación final

### 🥇 1. `20260220-0.log` — outage de red que dispara un split-brain

**Es el mejor caso del corpus: hay causa, efecto y recuperación, todo en un archivo.**

- 10:14:49 → 11:52:37: **98 fallas de heartbeat consecutivas**, 1 h 37 min 48 s
  (`:20122` a `:23726`). Recupera en `:23948` a las 11:53:48.
- 10:15:27 → 11:52:15: los **157 `PLAY burst`** del archivo, **todos** dentro de esa ventana
  (`:20148` a `:23703`). El nodo se autopromovió a master 38 s después de perder el servidor.
- Mientras tanto los snapshots de grupo de **antes** (`:19764`, 10:02) y de **después**
  (`:34398`, 16:27) muestran **2 `[Master]` que no son éste** → durante el outage hubo 3.
- 11:16:17 → 11:53:16: **46 `IO_ERROR: Failed to open the file`** (`:22302` a `:23932`), también
  dentro de la ventana.
- Además: cascada de pantalla negra a las 07:30:48 (`:15004`) y reinicio `Scheduled reboot`
  a las 07:30:34 (`:14925`).

```sh
grep -c 'Heartbeat Sync failed' "20260220-0.log"            # 105
grep -n 'PLAY burst' "20260220-0.log" | sed -n '1p;$p'      # 20148 .. 23703
grep -n 'Members:' "20260220-0.log"                         # 19764, 34398 (2 [Master] c/u)
grep -n 'IO_ERROR: Failed to open' "20260220-0.log" | sed -n '1p;$p'
```

### 🥈 2. `20260223-0.log` + `20260223-0 (1).log` — misma playlist corrupta en dos pantallas del mismo grupo

Dos pantallas distintas del grupo B, el mismo día, con **el mismo archivo de playlist corrupto**
y **la misma cascada a 370 ms de distancia**:

- `20260223-0.log:70` 08:49:02.80 y `20260223-0 (1).log:70` 08:49:03.17, ambas
  `Fail parsing JSON. File: playlists/67148_2026-02-12T14.43.43.763.json`.
- A las 12:04 el mismo archivo vuelve a fallar, ahora por IO_ERROR, otra vez en las dos
  (`20260223-0.log:2236`, `20260223-0 (1).log:2231`).
- A las 12:04:05 las dos reciben `Reboot command received` y reinician (`:2155`, `:2158`).
- **Sólo una de las dos** sufre además el corte de heartbeat (85 fallas en `20260223-0.log`,
  0 en la hermana) y el desfase de reloj de 2 h.

Prueba de fuego para `loga_compare`: lo común es el contenido, lo distinto es la red y el reloj.

```sh
grep -n 'Fail parsing JSON' "20260223-0.log" "20260223-0 (1).log"
grep -c 'Heartbeat Sync failed' "20260223-0.log" "20260223-0 (1).log"    # 85 vs 0
```

### 🥉 3. `20260222-0 (1).log` + `20260222-0.log` — loop de reinicios y pérdida de grupo

Las dos pantallas del grupo A reinician en la misma ventana de 6 minutos. `<MACHINE-A2>` arranca
4 veces en 4 min 44 s sin ninguna línea de razón; `<MACHINE-A1>` arranca dos veces y en el medio
reporta `Group: undefined - Members: ` (`20260222-0.log:133`). Sirve para las firmas 2 y 4 a la
vez. Es menos limpio que los anteriores: **no hay ninguna línea que explique por qué reiniciaron**,
así que el caso demuestra el límite del log, no una causa.

```sh
grep -n ' INFO Dex Player ' "20260222-0 (1).log"   # :2 :8211 :8348 :8385 :8672
grep -n 'Group: undefined' "20260222-0.log"        # :133
```

### Mención — `QMC32 QA 1/2`

Único grupo con **todos** sus miembros presentes (2 de 2), 808 y 1.144 líneas, master claro y un
miembro con 48 `Missing Content`. Flojo como incidente, ideal como **fixture** de `loga_cluster`
y `loga_compare`: chico, sano y bien formado.
