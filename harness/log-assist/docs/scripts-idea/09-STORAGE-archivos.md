# 09 — Storage, archivos y descargas

> Sección **específica**. Dominios `STO`, `CNT.DL`, `DIR`.
> Responde: ¿faltan archivos? ¿hay espacio? ¿se bajó el contenido?

---

## 9.1 El componente más ruidoso del log

```regex
^\[Webos Storage Manager\] Read operation completed for path:\s*(?<path>.+)$
```

**17.872 líneas, el 10 % del corpus.** Es la lectura de cualquier archivo, y es ruido casi puro.

> ⚠️ **Solo existe en webOS.** Tizen no tiene un equivalente, así que su ausencia no significa nada en un log de Tizen.

Las rutas más leídas son de configuración: `config/credentials.json`, `config/server.json`, `config/tags.json`, `config/policies.json`, `config/transmission.json`, `events.log`, `media.json`, `settings.json`, `state.json`, `timeOffset.json`.

**Para qué sirve, pese al ruido:**
- Te dice **qué playlists tiene el equipo en disco**: buscá las rutas `playlists/<id>_<ts>.json`.
- Los archivos `.lock` indican playlists en proceso de escritura.

> ⚠️ **Advertencia sobre documentación previa:** había cuatro versiones distintas de esta regex, algunas sin `for path:`. El texto real **siempre** incluye `for path:`.

---

## 9.2 Archivos que no existen

```regex
^\[Webos Storage Manager\] File does not exist at path: (?<path>.+)$
```

**Es WARNING, y la mayoría es benigna.** Depende del archivo:

| Archivo | Ocurrencias | Veredicto |
|---|---:|---|
| `screenshots/<id>` | 45 | 🟡 La captura se subió y se borró; carrera normal |
| `timezoneChanged.json` | 29 | ✅ **Ruido.** No existe hasta que cambia la zona horaria |
| `currentlyPlayingState.json` | 16 | ✅ **Ruido.** Aparece en el primer arranque |
| `logs/<archivo de hoy>` | — | ✅ **Ruido.** Todavía no se creó |
| `media/<hash>/…` | 12 | 🔴 **Señal: falta contenido real** |
| `bg/<id>/landscape.jpg` | 8 | 🔴 **Señal: falta el fondo** |

**Regla práctica:** si la ruta arranca con `media/` o `bg/`, es contenido faltante y va a verse en pantalla. Si es un archivo de estado conocido, es ruido.

---

## 9.3 Errores de storage

| Patrón | Regex sobre `message` | Nivel | Lectura |
|---|---|---|---|
| **Parseo fallido** | `^\[WebOS Storage\] Fail parsing JSON\. File: (?<archivo>.+)$` | ERROR | **Crítico.** Primer eslabón de la pantalla negra ([04 §4.4](04-GENERAL-contenido-playlists.md)) |
| Tamaño ilegible | `^\[Webos Storage Manager\] Failed to get file size for path: (?<path>.+?) \{` | ERROR | 44 casos. El archivo está pero no se puede leer |
| Archivo no encontrado | `not found, File does not exist` | ERROR | 45 casos, casi todos de screenshots |
| Apertura fallida | `^\[Global Error Handler\] IO_ERROR: Failed to open the file` | ERROR | 46 casos. **Grave**: el medio no se puede reproducir |

> **`Fail parsing JSON` es la línea más importante de esta sección.** Un JSON de playlist corrupto deja la pantalla en negro y **se repite en cada reinicio** hasta que se vuelva a bajar el archivo.

---

## 9.4 Directorios (arranque de Tizen)

```regex
^Dir failed (?<dir>\w+)$
```

```
+0.50s  ERROR  Dir failed playlists
+0.51s  ERROR  Dir failed schedules
+0.63s  INFO   [Main] Player files checked
```

> ⚠️ **Es ERROR, pero dentro del arranque es normal.** Aparece a medio segundo del banner, antes de `Player files checked`, y es la creación de directorios de Tizen.

| Contexto | Veredicto |
|---|---|
| Dentro de los 5 s posteriores a un arranque | ✅ **Ruido** |
| Fuera de esa ventana | 🔴 **Error real**: un directorio se volvió inaccesible |

Solo 6 apariciones en 3 archivos: es poco frecuente.

---

## 9.5 Descargas

```regex
^\[Download Manager\] Files to download: (?<n>\d+)$
^\[Download Manager\] Downloading File: (?<archivo>.+?) at (?<destino>.+)$
^\[Download Manager\] Error downloading file\. Error: (?<causa>.+?) \{
^\[BackgroundManager\] Cannot download image\. Reason: (?<causa>.+)$
^\[Pending Downloads\] Checking schedule$
^\[Media Library\] Check or download in progress$
```

**Cómo leerlo:**
- `Files to download: N` al arranque te dice cuánto contenido falta bajar. En el corpus se vio `10`.
- **`Error downloading file` es el eslabón que explica un `Missing Content` posterior.** Si tenés contenido faltante sin un error de descarga previo, el archivo se bajó bien y se perdió después.
- `Cannot download image. Reason: … HTTP status: 404` apareció al bajar un fondo: el recurso no está en el servidor.
- `Check or download in progress` explica por qué un chequeo de integridad no arrancó.

---

## 9.6 Espacio en disco y limpieza

```regex
[Ff]ree space
```

Solo 39 apariciones en 12 archivos: es una señal de baja frecuencia. **No hay ningún caso de disco lleno en el corpus**, así que no hay línea base para saber qué valor es preocupante.

---

## 9.7 Reporte de archivos de máquina

```regex
^\[Machine Files Reporter\]
```

237 líneas, en ningún catálogo previo. Reporta al servidor qué archivos tiene el equipo. Útil para confirmar qué cree el player que tiene, contra lo que realmente hay.

---

## 9.8 Cómo diagnosticar "falta contenido"

```
1. ¿Hay "Missing Content: N files. Media: <medio>"?   → qué falta y cuánto
2. ¿Hay "File does not exist" con ruta media/ o bg/?  → confirmación
3. ¿Hay "Error downloading file" antes?               → nunca se bajó
4. Si no lo hay                                        → se bajó y se perdió o corrompió
5. ¿Hay "Fail parsing JSON"?                          → el archivo está pero está roto
6. ¿Hay "IO_ERROR: Failed to open the file"?          → está y no se puede leer
```

---

## 9.9 Referencia rápida

| Patrón | Regex sobre `message` | Nivel | Señal |
|---|---|---|---|
| Lectura | `^\[Webos Storage Manager\] Read operation completed for path:\s*(?<path>.+)$` | INFO | **Ruido** (solo webOS) |
| Archivo ausente | `^\[Webos Storage Manager\] File does not exist at path: (?<path>.+)$` | WARNING | Depende de la ruta |
| **Parseo fallido** | `^\[WebOS Storage\] Fail parsing JSON\. File: (?<archivo>.+)$` | ERROR | **Crítica** |
| Tamaño ilegible | `^\[Webos Storage Manager\] Failed to get file size for path: (?<path>.+?) \{` | ERROR | Media |
| Apertura fallida | `^\[Global Error Handler\] IO_ERROR: Failed to open the file` | ERROR | **Alta** |
| Directorio | `^Dir failed (?<dir>\w+)$` | ERROR | Ruido en el arranque; señal fuera de él |
| Pendientes de bajar | `^\[Download Manager\] Files to download: (?<n>\d+)$` | INFO | Media |
| Descarga | `^\[Download Manager\] Downloading File: (?<a>.+?) at (?<d>.+)$` | INFO | Baja |
| **Descarga fallida** | `^\[Download Manager\] Error downloading file\. Error: (?<c>.+?) \{` | ERROR | **Alta** |
| Imagen fallida | `^\[BackgroundManager\] Cannot download image\. Reason: (?<c>.+)$` | INFO | Media |
| Chequeo en curso | `^\[Media Library\] Check or download in progress$` | WARNING | Baja |
| Espacio libre | `[Ff]ree space` | INFO | Baja |
| Reporte de archivos | `^\[Machine Files Reporter\]` | INFO | Baja |

---

**Anterior:** [08 — Templates](08-TEMPLATES.md) · **Siguiente:** [10 — Pantalla, políticas y screenshots](10-PANTALLA-politicas-screenshots.md)
