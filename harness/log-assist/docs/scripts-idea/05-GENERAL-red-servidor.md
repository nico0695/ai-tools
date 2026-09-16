# 05 — Red y servidor

> Sección **General**. Dominio `NET`.
> Responde: ¿el player ve al servidor? ¿está registrado? ¿cuántas fallas de red hubo?

---

## 5.1 El handshake: el registro inicial

Ocurre una vez por arranque, unos 10 segundos después del banner:

```
INFO     [Server Manager] Fetching dex config on <URL>
INFO     [System Manager] Player has network connection
INFO     [Server Manager] Sending Handshake
INFO     [Server Manager] Hostname: <IP> <MAC>
SUCCESS  [Server Manager] Found dex_config.xml
INFO     [Server Manager] Using server: <URL>
WARNING  [Server Manager] No tenant code found in dex_config.xml
INFO     [System Manager] The player has connectivity with the server
INFO     [Server Manager] The server has access to https, the url was changed to <URL>
SUCCESS  [Server Manager] Handshake received. Code "LICOK"
INFO     [Server Manager] Machine: <nombre de la pantalla>
INFO     [Server Manager] Machine HB Interval: 60 seconds
INFO     [Server Manager] New Tags saved ["SYNC03"]
```

| Patrón | Regex sobre `message` |
|---|---|
| Envío | `^\[Server Manager\] Sending Handshake$` |
| **Respuesta** | `^\[Server Manager\] Handshake received\. Code "(?<code>[A-Z]+)"$` |
| Identidad | `^\[Server Manager\] Machine: (?<machine>.+)$` |
| Host y MAC | `^\[Server Manager\] Hostname: (?<ip>\S+) (?<mac>\S+)$` |
| Intervalo de HB | `^\[Server Manager\] Machine HB Interval: (?<seg>\d+) seconds$` |
| Tags | `^\[Server Manager\] New Tags saved \[(?<tags>.*)\]$` |
| Servidor | `^\[Server Manager\] Using server: (?<url>.+)$` |
| Sin tenant | `^\[Server Manager\] No tenant code found in dex_config\.xml$` |

**Cómo leerlo:**
- **`Code "LICOK"` es el único código observado**, en las 21 apariciones del corpus. Es la licencia validada. Cualquier otro código merece atención.
- **Si no hay `Handshake received`, el player no quedó registrado.** Todo lo demás (playlists, sync, screenshots) va a fallar en cascada.
- `No tenant code found in dex_config.xml` apareció como WARNING en **los 14 archivos**. Es un problema de configuración generalizado, no un caso puntual.

---

## 5.2 Heartbeat: el pulso con el servidor

El player declara su propio intervalo: **60 segundos**, confirmado midiendo los intervalos reales.

```regex
^\[Server Manager\] Heartbeat received from server$                        ← SUCCESS, sano
^\[Server Manager\] Heartbeat Sync failed\. Status: (?<causa>.+)$          ← ERROR, falla
```

### Las dos causas de falla

| Causa | Ocurrencias | Lectura |
|---|---:|---|
| `Error: timeout of 50000ms exceeded` | 115 | El servidor no respondió en 50 s |
| `Error: Network Error` | 81 | No hubo conexión |

> ⚠️ **`Heartbeat Sync failed` es el heartbeat con el SERVIDOR, no con el grupo sync.** Lo emite `[Server Manager]` en el 100 % de los casos. Documentación previa lo clasificaba como caída del nodo sync local, y es un error de interpretación. El sync local usa `[Node] [Sync]`, que es otro componente (ver [07 — Cluster](07-SYNC-cluster.md)).

### Cómo calcular la salud de la conexión

Ahora sí es calculable, porque el log declara el intervalo:

```
heartbeats esperados = duración de la sesión (segundos) ÷ 60
tasa de éxito        = recibidos ÷ esperados
```

**Referencia del corpus:** 5.756 recibidos contra 196 fallidos, o sea un **3,3 % de fallas**, concentrado en 5 de 14 archivos. Los otros 9 no tuvieron ninguna.

**Cómo interpretarlo:**

| Observación | Lectura |
|---|---|
| Fallas aisladas, con recuperación inmediata | Normal. La red se cae un rato |
| Rachas de fallas seguidas | **Investigar**: corte real de conectividad |
| Muchas fallas más chequeos de integridad | El player desconfía de su contenido: ver [04 §4.6](04-GENERAL-contenido-playlists.md) |
| Huecos sin ningún heartbeat | Puede ser reinicio o congelamiento, no necesariamente red |

---

## 5.3 Timeouts: contalos, no los midas

**Los 159 timeouts del corpus miden exactamente 50000 ms. Todos.**

```regex
timeout of (?<ms>\d+)ms exceeded
```

> Ese número **no es una medición**: es el timeout configurado del cliente HTTP. Por eso cualquier estadística sobre su duración (promedio, p95, máximo) siempre da 50000 y no informa nada. **La métrica útil es la cantidad de timeouts por hora.**

Dónde aparecen los timeouts:

| Contexto | Regex | Ocurrencias |
|---|---|---:|
| Heartbeat | `^\[Server Manager\] Heartbeat Sync failed\. Status: Error: timeout` | 115 |
| Subida de eventos | `^\[Events Manager\] Uploading events\. Error: timeout` | 44 |

---

## 5.4 Conectividad general

```regex
^\[Dex Player\] Player lost Internet connection$      ← WARNING
^\[Dex Player\] Player has Internet connection$       ← INFO
^\[System Manager\] Player has network connection$
^\[System Manager\] The player has connectivity with the server$
```

**Cómo leerlo:** en el corpus, `lost Internet connection` apareció 4 veces y **se recuperó en 7,1 segundos** sin afectar la reproducción. Es una señal transitoria. Lo que importa es cuánto dura la caída, no que ocurra.

> Ojo con la distinción: `Player has network connection` es la red local, `The player has connectivity with the server` es el servidor alcanzable. Se puede tener red y no tener servidor.

---

## 5.5 Subida de eventos y screenshots

Dos operaciones de salida que fallan por su cuenta:

```regex
^\[Events Manager\] Uploading events\. Error: (?<causa>.+)$                                  ← 138
^\[Screenshots Manager\] Screenshot upload failed after (?<n>\d+) attempts\. (?<detalle>.+)$ ← 135
```

**Cómo leerlo:** si fallan **solo** estas dos y el heartbeat está bien, el problema no es la conectividad general sino los endpoints de subida o los permisos. Si fallan **junto** con el heartbeat, es un corte de red y no hace falta investigarlas por separado.

---

## 5.6 Otras señales de red

| Patrón | Regex sobre `message` | Nota |
|---|---|---|
| HTTP con error | `HTTP status: (?<code>\d+)` | `404` observado al bajar una imagen de fondo |
| Socket sin inicializar | `^\[Player\] Socket not initialized for report$` | WARNING, en 12 de 14 archivos |
| Node local caído | `^\[Player\] Node server not Running$` | ERROR, 14 casos en 9 archivos |
| Node local arriba | `NodeJs service is running` | SUCCESS, el contrapunto sano |

> `Socket not initialized for report` aparece en casi todos los archivos y en volumen bajo (33 en total). Es un problema menor recurrente, no un incidente.

---

## 5.7 Cómo diagnosticar "la pantalla no actualiza contenido"

```
1. ¿Hay "Handshake received. Code LICOK"?     → si no, nunca se registró
2. ¿Cuántos "Heartbeat received" vs "failed"? → tasa de éxito
3. Si hay fallas, ¿son racha o aisladas?      → racha = corte real
4. ¿Hay timeouts o Network Error?             → timeout = servidor lento; Network = sin ruta
5. ¿Fallan también eventos y screenshots?     → sí = corte general; no = endpoint puntual
6. ¿Aparece "Node server not Running"?        → el sync local está caído, ver doc 07
```

---

## 5.8 Referencia rápida

| Patrón | Regex sobre `message` | Nivel | Señal |
|---|---|---|---|
| Handshake enviado | `^\[Server Manager\] Sending Handshake$` | INFO | Media |
| **Handshake OK** | `^\[Server Manager\] Handshake received\. Code "(?<code>[A-Z]+)"$` | SUCCESS | **Alta** |
| Identidad | `^\[Server Manager\] Machine: (?<machine>.+)$` | INFO | Alta |
| Host y MAC | `^\[Server Manager\] Hostname: (?<ip>\S+) (?<mac>\S+)$` | INFO | Alta |
| Intervalo de HB | `^\[Server Manager\] Machine HB Interval: (?<seg>\d+) seconds$` | INFO | Alta |
| Tags | `^\[Server Manager\] New Tags saved \[(?<tags>.*)\]$` | INFO | Media |
| Heartbeat OK | `^\[Server Manager\] Heartbeat received from server$` | SUCCESS | Ruido en volumen, clave por ausencia |
| **Heartbeat falla** | `^\[Server Manager\] Heartbeat Sync failed\. Status: (?<causa>.+)$` | ERROR | **Alta** |
| Timeout | `timeout of (?<ms>\d+)ms exceeded` | ERROR | Alta. **Contar, no medir** |
| Error de red | `Network Error` | ERROR | Alta |
| Internet caída | `^\[Dex Player\] Player lost Internet connection$` | WARNING | Media |
| Internet OK | `^\[Dex Player\] Player has Internet connection$` | INFO | Ruido |
| Servidor alcanzable | `^\[System Manager\] The player has connectivity with the server$` | INFO | Media |
| Sin tenant | `^\[Server Manager\] No tenant code found in dex_config\.xml$` | WARNING | Media, config |
| Eventos fallidos | `^\[Events Manager\] Uploading events\. Error: (?<causa>.+)$` | ERROR | Media |
| Socket sin init | `^\[Player\] Socket not initialized for report$` | WARNING | Baja |
| Node caído | `^\[Player\] Node server not Running$` | ERROR | **Alta** |
| HTTP error | `HTTP status: (?<code>\d+)` | ERROR | Media |

---

**Anterior:** [04 — Contenido y playlists](04-GENERAL-contenido-playlists.md) · **Siguiente:** [06 — Ruido](06-GENERAL-ruido.md)
