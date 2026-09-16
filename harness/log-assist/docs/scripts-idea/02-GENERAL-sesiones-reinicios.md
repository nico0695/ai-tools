# 02 — Sesiones, arranques y reinicios

> Sección **General**. Dominio `SYS` (+ `SYS.VER`).
> Responde: ¿cuántas veces se reinició? ¿fue programado o se cayó? ¿cuánto estuvo arriba?

---

## 2.1 Detectar un arranque

Un arranque es un **sándwich de tres líneas**:

```
2026-02-22 11:10:52.68 INFO =====================================================
2026-02-22 11:10:52.70 INFO Dex Player 6.7.2601.2300
2026-02-22 11:10:52.71 INFO =====================================================
2026-02-22 11:10:52.71 INFO [Main] Initializing Dex Player. Platform "webos"
2026-02-22 11:10:52.72 INFO Device UserAgent: Mozilla/5.0 (Web0S; Linux/SmartTV) AppleWebKit/537.36 …
```

| Qué querés | Regex (sobre `message`) | Captura |
|---|---|---|
| **Contar arranques** ✅ | `^Dex Player (?<version>[\d.]+)$` | versión del player |
| Plataforma | `^\[Main\] Initializing Dex Player\. Platform "(?<plataforma>[^"]+)"` | `webos`, `tizen` |
| UserAgent | `^Device UserAgent: (?<ua>.+)$` | modelo y SO del equipo |
| Banner (si lo necesitás) | `^={53}$` | — **dividí por 2** |

> **Usá `Dex Player <versión>` para contar.** Da exactamente un match por arranque y evita la colisión con el bloque de sync (ver [01 §1.5](01-LECTURA-BASE.md)).

**Cada arranque abre una sesión nueva.** Todo lo anterior al banner pertenece a la sesión previa. Esto importa: los contadores (errores, reinicios, timeouts) se deberían leer por sesión, no por archivo.

### Versiones observadas

| Versión del player | Plataforma |
|---|---|
| `6.7.2601.2300` | webOS |
| `6.7.2508.0100` | webOS |
| `6.4.2408.2600` | Tizen |

---

## 2.2 Secuencia real de un arranque

### webOS (tiempos reales medidos)

```
+0.00s  INFO     Dex Player 6.7.2601.2300
+0.00s  INFO     [Main] Initializing Dex Player. Platform "webos"
+0.01s  INFO     Device UserAgent: Mozilla/5.0 (Web0S; Linux/SmartTV) …
+0.15s  WARNING  [Webos Storage Manager] File does not exist at path: currentlyPlayingState.json
+0.26s  INFO     [Webos Storage Manager] Read operation completed for path: config/credentials.json
        …                                          (lee config/*, media.json, settings.json, state.json)
+0.45s  INFO     [Main] Player files checked
+0.80s  INFO     [Node Server Manager] Starting node as service
+3.59s  INFO     [Player] Schedule check
+3.60s  SUCCESS  [Player] Processing State
```

### Tizen (tiempos reales medidos)

```
+0.00s  INFO     Dex Player 6.4.2408.2600
+0.01s  INFO     [Main] Initializing Dex Player. Platform "tizen"
+0.50s  ERROR    Dir failed playlists          ← NORMAL en el arranque
+0.51s  ERROR    Dir failed schedules          ← NORMAL en el arranque
+0.63s  INFO     [Main] Player files checked
+2.16s  INFO     [User Settings] Settings Created
+2.18s  INFO     [Events Manager] Events file created
+2.91s  INFO     [Node Server Manager] Starting node as service
+2.91s  WARNING  [Node Server Manager] Tizen default version loading server2022.js
+3.22s  INFO     [Tizen App] Device time: Fri Sep 19 2025 16:24:25 -05:00
+3.43s  SUCCESS  [Node Server Manager] Node server started
+3.59s  ERROR    [Transmission Policies] No Transmission Policies found.
+3.60s  INFO     [Screenshots Manager] Started with 30 minutes interval
+3.86s  INFO     [System Manager] Player has network connection
+9.18s  INFO     [Server Manager] Sending Handshake
+9.30s  INFO     [System Manager] CPU: 98.00%. Used RAM: 765.12 Mb   ← pico NORMAL
+9.63s  SUCCESS  [Server Manager] Handshake received. Code "LICOK"
+9.63s  INFO     [Server Manager] Machine: <nombre de la pantalla>
+9.63s  INFO     [Server Manager] Machine HB Interval: 60 seconds
+9.68s  INFO     [Server Manager] New Tags saved ["SYNC03"]
```

**Cómo leerlo:**
- Un arranque sano llega a `Player files checked` en menos de 1 segundo y a `Handshake received. Code "LICOK"` en unos 10.
- **`Dir failed` y el pico de CPU al 98 % en esta ventana son normales.** No los reportes como incidentes.
- Si **no** aparece `Handshake received`, el player arrancó pero no se registró contra el servidor: mirá [05 — Red y servidor](05-GENERAL-red-servidor.md).

---

## 2.3 Reinicio programado

El player avisa con un **countdown** que se repite y va bajando de a un minuto:

```regex
^\[System Manager\] Device will reboot in (?<minutos>\d+) minutes$
```

```
2026-02-22 11:11:01 INFO [System Manager] Device will reboot in 1353 minutes
2026-02-22 11:12:01 INFO [System Manager] Device will reboot in 1352 minutes
…
```

Y la hora absoluta del próximo reinicio:

```regex
reboot at: (?<iso>[\d\-T:]+)
```

**Cómo leerlo:**
- El countdown es **altísimamente frecuente** (749 líneas en el corpus) y **no es un evento**: es un latido. No lo cuentes como reinicio.
- Lo que sí sirve: **el valor del countdown define el horario de reinicio programado**. Si ves `1437 minutes`, faltan casi 24 horas.
- **Un reinicio programado real** se reconoce porque el countdown llega a valores bajos y después aparece el banner de arranque.

---

## 2.4 Reinicio inesperado

**No hay ninguna señal previa.** Esto es un hallazgo verificado, no una suposición:

```
-36.37s  INFO  [MENUBOARD_TPL] ****** TEMPLATE STARTED ******
-36.25s  INFO  [MENUBOARD_TPL] Metadata {…}
-33.60s  INFO  [MENUBOARD_TPL] START_TPL received
 -0.03s  INFO  =====================================================   ← corte seco
 +0.00s  INFO  Dex Player 6.7.2601.2300
```

**Cómo distinguirlo de uno programado:**

| Señal | Programado | Inesperado |
|---|---|---|
| Countdown bajo antes del banner | Sí | No |
| `All tasks were finished` antes del corte | A veces | No |
| Última línea antes del banner | Cierre ordenado | Cualquier cosa, a mitad de una operación |
| Salto de timestamp | Chico | Puede ser grande |

**Regla práctica:** si el banner aparece sin countdown bajo justo antes, tratalo como caída. Anotá la última línea previa: suele apuntar a la causa (RAM, error de video, template colgado).

---

## 2.5 Uptime y salud

```
uptime de la sesión = (último timestamp de la sesión) − (timestamp del banner)
reinicios del día   = cantidad de líneas "Dex Player <ver>" en el archivo
```

**Interpretación:**

| Observación | Lectura |
|---|---|
| 1 arranque en un log de día completo | Normal |
| 2 arranques, uno con countdown previo | Normal (reinicio programado) |
| 3 o más arranques en un día | **Investigar**: mirá RAM ([03](03-GENERAL-recursos.md)) y errores de video ([04](04-GENERAL-contenido-playlists.md)) |
| Arranques con pocos minutos entre sí | **Ciclo de reinicio**: el player no llega a estabilizarse |

> En el corpus analizado, un archivo tuvo **5 arranques en 15 horas**. Ese es el patrón de un equipo con problemas.

---

## 2.6 Referencia rápida

| Patrón | Regex sobre `message` | Nivel | Uso |
|---|---|---|---|
| Arranque | `^Dex Player (?<version>[\d.]+)$` | INFO | **Contar reinicios** |
| Banner | `^={53}$` | INFO | Delimitar sesión (÷2) |
| Plataforma | `^\[Main\] Initializing Dex Player\. Platform "(?<plataforma>[^"]+)"` | INFO | Identidad |
| UserAgent | `^Device UserAgent: (?<ua>.+)$` | INFO | Modelo del equipo |
| Countdown | `^\[System Manager\] Device will reboot in (?<minutos>\d+) minutes$` | INFO | Horario programado. **No es un evento** |
| Reinicio absoluto | `reboot at: (?<iso>[\d\-T:]+)` | INFO | Horario programado |
| Cierre ordenado | `All tasks were finished` | INFO | Distinguir apagado limpio |
| Archivos verificados | `^\[Main\] Player files checked$` | INFO | Hito de arranque |
| Node arriba | `NodeJs service is running` | SUCCESS | Salud del sync local |
| Node caído | `^\[Player\] Node server not Running$` | ERROR | **Falla real** |

---

**Anterior:** [01 — Lectura base](01-LECTURA-BASE.md) · **Siguiente:** [03 — Recursos](03-GENERAL-recursos.md)
