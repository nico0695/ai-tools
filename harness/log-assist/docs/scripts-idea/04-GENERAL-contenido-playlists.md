# 04 — Contenido, playlists y pantalla negra

> Sección **General**. Dominios `CNT`, `CNT.PLAY`, `CNT.DL`.
> Responde: ¿qué playlist hay? ¿cambió? ¿está reproduciendo? ¿por qué se quedó en negro?

---

## 4.1 Qué playlist está puesta

La línea que lo dice todo:

```regex
^\[Player\] Playing Playlist "(?<nombre>[^"]+)"$
```

```
SUCCESS [Player] Playing Playlist "V01 V SERV 7PV (Mall Plaza Vespucio) - TPL 2600 [2026-02-16T17:05:57.217Z]"
                                   └──────────────── nombre ────────────────┘ └──── timestamp de versión ────┘
```

El nombre trae **la ubicación y la versión de la playlist**. Ese timestamp entre corchetes es la clave para comparar pantallas: dos que reproducen la misma playlist deben tener el mismo.

Otras formas de identificarla:

| Qué querés | Regex sobre `message` |
|---|---|
| ID numérico | `^\[Node\] \[Sync\] PLAYLIST ID = (?<id>\d+)$` |
| Archivo en disco | `Read operation completed for path: playlists/(?<archivo>(?<id>\d+)_(?<ts>[\dT.\-]+)\.json)` |
| ID en un error | `^\[Player\] Error Message: (?<msg>.+?)\. PlaylistId: (?<id>\d+)$` |

> El nombre del archivo de playlist tiene la forma `<id>_<timestamp ISO con puntos>.json`, por ejemplo `67161_2026-02-16T17.05.57.217.json`. Ese es el mismo timestamp que aparece entre corchetes en `Playing Playlist`.

---

## 4.2 El ciclo normal de reproducción

```
INFO  [Channel Manager] preloadNextMedia:  {"nextController":"LonelyVideoComponent","media":"7PV 2"}
INFO  [Player] [Sync] PLAY Command received. Media "7PV 2"
INFO  [Channel Manager] playNextMedia: Transitioning media  {"previous":"…","show":"7PV 2"}
      … (dura lo que dura el medio) …
INFO  [Player] Playlist ended.
```

| Patrón | Regex sobre `message` |
|---|---|
| Precarga | `^\[Channel Manager\] preloadNextMedia:\s*(?<json>\{.*\})$` |
| Reproducir | `^\[Player\] \[Sync\] PLAY Command received\. Media "(?<media>[^"]*)"$` |
| Transición | `^\[Channel Manager\] playNextMedia: Transitioning media\s*(?<json>\{.*\})$` |
| Fin de ciclo | `^\[Player\] Playlist ended\.$` |

**Cómo leerlo:**
- **El intervalo entre PLAY es la duración del medio**, no una cadencia fija. En el corpus va de 4,4 s a 60 s según la pantalla. **No lo uses como señal de nada** (ver [07 — Cluster](07-SYNC-cluster.md), donde esto invalida una heurística popular).
- `Playlist ended.` marca el fin de una vuelta completa y el reinicio del ciclo. Es normal y muy frecuente.
- **Si `PLAY Command received` se corta y no vuelve, la pantalla dejó de rotar contenido.**

---

## 4.3 Update de playlist, de punta a punta

Secuencia real, completa en menos de un segundo:

```
SUCCESS [Player] Playing Playlist "V01 V SERV 7PV … [2026-02-16T17:05:57.217Z]"
INFO    [Channel Manager] Channel removed
INFO    [Node] [Sync] Playlist stopped              ← parte del ciclo NORMAL
INFO    [Node] [Sync] PLAYLIST ID = 67161
INFO    [Node] [Sync] New Playlist received
INFO    [Player] Received playlist:change from node
INFO    [Player] Reported playlist to change is not trigger. Processing state.
INFO    [Playlist Manager] Clearing current playlist
```

| Patrón | Regex sobre `message` | Qué marca |
|---|---|---|
| Cierre del anterior | `^\[Node\] \[Sync\] Playlist stopped$` | **Normal**, no es una falla |
| ID nuevo | `^\[Node\] \[Sync\] PLAYLIST ID = (?<id>\d+)$` | Qué playlist entra |
| Recepción | `^\[Node\] \[Sync\] New Playlist received$` | Llegó una versión nueva |
| Propagación | `^\[Player\] Received playlist:change from node$` | El nodo avisa al player |
| No aplica | `Reported playlist to change is not trigger` | Se evaluó y se descartó |
| Limpieza | `^\[Playlist Manager\] Clearing current playlist$` | Pantalla vacía **por un instante** |

> ⚠️ **`Playlist stopped` NO significa que la pantalla se apagó.** Es parte del cambio normal de playlist. La documentación previa lo trataba como señal de cese de reproducción y es un error: aparece 144 veces en operación perfectamente sana.

---

## 4.4 Pantalla negra: la cascada del JSON corrupto

**Este es el caso de soporte número uno.** Son 5 líneas en menos de 100 milisegundos:

```
ERROR [WebOS Storage] Fail parsing JSON. File: playlists/67161_2026-02-16T17.05.57.217.json
ERROR [Playlist Manager] Loading playlist 67161_2026-02-16T17.05.57.217.json Unexpected end of JSON input
ERROR [Player] Playing playlist 67161 Unexpected end of JSON input
INFO  [Playlist Manager] Clearing current playlist          ← ACÁ QUEDA EN NEGRO
INFO  [Player] Error Message: Unexpected end of JSON input. PlaylistId: 67161
```

| Paso | Regex sobre `message` | Nivel |
|---|---|---|
| 1. Parseo | `^\[WebOS Storage\] Fail parsing JSON\. File: (?<archivo>.+)$` | ERROR |
| 2. Carga | `^\[Playlist Manager\] Loading playlist (?<archivo>\S+) (?<causa>.+)$` | ERROR |
| 3. Reproducción | `^\[Player\] Playing playlist (?<id>\d+) (?<causa>.+)$` | ERROR |
| 4. **Negro** | `^\[Playlist Manager\] Clearing current playlist$` | INFO |
| 5. Resumen | `^\[Player\] Error Message: (?<msg>.+?)\. PlaylistId: (?<id>\d+)$` | INFO |

**Cómo detectarlo:** `Clearing current playlist` **precedido por líneas ERROR**. La línea 4 sola no alcanza: también aparece en el update normal (§4.3). Lo que la convierte en pantalla negra es el contexto de errores inmediatamente anterior.

**Lo más importante:** esta cascada apareció **durante un arranque**, a +3,7 s del banner. O sea que el player arrancó y se quedó en negro enseguida. Si el archivo de playlist está corrupto en disco, **cada reinicio repite el problema**, lo que explica los ciclos de reinicio.

**Qué hacer con eso:** el `PlaylistId` de la línea 5 y el archivo de la línea 1 te dicen exactamente qué hay que volver a bajar.

---

## 4.5 Otras causas de pantalla en negro o contenido incompleto

### Fallas de reproducción de video

```regex
^\[Global Error Handler\] Failed to play video with ID (?<id>\S+): (?<causa>.+?) Line:
```

**Separá dos casos, porque no son lo mismo:**

| Causa | Ocurrencias | Gravedad |
|---|---:|---|
| `The play() request was interrupted by a new load request` | 316 | **Benigno.** Es una carrera; se recupera en menos de 2 s |
| `IO_ERROR: Failed to open the file` | 46 | **Grave.** El archivo no se puede leer |

> Este componente no aparecía en ninguna documentación previa y es una causa directa de fallas visibles.

### Contenido faltante

```regex
^\[Player\] Checking playlist failed\s+Missing Content: (?<n>\d+) files\. Media: (?<media>.+)$
^\[Player\] Error checkIntegrity Missing Content: (?<n>\d+) files\. Media: (?<media>.+)$
```

Casos observados: 33 con 1 archivo faltante, y casos de 2, 6 y 8. **La playlist se reproduce igual, pero salteando el medio que falta.**

### Descarga fallida

```regex
^\[Download Manager\] Error downloading file\. Error: (?<causa>.+?) \{
^\[BackgroundManager\] Cannot download image\. Reason: (?<causa>.+)$
```

Es el eslabón que explica **por qué** falta contenido. Si ves `Missing Content` sin un error de descarga previo, el archivo se perdió después de bajarse.

---

## 4.6 El chequeo de integridad

```regex
^\[Player\] Checking internal content integrity$
^\[Player\] Check integrity from heartbeat fail\.$
^\[Media Library\] Check or download in progress$
```

> **Dato útil:** `Check integrity from heartbeat fail.` conecta red con contenido. Cuando falla el heartbeat, el player desconfía de su contenido y lo verifica. Si ves muchos chequeos de integridad, mirá primero la red.

`Check or download in progress` explica por qué un chequeo no arrancó: ya había uno corriendo.

---

## 4.7 Cómo diagnosticar "la pantalla está en negro"

```
1. ¿Hay ERROR cerca del horario del reclamo?
2. ¿Aparece "Clearing current playlist" después de esos ERROR?     → §4.4, JSON corrupto
3. ¿Hay "IO_ERROR: Failed to open the file"?                        → §4.5, archivo ilegible
4. ¿Se cortó "PLAY Command received" y no volvió?                   → dejó de rotar
5. ¿Hay "Missing Content"?                                          → falta contenido, pero rota igual
6. ¿Aparece "Screen state : OFF"?                                   → apagado por política, ver doc 10
7. ¿Hay un arranque justo antes?                                    → se reinició, ver doc 02
```

---

## 4.8 Referencia rápida

| Patrón | Regex sobre `message` | Nivel | Señal |
|---|---|---|---|
| Playlist activa | `^\[Player\] Playing Playlist "(?<nombre>[^"]+)"$` | SUCCESS | Alta |
| ID de playlist | `^\[Node\] \[Sync\] PLAYLIST ID = (?<id>\d+)$` | INFO | Alta |
| Playlist nueva | `^\[Node\] \[Sync\] New Playlist received$` | INFO | Alta |
| Cambio propagado | `^\[Player\] Received playlist:change from node$` | INFO | Media |
| Reproducir medio | `^\[Player\] \[Sync\] PLAY Command received\. Media "(?<media>[^"]*)"$` | INFO | Ruido en volumen, útil por ausencia |
| Fin de vuelta | `^\[Player\] Playlist ended\.$` | INFO | Ruido |
| Cierre de playlist | `^\[Node\] \[Sync\] Playlist stopped$` | INFO | **Ruido, no es falla** |
| **Pantalla vacía** | `^\[Playlist Manager\] Clearing current playlist$` | INFO | **Crítica si hay ERROR antes** |
| JSON corrupto | `^\[WebOS Storage\] Fail parsing JSON\. File: (?<archivo>.+)$` | ERROR | **Crítica** |
| Carga fallida | `^\[Playlist Manager\] Loading playlist (?<archivo>\S+) (?<causa>.+)$` | ERROR | **Crítica** |
| Reproducción fallida | `^\[Player\] Playing playlist (?<id>\d+) (?<causa>.+)$` | ERROR | **Crítica** |
| Resumen del error | `^\[Player\] Error Message: (?<msg>.+?)\. PlaylistId: (?<id>\d+)$` | INFO | Alta |
| Video fallido | `^\[Global Error Handler\] Failed to play video with ID (?<id>\S+): (?<causa>.+?) Line:` | ERROR | Depende de la causa |
| Archivo ilegible | `^\[Global Error Handler\] IO_ERROR: Failed to open the file` | ERROR | **Crítica** |
| Contenido faltante | `Missing Content: (?<n>\d+) files\. Media: (?<media>.+)$` | ERROR | Alta |
| Descarga fallida | `^\[Download Manager\] Error downloading file\. Error: (?<causa>.+?) \{` | ERROR | Alta |
| Chequeo por heartbeat | `^\[Player\] Check integrity from heartbeat fail\.$` | WARNING | Media, conecta con red |
| Sin canales | `^\[Node\] \[Sync\] Channels empty$` | INFO | Media |

---

**Anterior:** [03 — Recursos](03-GENERAL-recursos.md) · **Siguiente:** [05 — Red y servidor](05-GENERAL-red-servidor.md)
