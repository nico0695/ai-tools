# 10 — Pantalla, políticas, screenshots y configuración

> Sección **específica**. Dominios `POL`, `SCR`, `SCH`, `CFG`.
> Responde: ¿la pantalla está encendida? ¿se apagó por política o por falla? ¿hay evidencia visual?

---

## 10.1 Estado del display

Dos componentes distintos hablan del display, y conviene no mezclarlos:

```regex
^\[Hardware Policies\] Next Display State policy: (?<estado>\w+)$    ← la política que se va a aplicar
^\[Hardware Policies\] Screen State: (?<estado>\w+)$                 ← el estado según políticas
^\[Screen Manager\] Screen state : (?<estado>ON|OFF)$                ← el estado real del display
^\[Hardware Policies\] Processing policies$                          ← latido, sin contenido
```

**Valores observados:**

| Valor | Ocurrencias | Qué significa |
|---|---:|---|
| `NONE` | 5.044 | ✅ **Sin acción.** Es ruido: el 86 % de los casos |
| `ON` | 820 | 🟡 **Señal.** Cambio real de estado |

> ⚠️ **Advertencia sobre documentación previa:** un catálogo declaraba que `Next Display State policy` **no aparecía en los ejemplos**. Aparece 5.864 veces en 12 de los 14 archivos. Es uno de los mensajes más frecuentes del log.

**Cómo leerlo:**
- Filtrá `NONE`: no informa nada.
- **`Screen state : OFF` explica una "pantalla apagada" sin que haya ninguna falla.** Antes de investigar un incidente, verificá si fue una política horaria.
- `Processing policies` (5.864) es un latido puro: ocultalo siempre.

> **Limitación:** el log no dice el horario configurado de encendido y apagado. Podés ver los cambios de estado, pero no si son los esperados, salvo que conozcas el horario de la tienda por fuera.

---

## 10.2 Screenshots: la evidencia visual

El ciclo completo, tal como aparece:

```
INFO  [Screenshots Manager] Started with 30 minutes interval
INFO  [Screenshots Manager] 1 screenshots to upload
INFO  [Webos Storage Manager] Read operation completed for path: screenshots/<id>
INFO  [Screenshots Manager] Endpoint for screenshot upload <RUTA>
INFO  [Screenshots Manager] Screenshot Uploaded to <RUTA>
INFO  [Screenshots Manager] Upload process finished
```

| Patrón | Regex sobre `message` |
|---|---|
| Intervalo configurado | `^\[Screenshots Manager\] Started with (?<min>\d+) minutes interval$` |
| Pendientes | `^\[Screenshots Manager\] (?<n>\d+) screenshots to upload$` |
| **Subida OK** | `^\[Screenshots Manager\] Screenshot Uploaded to (?<destino>.+)$` |
| Fin del proceso | `^\[Screenshots Manager\] Upload process finished$` |
| **Subida fallida** | `^\[Screenshots Manager\] Screenshot upload failed after (?<n>\d+) attempts\. (?<detalle>.+)$` |
| Archivo perdido | `^\[Screenshots Manager\] File (?<archivo>\S+) not found, File does not exist$` |

**Cómo leerlo:**
- El intervalo es de **30 minutos**, declarado en el propio log. Son unas 16 capturas en una jornada de 8 horas.
- **1.004 subidas exitosas en el corpus**: es un proceso que funciona bien en general.
- Los fallos vienen en dos sabores: **135 por reintentos agotados** (casi siempre `Network error`) y **45 por archivo no encontrado**, que es una carrera entre la subida y el borrado.

> **Valor para soporte:** si las capturas suben bien, tenés evidencia visual de lo que la pantalla mostraba. Si `Screenshot Uploaded` se corta, perdés esa evidencia justo cuando más la necesitás.

Este dominio existía **solo en una de las cuatro fuentes** del relevamiento y quedó confirmado con 1.004 apariciones.

---

## 10.3 Calendarios y programación

```regex
^\[Player\] Schedule check$
^\[Player\] Evaluating calendar: (?<resultado>.+)$
^\[Pending Downloads\] Checking schedule$
^\[Events Manager\]
```

**Cómo leerlo:**
- `Evaluating calendar: Error: Schedule ID is null` es el caso más frecuente y significa **que no hay calendario asignado**. La playlist se reproduce sin restricción horaria. No es una falla si la pantalla no usa calendarios.
- En el bloque `SYNC GROUP INFO`, el campo `Schedule` lo confirma desde el lado del cluster ([07 §7.3](07-SYNC-cluster.md)): vacío (`Schedule:  []`) es sin calendario, y con id (`Schedule: 4092 [<ts>]`) es con calendario asignado. En el corpus, solo 4 de 109 filas tenían calendario.
- `[Events Manager]` (202 líneas) era **exclusivo de una sola fuente** del relevamiento y quedó confirmado.

---

## 10.4 Configuración, tenant y transmisión

```regex
^\[Server Manager\] No tenant code found in dex_config\.xml$
^\[Server Manager\] Found dex_config\.xml$
^\[Transmission Policies\] No Transmission Policies found\.$
^\[Transmission Policies\] Saved (?<archivo>.+)$
^\[User Settings\] Settings Created$
```

**Cómo leerlo:**
- **`No tenant code found in dex_config.xml` apareció en los 14 archivos.** Es un WARNING sistemático, no un caso puntual: la configuración de tenant está incompleta en toda la flota analizada.
- `No Transmission Policies found.` es ERROR pero aparece **durante el arranque de Tizen**, antes del handshake. Es esperable si todavía no bajó las políticas.
- `Settings Created` en el arranque indica **primer arranque** o configuración reiniciada.

---

## 10.5 Cómo diagnosticar "la pantalla está apagada"

```
1. ¿Hay "Screen state : OFF"?              → apagado deliberado, no es falla
2. ¿Hay "Next Display State policy: ON/OFF"? → hubo un cambio de política
3. ¿El log se corta y retoma más tarde?     → apagado programado
4. Si no hay nada de eso                    → no es política; ver doc 04 (pantalla negra)
```

---

## 10.6 Referencia rápida

| Patrón | Regex sobre `message` | Nivel | Señal |
|---|---|---|---|
| Política de display | `^\[Hardware Policies\] Next Display State policy: (?<e>\w+)$` | INFO | `NONE` es ruido; `ON`/`OFF` es señal |
| Estado por política | `^\[Hardware Policies\] Screen State: (?<e>\w+)$` | INFO | Media |
| **Estado real** | `^\[Screen Manager\] Screen state : (?<e>ON\|OFF)$` | INFO | **Alta** |
| Latido de políticas | `^\[Hardware Policies\] Processing policies$` | INFO | **Ruido** |
| Intervalo de capturas | `^\[Screenshots Manager\] Started with (?<m>\d+) minutes interval$` | INFO | Baja |
| Pendientes | `^\[Screenshots Manager\] (?<n>\d+) screenshots to upload$` | INFO | Baja |
| **Captura subida** | `^\[Screenshots Manager\] Screenshot Uploaded to (?<d>.+)$` | INFO | Media |
| **Captura fallida** | `^\[Screenshots Manager\] Screenshot upload failed after (?<n>\d+) attempts\. (?<d>.+)$` | ERROR | **Alta** |
| Captura perdida | `^\[Screenshots Manager\] File (?<a>\S+) not found, File does not exist$` | ERROR | Media |
| Chequeo de calendario | `^\[Player\] Schedule check$` | INFO | Baja |
| Evaluación de calendario | `^\[Player\] Evaluating calendar: (?<r>.+)$` | INFO | Media |
| Eventos | `^\[Events Manager\]` | varios | Media |
| Sin tenant | `^\[Server Manager\] No tenant code found in dex_config\.xml$` | WARNING | Media |
| Config encontrada | `^\[Server Manager\] Found dex_config\.xml$` | SUCCESS | Media |
| Sin políticas de transmisión | `^\[Transmission Policies\] No Transmission Policies found\.$` | ERROR | Baja en el arranque |
| Settings creados | `^\[User Settings\] Settings Created$` | INFO | Media (primer arranque) |

---

**Anterior:** [09 — Storage y archivos](09-STORAGE-archivos.md) · **Siguiente:** [11 — Catálogo](11-CATALOGO.md)
