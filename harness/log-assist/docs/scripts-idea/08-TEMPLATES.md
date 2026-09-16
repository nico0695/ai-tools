# 08 — Templates y menuboards

> Sección **específica**. Dominio `TPL`.
> Responde: ¿el menuboard carga bien? ¿los precios están actualizados? ¿por qué se ve desactualizado?

---

## 8.1 Por qué tiene su propia sección

`[MENUBOARD_TPL]` y sus submódulos son **~69.000 líneas, el 39 % del corpus**. Tienen vocabulario propio y, a diferencia del resto del log, traen **datos de negocio**: precios, SKUs, combos, faltantes.

Los componentes:

| Componente | Líneas | Qué hace |
|---|---:|---|
| `[MENUBOARD_TPL]` | 30.173 | Ciclo de vida del template |
| `[MENUBOARD_TPL] [OffsetsManager]` | 16.266 | Posicionamiento en pantalla |
| `[MENUBOARD_TPL] [StoreDataManager]` | 12.657 | Datos de la tienda |
| `[MENUBOARD_TPL] [DataManager]` | 10.951 | Precios y SKUs |
| `[Template Controller]` | 1.462 | Precarga |
| `[TEMPLATE]` | 300 | Variante genérica |
| `[EMBEBIDO …]` | ~1.270 | Templates embebidos, con el nombre en el componente |

---

## 8.2 El ciclo de un template

Secuencia real completa:

```
INFO  [Channel Manager] playNextMedia: Transitioning media {"show":"tpl-menuboard.3.4.2601.2600-STORE"}
INFO  [MENUBOARD_TPL] START_TPL received
INFO  [MENUBOARD_TPL] On Load TPL
INFO  [MENUBOARD_TPL] ****** TEMPLATE STARTED ******
INFO  [MENUBOARD_TPL] [OffsetsManager] userAgent: Mozilla/5.0 (Web0S; …)
INFO  [MENUBOARD_TPL] [OffsetsManager] platform: WEBOS
INFO  [MENUBOARD_TPL] [OffsetsManager] Found 16 offsets in file.
INFO  [MENUBOARD_TPL] 1 assets loaded
INFO  [MENUBOARD_TPL] Loaded fonts: ["Grota-ExtraBold"]
INFO  [MENUBOARD_TPL] Metadata {"Coordenadas":"","Group":{},"Id":98305,"Server":"<URL>", …}
INFO  [MENUBOARD_TPL] [StoreDataManager] TPL Mode: STORE
INFO  [MENUBOARD_TPL] [DataManager] SKUs found in configs: 10
INFO  [MENUBOARD_TPL] [DataManager] Local Storage found: 310 prices | 0 outages | 0 combos
INFO  [MENUBOARD_TPL] [StoreDataManager] Fetch started...
INFO  [MENUBOARD_TPL] [StoreDataManager] Fetching from: <URL>
INFO  [MENUBOARD_TPL] Fetch response: 200 - OK
INFO  [MENUBOARD_TPL] [StoreDataManager] Updated pricing source: No
INFO  [MENUBOARD_TPL] [DataManager] Data fetched. Updating local storage
…
INFO  [MENUBOARD_TPL] STOP_TPL received
```

| Hito | Regex sobre `message` |
|---|---|
| Arranca | `^\[(?<tpl>[^\]]+)\] START_TPL received$` |
| Carga | `^\[(?<tpl>[^\]]+)\] On Load TPL$` |
| **Iniciado** | `^\[(?<tpl>[^\]]+)\] \*+ TEMPLATE STARTED \*+$` |
| Termina | `^\[(?<tpl>[^\]]+)\] STOP_TPL received$` |
| Precarga | `^\[Template Controller\] Preloading media (?<media>.+)$` |

**Cómo leerlo:** el par `START_TPL` / `STOP_TPL` debería estar balanceado. En el corpus hay 3.073 START contra 3.932 STOP, y esa diferencia es esperable porque el log arranca y termina a mitad de ciclo. **Un desbalance grande sí es señal** de templates que arrancan y no cierran.

---

## 8.3 Los datos de negocio

Acá está lo que diferencia esta sección del resto del log:

```regex
^\[(?<tpl>[^\]]+)\] \[DataManager\] SKUs found in configs:\s*(?<skus>\d+)$
^\[(?<tpl>[^\]]+)\] \[DataManager\] Local Storage found: (?<precios>\d+) prices \| (?<faltantes>\d+) outages \| (?<combos>\d+) combos$
^\[(?<tpl>[^\]]+)\] \[StoreDataManager\] TPL Mode: (?<modo>\w+)$
^\[(?<tpl>[^\]]+)\] \[StoreDataManager\] Updated pricing source: (?<actualizado>\w+)$
```

**Cómo leerlo:**

| Campo | Valor observado | Qué significa |
|---|---|---|
| `SKUs found in configs` | 8, 10 | Cuántos productos tiene configurados el template |
| `prices` | 310 | Precios en el storage local |
| `outages` | 0 | **Productos marcados sin stock.** Un valor alto explica un menú con faltantes |
| `combos` | 0 | Combos configurados |
| `TPL Mode` | `STORE` | Modo de operación |
| `Updated pricing source` | `No` | **`No` significa que usó el caché local**, no datos frescos |

> **Para el reclamo "el menú muestra precios viejos":** buscá `Updated pricing source`. Si dice `No` de forma persistente, el template nunca está trayendo precios nuevos aunque el fetch dé 200.

---

## 8.4 La obtención de datos

```regex
^\[(?<tpl>[^\]]+)\] \[StoreDataManager\] Fetch started\.\.\.$
^\[(?<tpl>[^\]]+)\] \[StoreDataManager\] Fetching from:\s*(?<url>.+)$
^\[(?<tpl>[^\]]+)\] Fetch response: (?<status>\d+) - (?<texto>.+)$
^\[(?<tpl>[^\]]+)\] \[DataManager\] Data fetched\. Updating local storage$
```

**Cadena de diagnóstico para "el menuboard no actualiza":**

```
1. ¿Hay "Fetch started..."?              → si no, ni lo intentó
2. ¿Qué da "Fetch response"?             → 200 es OK; otro código es el problema
3. ¿Hay "Data fetched. Updating local storage"?  → si no, trajo datos pero no los guardó
4. ¿Qué dice "Updated pricing source"?   → "No" = sigue usando el caché
```

En el corpus, las 2.726 respuestas observadas fueron todas `200 - OK`, y aun así `Updated pricing source` dio `No`. **El fetch exitoso no garantiza precios nuevos.**

---

## 8.5 Metadata del template

```regex
^\[(?<tpl>[^\]]+)\] Metadata (?<json>\{.*)$
```

Trae un JSON con la identidad del template y de la tienda: `Id`, `Server`, `Coordenadas`, `Group`, y según el caso `CustomerId`, `Tags` y `Products`.

> ⚠️ **Advertencia sobre documentación previa:** el catálogo original buscaba `[TEMPLATE] Metadata received` con la palabra `content`. **Ese texto no existe.** El real es `[MENUBOARD_TPL] Metadata {…}` (4.071 apariciones) y `[TEMPLATE] Metadata …` (147), sin la palabra `received` ni `content`.

---

## 8.6 Templates embebidos

Los `EMBEBIDO` traen el nombre y la duración **en el propio componente**:

```
[EMBEBIDO 4V3 Crea tu pizza 1m8s]
[EMBEBIDO 4V2 Especialidad 2m45s]
[EMBEBIDO 4V4 Acompañantes 2m50s]
```

```regex
^\[EMBEBIDO (?<nombre>.+?) (?<duracion>\d+m\d+s)\]
```

Es una fuente gratis para saber qué piezas de contenido están rotando y cuánto duran.

---

## 8.7 Fallas de template

| Patrón | Regex sobre `message` | Lectura |
|---|---|---|
| Reinicio por timeout | `restart tpl timeout` | El template se colgó y se reinició. 276 casos en 3 archivos |
| Offsets | `^\[(?<tpl>[^\]]+)\] \[OffsetsManager\] Found (?<n>\d+) offsets in file\.$` | Si da 0, el template se ve mal posicionado |
| Assets | `^\[(?<tpl>[^\]]+)\] (?<n>\d+) assets loaded$` | Si da 0, faltan recursos |

> **`restart tpl timeout` con 276 apariciones concentradas en 3 archivos** es el patrón de un template inestable en equipos puntuales, no un problema general.

---

## 8.8 Referencia rápida

| Patrón | Regex sobre `message` | Señal |
|---|---|---|
| Template iniciado | `^\[(?<tpl>[^\]]+)\] \*+ TEMPLATE STARTED \*+$` | Media |
| START / STOP | `^\[(?<tpl>[^\]]+)\] (?<ev>START_TPL\|STOP_TPL) received$` | Media |
| Metadata | `^\[(?<tpl>[^\]]+)\] Metadata (?<json>\{.*)$` | Alta |
| **Precios y faltantes** | `\[DataManager\] Local Storage found: (?<p>\d+) prices \| (?<o>\d+) outages \| (?<c>\d+) combos$` | **Alta** |
| SKUs | `\[DataManager\] SKUs found in configs:\s*(?<n>\d+)$` | Media |
| **Precios actualizados** | `\[StoreDataManager\] Updated pricing source: (?<v>\w+)$` | **Alta** |
| Modo | `\[StoreDataManager\] TPL Mode: (?<modo>\w+)$` | Baja |
| Fetch | `\[StoreDataManager\] Fetch started\.\.\.$` | Media |
| Respuesta | `^\[(?<tpl>[^\]]+)\] Fetch response: (?<status>\d+) - (?<t>.+)$` | **Alta** |
| Datos guardados | `\[DataManager\] Data fetched\. Updating local storage$` | Alta |
| Reinicio por timeout | `restart tpl timeout` | **Alta** |
| Offsets | `\[OffsetsManager\] Found (?<n>\d+) offsets in file\.$` | Baja |
| Precarga | `^\[Template Controller\] Preloading media (?<media>.+)$` | Baja |
| Embebido | `^\[EMBEBIDO (?<nombre>.+?) (?<dur>\d+m\d+s)\]` | Baja |

---

**Anterior:** [07 — Cluster](07-SYNC-cluster.md) · **Siguiente:** [09 — Storage y archivos](09-STORAGE-archivos.md)
