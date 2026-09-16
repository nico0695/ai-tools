# 06 — Ruido: qué ocultar y qué nunca ocultar

> Sección **General**. Dominio `NOISE`.
> Responde: ¿cómo paso de 178.000 líneas a las 50 que importan?

---

## 6.1 El problema, en números

**El 60 % del volumen son 20 mensajes repetidos.** Sin filtrar, cualquier lectura se ahoga.

| Mensaje | Líneas | % del corpus |
|---|---:|---:|
| `[Player] [Sync] PLAY Command received. Media "…"` | 14.657 | 8,2 % |
| `[Webos Storage Manager] Read operation completed for path: …` | 17.872 | 10,0 % |
| `[Channel Manager] preloadNextMedia: {…}` | 8.317 | 4,7 % |
| `[Player] Playlist ended.` | 6.942 | 3,9 % |
| `[Channel Manager] playNextMedia: Transitioning media {…}` | 6.809 | 3,8 % |
| `[Hardware Policies] Processing policies` | 5.864 | 3,3 % |
| `[Server Manager] Heartbeat received from server` | 5.756 | 3,2 % |
| `[Hardware Policies] Next Display State policy: NONE` | 5.044 | 2,8 % |
| `[Input Manager] Remote Control enabled` | 5.073 | 2,8 % |
| `[Input Manager] Panel enabled` | 5.063 | 2,8 % |
| Bloque `[MENUBOARD_TPL]` (carga de template) | ~30.000 | 17 % |

---

## 6.2 Regla de oro

> **Ocultar no es lo mismo que no contar.**
> Un mensaje oculto sigue alimentando los KPIs y sigue disponible como contexto. Lo que se oculta es su aparición línea por línea en la vista de eventos.

Esto importa porque varios mensajes ruidosos son **valiosos por su ausencia**: si `PLAY Command received` desaparece, la pantalla dejó de rotar. No podrías detectarlo si lo hubieras descartado al parsear.

---

## 6.3 Qué ocultar por defecto

| Patrón | Regex sobre `message` | Por qué |
|---|---|---|
| Lecturas de storage | `^\[Webos Storage Manager\] Read operation completed for path:` | 10 % del volumen, sin valor individual |
| Precarga de medio | `^\[Channel Manager\] preloadNextMedia:` | Mecánica del ciclo |
| Transición de medio | `^\[Channel Manager\] playNextMedia: Transitioning media` | Mecánica del ciclo |
| Canal removido | `^\[Channel Manager\] Channel removed$` | Mecánica del ciclo |
| Control remoto | `^\[Input Manager\] (Remote Control\|Panel) enabled$` | Ruido puro, sin diagnóstico |
| Procesamiento de políticas | `^\[Hardware Policies\] Processing policies$` | Latido, sin contenido |
| Política sin cambio | `^\[Hardware Policies\] Next Display State policy: NONE$` | `NONE` = sin acción |
| Carga de template | `^\[MENUBOARD_TPL\] \[(OffsetsManager\|DataManager\|StoreDataManager)\]` | 17 % del volumen |
| Fuentes y assets | `^\[MENUBOARD_TPL\] (Loaded fonts\|\d+ assets loaded)` | Mecánica de carga |
| Countdown de reinicio | `^\[System Manager\] Device will reboot in \d+ minutes$` | Latido. **Guardá solo el último valor** |
| Node local vivo | `NodeJs service is running` | Latido de salud |
| Playlist cerrada | `^\[Node\] \[Sync\] Playlist stopped$` | Parte del update normal |
| Fin de vuelta | `^\[Player\] Playlist ended\.$` | Mecánica del ciclo |
| Cambio descartado | `Reported playlist to change is not trigger` | Evaluación de rutina |

---

## 6.4 Qué agrupar en lugar de ocultar

Hay mensajes que individualmente no dicen nada, pero **contados sí**:

| Patrón | Cómo agruparlo | Qué revela |
|---|---|---|
| `PLAY Command received` | Contar por hora | **Un hueco = dejó de rotar.** No lo ocultes del todo |
| `Heartbeat received from server` | Contar por hora | Tasa de éxito de la conexión ([05 §5.2](05-GENERAL-red-servidor.md)) |
| `CPU: …%. Used RAM: … Mb` | Serie temporal | Tendencia de recursos ([03](03-GENERAL-recursos.md)) |
| `Screenshot Uploaded to …` | Contar por hora | Confirma que la pantalla reporta evidencia |
| **Stack traces** (`^\s+at\s`) | **Plegar bajo el error anterior** | Son el 20 % de las líneas ERROR y no son eventos |
| `Failed to play video … interrupted by a new load request` | Contar | Benigno en pocas ocurrencias; una racha sí es señal |
| `File does not exist at path: …` | Agrupar por archivo | Un archivo faltante recurrente es un problema real |

---

## 6.5 Qué NUNCA se oculta

Aunque sea repetitivo o de nivel bajo:

| Patrón | Por qué |
|---|---|
| `Fail parsing JSON` | Primer eslabón de la pantalla negra |
| `Unexpected end of JSON input` | Cascada de pantalla negra |
| `Clearing current playlist` **precedido de ERROR** | Es el momento del negro |
| `IO_ERROR: Failed to open the file` | Archivo ilegible |
| `Heartbeat Sync failed` | Salud de la conexión |
| `Node server not Running` | Sync local caído |
| `Missing Content: N files` | Contenido incompleto |
| `Handshake received. Code "…"` | Hito de registro |
| `Dex Player <versión>` | **Marca de sesión.** Ocultarlo rompe toda la segmentación |
| `Member <IP> is not active` | Nodo caído del cluster |
| Toda la línea `Members:` y el bloque `SYNC GROUP INFO` | Estado del cluster |

---

## 6.6 Los tres casos que dependen del contexto

Estos mensajes son ruido **o** señal según dónde aparezcan. Es lo que la documentación previa resolvía de formas contradictorias.

### `Dir failed`

```regex
^Dir failed (?<dir>\w+)$
```

| Contexto | Veredicto |
|---|---|
| **Dentro de los 5 s posteriores a un arranque** | **Ruido.** Es la creación normal de directorios en Tizen |
| Fuera de esa ventana | **Error real.** Un directorio se volvió inaccesible |

### `File does not exist at path: …`

```regex
^\[Webos Storage Manager\] File does not exist at path: (?<path>.+)$
```

| Archivo | Veredicto |
|---|---|
| `currentlyPlayingState.json`, `timezoneChanged.json`, `logs/<archivo de hoy>` | **Ruido.** Es el primer arranque del día; todavía no existen |
| Un archivo de media o de playlist | **Señal.** Falta contenido |
| El mismo archivo una y otra vez | **Señal.** Algo no se está creando nunca |

### `Screen state` y `Next Display State policy`

```regex
^\[Screen Manager\] Screen state : (?<estado>ON|OFF)$
^\[Hardware Policies\] Next Display State policy: (?<estado>\w+)$
```

| Valor | Veredicto |
|---|---|
| `NONE` | **Ruido.** Significa "sin acción" y es el 86 % de los casos |
| `ON` u `OFF` | **Señal.** Es un cambio real de estado del display, y explica una "pantalla apagada" sin que haya falla |

---

## 6.7 Filtro mínimo recomendado

Para pasar de 178.000 líneas a algo legible, en orden:

```
1. Quedate solo con ERROR y WARNING.
2. Plegá los stack traces (^\s+at\s) bajo su error.
3. Sacá "Dir failed" dentro de los 5 s de un arranque.
4. Sacá "File does not exist" de los 3 archivos de estado conocidos.
5. Agrupá los "Failed to play video … interrupted" en un solo contador.
6. Sumá SIEMPRE, aunque sean INFO o SUCCESS:
   - Dex Player <versión>            (sesiones)
   - Handshake received              (registro)
   - Playing Playlist                (qué se reproduce)
   - Clearing current playlist       (pantalla vacía)
   - la línea Members:               (salud del cluster)
```

Con eso, un log de 35.000 líneas queda en unas pocas decenas de eventos con significado.

---

**Anterior:** [05 — Red y servidor](05-GENERAL-red-servidor.md) · **Siguiente:** [07 — Cluster / Sync Group](07-SYNC-cluster.md)
