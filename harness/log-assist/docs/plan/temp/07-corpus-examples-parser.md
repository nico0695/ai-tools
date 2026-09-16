# Corpus A — validación del parser y caracterización de webOS

Corpus: 14 archivos de `logs_examples/`, **178.415 líneas**.
Herramienta: `profile_corpus.py`, que usa `loga_core.reader` + `loga_core.parser` reales; todo
contrastado con `grep`/`awk` independientes del parser.
Referencia puesta a prueba: `docs/log-format.md` (medido sobre 157.100 líneas 100 % Tizen, una pantalla).

**Máscaras**: nombres de máquina/grupo → `<MACHINE-x>` / `<GROUP-n>`; IPs → `<IP>`; MACs → `<MAC>`;
rutas absolutas → `<PATH>`. Espaciado, corchetes y puntuación textuales.
`Machine ID` y `Machine Sync ID` se conservan: son numéricos y no son nombre de cliente.

## 0. Tabla maestra

| Archivo | Plataforma | Líneas | parse_rate | Arranques | Stack frames | Máx. chars | Player |
|---|---|---|---|---|---|---|---|
| `20260219-0.log` | webos | 33.209 | 1.000000 | 1 | 253 | 356 | 6.7.2601.2300 |
| `20260220-0.log` | webos | 34.407 | 1.000000 | 1 | 144 | 356 | 6.7.2601.2300 |
| `20260222-0.log` | webos | 35.358 | 1.000000 | 2 | 0 | 266 | 6.7.2601.2300 |
| `20260222-0 (1).log` | webos | 42.863 | 1.000000 | 5 | 15 | 356 | 6.7.2601.2300 |
| `20260223-0.log` | webos | 5.472 | 1.000000 | 2 | 0 | 231 | 6.7.2601.2300 |
| `20260223-0 (1).log` | webos | 5.472 | 1.000000 | 2 | 0 | 210 | 6.7.2601.2300 |
| `PJ - 6DIC 2.log` | webos | 3.455 | 1.000000 | 1 | 0 | 264 | 6.7.2508.0100 |
| `PJ - 6DIC 3.log` | webos | 3.666 | 1.000000 | 1 | 0 | 264 | 6.7.2508.0100 |
| `PJ - 6DIC 4.log` | webos | 3.497 | 1.000000 | 1 | 0 | 264 | 6.7.2508.0100 |
| `QMC32 QA 1.log` | tizen | 808 | 1.000000 | 1 | 0 | 1.093 | 6.4.2408.2600 |
| `QMC32 QA 2.log` | tizen | 1.144 | 1.000000 | 1 | 0 | 1.057 | 6.4.2408.2600 |
| `TimHortonsTransistmicaP1.log` | tizen | 2.599 | 1.000000 | 1 | 0 | 213 | 6.4.2408.2600 |
| `TimHortonsTransistmicaP3.log` | tizen | 3.188 | 1.000000 | 2 | 0 | 393 | 6.4.2408.2600 |
| `TimHortonsTransistmicaP4 MASTER.log` | tizen | 3.277 | 1.000000 | 2 | 0 | 213 | 6.4.2408.2600 |

## 1. ¿El parser aguanta?

**Sí. parse_rate = 1.000000 en los 14 archivos, 178.415 de 178.415 líneas.**
Ningún archivo cae por debajo de 1.0, así que no hay líneas no-matcheadas que transcribir.

Verificaciones independientes del parser, sobre los 14 archivos:

- Líneas en blanco **0**; BOM **0** (los 3 primeros bytes son siempre `32 30 32`, el año); CR **0**
  (LF puro); `wc -l` coincide exactamente con el conteo del reader → no hay última línea sin `\n`.
- Bytes no-ASCII: 530 en `PJ - 6DIC 4.log`, 2 en `TimHortonsTransistmicaP3.log`, 1 en cada
  `QMC32 QA *.log`, 0 en los otros diez. Los 14 decodifican como **UTF-8 válido**; el
  `errors="replace"` del reader nunca se ejercita.

**§2.1 se sostiene íntegramente en webOS.** Toda línea es atómica: hasta el banner de `=` y la línea
de versión llevan su propio prefijo `fecha hora.cs NIVEL` (`20260222-0.log:1-3`):

```
2026-02-22 11:10:52.68 INFO =====================================================
2026-02-22 11:10:52.71 INFO Dex Player 6.7.2601.2300
2026-02-22 11:10:52.71 INFO =====================================================
```

Consecuencia: `^Dex Player [\d.]+$` y `^={53}$` dan **0 hits** aplicados al texto crudo de los 14
archivos. Solo matchean sobre el `raw_message`, que es lo que hace `parser.count_boots`. La regla 5
de §7 es correcta, pero el documento no aclara que se aplica al **mensaje**, no a la línea.

**Ningún stack frame rompe el parser**: en webOS cada frame `at …` es una línea completa con su
timestamp y su nivel `ERROR`. Por eso hay 412 frames en el corpus y **0 líneas no-matcheadas**.
En webOS tampoco existen líneas de continuación.

## 2. Plataforma por archivo

Tomada de `[Main] Initializing Dex Player. Platform "<...>"` (línea 4 de cada arranque), no del nombre.

**La división 9 webOS / 5 Tizen de la documentación se confirma** y coincide con los nombres: los
seis `2026*` y los tres `PJ - 6DIC *` son `webos`; `QMC32 QA *` y `TimHortons*` son `tizen`.
Ver la columna *Plataforma* de §0. Evidencia: `20260222-0.log:4`
(`INFO [Main] Initializing Dex Player. Platform "webos"`), `PJ - 6DIC 2.log:4`,
`QMC32 QA 1.log:4`, `TimHortonsTransistmicaP1.log:4`.

**Tres versiones de player, no una.** §1 de `log-format.md` solo conocía `6.4.2408.2600`. Aparecen
`6.7.2601.2300` (6 webOS) y `6.7.2508.0100` (3 webOS).

## 3. Stack traces

Líneas cuyo **mensaje** matchea `^\s+at\s`, y líneas que no matchean `LINE_RE`:

| Archivo | Frames `^\s+at\s` | No-match `LINE_RE` | Líneas ERROR | Frames / ERROR |
|---|---|---|---|---|
| `20260219-0.log` | 253 | 0 | 510 | **49,6 %** |
| `20260220-0.log` | 144 | 0 | 671 | **21,5 %** |
| `20260222-0 (1).log` | 15 | 0 | 46 | **32,6 %** |
| los otros 11 | 0 | 0 | 5–137 | 0 % |

**Sí llegan al 20 % de ERROR que declara `scripts-idea/06`, y lo superan** — pero solo en 3 de los 9
archivos webOS. En los otros 6 webOS y en los 5 Tizen son 0. El fenómeno es webOS **y además**
depende de `[Global Error Handler]`, que solo existe en esos 3 archivos (§7). §6-3 de
`log-format.md` se sostiene como medición Tizen y cae como generalización.

### Stack trace completo, verbatim

Traza de dos frames con su cabecera, `20260220-0.log:22302-22304`:

```
2026-02-20 11:16:17.69 ERROR [Global Error Handler] IO_ERROR: Failed to open the file Line: undefined Column: undefined File: undefined Error: IO_ERROR: Failed to open the file
2026-02-20 11:16:17.69 ERROR     at onFailure (file://<PATH>/main.js:26500:22)
2026-02-20 11:16:17.69 ERROR     at e.value (file://<PATH>
```

Contexto inmediato, `20260220-0.log:22300-22301`:

```
2026-02-20 11:16:17.66 ERROR [Screenshots Manager] Screenshot upload failed after 3 attempts. File screenshots/1771593645907. File does not exist
2026-02-20 11:16:17.67 INFO [Screenshots Manager] Upload process finished
```

Observaciones sobre la forma:

- La cabecera es una línea `[Global Error Handler]` normal; los frames que siguen **no llevan
  componente**, solo cinco espacios y `at `.
- **Los frames vienen truncados al tope de 356 caracteres.** `:22304` corta a mitad de ruta, sin
  cerrar el paréntesis. Por eso `20260219-0.log` tiene 253 frames **todos idénticos**: es un frame
  único cortado en el mismo punto, no 253 frames distintos.
- `20260220-0.log` tiene 3 formas de frame (48 truncados, 48 `at onFailure (…:26500:22)`,
  46 `at e.value (…` truncado) → trazas de 2 frames.
- Cabecera y frames comparten la centésima exacta (`11:16:17.69`): agrupar por
  `(timestamp, nivel, contigüidad de línea)` es viable; por timestamp solo, no.

## 4. Profundidad de corchetes en webOS

Medida con el algoritmo del parser (`_GROUP_RE` desde el inicio del mensaje, tope 4).

Reparto de grupos por archivo (0 / 1 / 2 grupos), **3 y 4 grupos = 0 en los 14**:
`20260219-0.log` 340 / 20.278 / 12.591 · `20260220-0.log` 231 / 21.220 / 12.956 ·
`20260222-0.log` 41 / 23.365 / 11.952 · `20260222-0 (1).log` 85 / 28.209 / 14.569 ·
`20260223-0.log` 131 / 4.515 / 826 · `20260223-0 (1).log` 125 / 4.488 / 859 ·
`PJ - 6DIC 2/3/4.log` 118-80-154 / 3.183-3.434-3.188 / 154-152-155 ·
los 5 Tizen 14–50 / 545–2.335 / 101–1.124.

**Ni 3 ni 4 niveles: el máximo del corpus entero es 2.** Confirmado por `grep` independiente —
`^<prefijo> \[[^]]*\] ?\[[^]]*\] ?\[[^]]*\]` da **0 hits en los 14 archivos**.

### Status anidados

**No hay ninguno, en ningún archivo.** `nested statuses: {}` y `differing-from-line: 0` en los 14.
El chequeo más amplio posible —`grep -cE '\[(INFO|SUCCESS|ERROR|DEBUG|WARNING)\]'` sobre la línea
entera, en cualquier posición— da **0 en los 14 archivos, 178.415 líneas**.

- **No se encontró ningún status anidado que difiera del nivel de línea.** El caso sigue sin verse:
  no es que se haya descartado, es que no hay un solo token de nivel entre corchetes en el corpus.
- §2.3 y §2.4 describen `[MENUBOARD_TPL] [INFO]` con 41.981 líneas. Acá `MENUBOARD_TPL` es el
  componente más frecuente de webOS (6.422 en `20260219-0.log`, 9.255 en `20260222-0 (1).log`) y
  **nunca** va seguido de `[INFO]`. El segundo grupo, cuando existe, es el sub-componente directo:
  `[MENUBOARD_TPL] [OffsetsManager]`, `[MENUBOARD_TPL] [DataManager]`, `[MENUBOARD_TPL] [StoreDataManager]`.
- Esto invalida §6-2 en webOS: acá `[DataManager]` es el **segundo** grupo, tal como decía `scripts-idea/`.
- Y confirma §6-1 al revés: "como mucho 2 grupos" de `scripts-idea/` **es correcto en este corpus**.
  Los 3 grupos son un fenómeno del template del corpus Tizen del documento, no del formato.
- Las reglas 3 y 4 de §7 siguen siendo seguras: no se rompen, simplemente no se ejercitan acá.

## 5. Recursos en webOS

Fuente: `CPU: <n>%. Used RAM: <n> Mb`.

| Archivo | Plat. | n | CPU | RAM (Mb) | Cadencia dominante |
|---|---|---|---|---|---|
| `20260219-0.log` | webos | 131 | 13–77 % | 1.150–1.288 | 300 s (90) / 299 s (38) |
| `20260220-0.log` | webos | 196 | 13–73 % | 1.123–1.196 | 300 s (135) / 299 s (57) |
| `20260222-0.log` | webos | 151 | 14–15 % | 1.123–1.223 | 300 s (97) / 299 s (51) |
| `20260222-0 (1).log` | webos | 180 | 14–15 % | 1.135–1.224 | 300 s (112) / 299 s (60) |
| `20260223-0.log` | webos | 102 | 6–75 % | 1.064–1.176 | 300 s (67) / 299 s (33) |
| `20260223-0 (1).log` | webos | 102 | 7–74 % | 1.118–1.191 | 300 s (76) / 299 s (24) |
| `PJ - 6DIC 2.log` | webos | 55 | 11–12 % | 1.141–1.171 | 300 s (39) / 299 s (15) |
| `PJ - 6DIC 3.log` | webos | 55 | 11–12 % | 1.137–1.172 | 300 s (34) / 299 s (20) |
| `PJ - 6DIC 4.log` | webos | 53 | 11–12 % | 1.129–1.164 | 300 s (30) / 299 s (19) |
| `QMC32 QA 1.log` | tizen | 14 | 10–**99** % | 781–885 | 60 s (8) / 59 s (5) |
| `QMC32 QA 2.log` | tizen | 14 | 10–**99** % | 773–876 | 60 s (8) / 59 s (5) |
| `TimHortonsTransistmicaP1.log` | tizen | 237 | 4–**98** % | 693–847 | 60 s (185) / 59 s (51) |
| `TimHortonsTransistmicaP3.log` | tizen | 264 | 4–**98** % | 648–861 | 60 s (236) / 59 s (26) |
| `TimHortonsTransistmicaP4 MASTER.log` | tizen | 241 | 5–**98** % | 688–855 | 60 s (234) / 59 s (5) |

**`scripts-idea/03` se sostiene, con precisión llamativa.**

- Cadencia webOS 300 s confirmada en los 9 (300 s o 299 s en ~99 % de los deltas); Tizen 60 s
  confirmada en los 5, coincidiendo con §4 de `log-format.md`.
- RAM webOS **1.064–1.288 Mb** (mínimo en `20260223-0.log`, máximo en `20260219-0.log`) y RAM Tizen
  **648–885 Mb** (mínimo en `TimHortonsTransistmicaP3.log`, máximo en `QMC32 QA 1.log`): los dos
  rangos coinciden **exactamente** con los declarados.
- Corolario: **§6-8 cae.** Dice que el piso de 648 Mb es falso porque 12,6 % de sus muestras caen
  debajo; en estos 5 Tizen **ninguna** baja de 648. El desacuerdo es de corpus, no de referencia.

### El pico de CPU de 98 % post-arranque: **aparece, y es de Tizen**

Picos: `TimHortonsTransistmicaP1.log:31` 98 % a +6 s · `…P3.log:26` 98 % a +9 s y `:2748` 98 % a
+8 s del 2.º arranque · `…P4 MASTER.log:33` 98 % a +8 s y `:3191` 98 % a +9 s del 2.º arranque ·
`QMC32 QA 1.log:26` **99 %** en la misma ventana del arranque · `QMC32 QA 2.log:28` **99 %** a +8 s.

En los 5 archivos Tizen la **primera muestra de telemetría tras cada arranque es el máximo del
archivo**, 98–99 %, dentro de los 10 s; la segunda ya cae a 27–33 %.
En webOS el pico post-arranque existe pero es menor: 77 % a +5 s (`20260219-0.log:25981`),
73 % a +12 s (`20260220-0.log:14982`), 74,25 % a +7 s (`20260223-0 (1).log:2207`).

**§6-9 cae en los dos sentidos**: el 98 % de `scripts-idea/` es exacto en Tizen y tiene un análogo de
~75 % en webOS. Confirma, en cambio, §4 y la regla 10 de §7: medir contra el rango observado.

## 6. Ventana de época

**No hay ninguna línea de época en ningún archivo, ni webOS ni Tizen.**

- `parser.epoch_window()` → 0 en los 14. `grep -cE '^(1969|1970)-'` → 0 en los 14.
- `[Tizen App] Device time:` aparece 1–2 veces en cada archivo Tizen y **0 veces** en los 9 webOS;
  no existe un equivalente webOS con ese nombre.
- Rangos reales: `20260219-0.log` 2026-02-18 23:59:51 .. 2026-02-19 11:02:49 (spillea 9 s del día
  previo, coherente con §2.7); `PJ - 6DIC 2.log` 2025-11-19 11:30:07 .. 16:04:15.

**Qué se puede afirmar y qué no.** Hay 12 arranques Tizen y 18 webOS y **ninguno** cruza la ventana.
La pregunta "¿es solo de Tizen?" **no se puede responder con este corpus**: no se observó en ninguna
plataforma, así que no hay evidencia ni a favor ni en contra de la exclusividad. Lo que sí queda
demostrado es que **no es universal en Tizen**: depende del arranque en frío del dispositivo y estos
archivos no lo capturan. La regla 6 de §7 sigue siendo necesaria como defensa, pero no se valida acá.

## 7. Componentes solo de webOS

| Componente | 19 | 20 | 22 | 22(1) | 23 | 23(1) | 6DIC 2/3/4 | los 5 Tizen |
|---|---|---|---|---|---|---|---|---|
| `[Webos Storage Manager]` | 3.752 | 2.798 | 4.757 | 5.580 | 318 | 300 | 180/176/181 | **0** |
| `[Global Error Handler]` | 253 | 96 | **0** | 15 | **0** | **0** | **0** | **0** |
| `[Channel Manager]` | 2.993 | 2.922 | 3.907 | 4.820 | 15 | 15 | 207/207/207 | **0** |

Los tres son **exclusivos de webOS**: 0 en los 5 Tizen. Confirma §6-14 y §6-16 en lo que hace a
`[Webos Storage Manager]` y `[Global Error Handler]`. Ejemplos verbatim (las rutas son relativas
internas del player, no absolutas, y se conservan):

`20260219-0.log:8`
```
2026-02-18 23:59:55.64 INFO [Webos Storage Manager] Read operation completed for path: media/39/391c99fb617c3e5cf6eac3bee4acd8494ab645b6/timestamp.1998399
```

`20260220-0.log:11283`
```
2026-02-20 06:09:18.23 ERROR [Global Error Handler] Failed to play video with ID c-1-video-one: The play() request was interrupted by a new load request. https://goo.gl/LdLk22 Line: undefined Column: undefined File: undefined Error: Failed to play video with ID c-1-video-one: The play() request was interrupted by a new load request. https://goo.gl/LdLk22
```

`20260219-0.log:1` y `:3`
```
2026-02-18 23:59:51.99 INFO [Channel Manager] playNextMedia: Transitioning media  {"previous":"7PV 1","show":"tpl-menuboard.3.4.2601.2600-STORE"}
2026-02-18 23:59:52.40 INFO [Channel Manager] preloadNextMedia:  {"nextController":"LonelyVideoComponent","media":"7PV 1"}
```

`Read operation completed for path` es **11,3 %** de `20260219-0.log`, **13,4 %** de `20260222-0.log`
y **4,6 %** de `PJ - 6DIC 3.log`: el "~10 % del volumen" de `scripts-idea/` **se sostiene** como
orden de magnitud en webOS, y §6-14 queda confirmado en sus dos mitades.

### Otras formas que §6 daba por 0 y que sí aparecen en webOS

| §6 | Forma | Dónde | Ejemplo verbatim |
|---|---|---|---|
| 16 | `Member <IP> is not active` | 5 webOS + 2 Tizen; 41 en `20260220-0.log` | `INFO [Node] [Sync] Member <IP> is not active` |
| 16 | `Next candidates check` | solo `20260220-0.log`, 157 | `INFO [Node] [Sync] Next candidates check in 60 seconds` |
| 16 | `Clearing current playlist` | los 9 webOS; 69 en `20260222-0 (1).log` | `INFO [Playlist Manager] Clearing current playlist` |
| 16 | `preloadNextMedia` / `playNextMedia` | webOS, dentro de `[Channel Manager]` | ver arriba |
| 16 | `NodeJs service is running` | los 9 webOS; 660 en `20260220-0.log` | `SUCCESS [Node Server Manager] webos NodeJs service is running` |
| 16 | `Missing Content` | 2 webOS + 4 Tizen | `TimHortonsTransistmicaP3.log:68` |
| 12 | `[Input Manager] … enabled` | los 9 webOS | `INFO [Input Manager] Remote Control enabled` · `INFO [Input Manager] Panel enabled` |

**§6-12 cae en webOS**: la regex de `scripts-idea/` `(Remote Control|Panel) enabled` matchea
literalmente. La forma del documento — `Remote Control Enabled` con mayúscula y `Panel Unlocked`
en SUCCESS — solo aparece en los 3 `TimHortons*`; los `QMC32 QA *` no tienen ninguna de las dos.

**§6-10 cae en webOS**: `20260223-0.log` tiene **79** `Heartbeat Sync failed. Status: Error: timeout
of Nms exceeded` frente a 6 `Network Error`. El documento afirma "cero timeouts"; en webOS son mayoría.

**§6-13 se sostiene**: `All tasks were finished` aparece 1 vez en 3 archivos y 0 en los otros 11.

## 8. Largo de línea y encoding

**BOM: 0 en los 14. CRLF: 0 en los 14. UTF-8 válido: los 14.** Máximos de caracteres en la tabla de §0.
No-ASCII solo en 4 archivos: `PJ - 6DIC 4.log` (530 bytes), `TimHortonsTransistmicaP3.log` (2),
`QMC32 QA 1.log` (1), `QMC32 QA 2.log` (1).

- **El techo de 325 de §6-6 cae, pero por poco y sin DEBUG**: 8 de los 9 webOS están entre 210 y 266,
  y los 3 que llegan a **356** lo hacen por una única forma, `[Global Error Handler] Failed to play
  video with ID …` (`20260219-0.log:2088`, 356 chars). No hay JSON crudo largo en webOS.
- El techo real del corpus es Tizen con DEBUG, igual que en el documento: **1.093** chars en
  `QMC32 QA 1.log:478`, un `DEBUG [Player] reportReadyState array de playlist [...]` con un array
  JSON de nombres de playlist. Es un orden de magnitud menos que los 5.681 del documento, pero la
  regla 11 de §7 (truncar a 300, esperar más de 5.000) sigue siendo la correcta.
- `TimHortonsTransistmicaP3.log:68` llega a 393 chars y trae los 2 bytes no-ASCII del archivo
  (`í`, `é` en nombres de media). Nótese el **doble espacio** antes de `Missing`:
  ```
  2025-09-19 16:24:34.94 ERROR [Player] Checking playlist failed  Missing Content: 8 files. Media: …
  ```
- Los 530 bytes no-ASCII de `PJ - 6DIC 4.log` son `ñ` dentro de un nombre de componente-template:
  `[EMBEBIDO 4V4 Acompañantes 2m50s]`. **Un nombre de componente puede llevar no-ASCII y espacios.**
  Refuerza la regla 4 de §7 (nunca whitelist).
- **§2.1 "ASCII only" cae**: 4 de 14 archivos traen UTF-8 multibyte. Nunca inválido, pero cualquier
  corte por bytes rompería un carácter.

## 9. Identidad

| Archivo | Machine | Machine ID | Sync ID | Grupo | Client IP |
|---|---|---|---|---|---|
| `20260219-0.log` | `<MACHINE-A>` | 98311 | 1 | `<GROUP-1>` | `<IP>.107` |
| `20260222-0.log` | `<MACHINE-A>` | 98311 | 1 | `undefined` | `<IP>.107` |
| `20260220-0.log` | `<MACHINE-B>` | 98305 | 2 | `<GROUP-1>` | `<IP>.106` |
| `20260222-0 (1).log` | `<MACHINE-B>` | 98305 | 2 | `<GROUP-1>` | `<IP>.106` |
| `20260223-0.log` | `<MACHINE-C>` | 97844 | 2 | `<GROUP-2>` | `<IP>.106` |
| `20260223-0 (1).log` | `<MACHINE-D>` | 97845 | 3 | `<GROUP-2>` | `<IP>.105` |
| `PJ - 6DIC 2.log` | `<MACHINE-E>` | 104355 | 2 | `<GROUP-3>` | `<IP>.11` |
| `PJ - 6DIC 3.log` | `<MACHINE-F>` | 104357 | 3 | `<GROUP-3>` | `<IP>.12` |
| `PJ - 6DIC 4.log` | `<MACHINE-G>` | 104358 | 4 | `<GROUP-3>` | `<IP>.13` |
| `QMC32 QA 1.log` | `<MACHINE-H>` | 43168 | 2 | `<GROUP-4>` | `<IP>.73` |
| `QMC32 QA 2.log` | `<IP> <MAC>` | 47940 | 1 | `<GROUP-4>` | `<IP>.147` |
| `TimHortonsTransistmicaP1.log` | `<MACHINE-J>` | *(ausente)* | *(ausente)* | *(ausente)* | *(ausente)* |
| `TimHortonsTransistmicaP3.log` | `<MACHINE-K>` | 90917 | 3 | `<GROUP-5>` | `<IP>.207` |
| `TimHortonsTransistmicaP4 MASTER.log` | `<MACHINE-L>` | *(ausente)* | *(ausente)* | *(ausente)* | *(ausente)* |

### Los pares ` (1)` — el hallazgo que contradice §2.7

**`20260222-0.log` y `20260222-0 (1).log` son pantallas DISTINTAS.** `Machine ID: 98311` vs `98305`;
`Serial Number:` distintos; `Client IP:` `.107` vs `.106`; `Machine Sync ID:  1` vs `2`. Cubren el
mismo día y el mismo grupo sync: no es una continuación, es la pantalla vecina.
Además `20260222-0.log` (98311) es la **misma** pantalla que `20260219-0.log`, y
`20260222-0 (1).log` (98305) la misma que `20260220-0.log`.

**`20260223-0.log` y `20260223-0 (1).log` también son pantallas distintas.** `Machine ID: 97844` vs
`97845`, Sync ID 2 vs 3, IP `.106` vs `.105`, mismo grupo. Los dos tienen **exactamente 5.472 líneas**
y rangos horarios casi idénticos: el tamaño igual invita a deduplicar, y la identidad prueba que sería
un error.

Este es exactamente el caso de `scripts-idea/01` (archivos ` (1)` que son pantallas distintas) y
**no** el de §2.7 (carpeta ` (1)`, misma pantalla). Las dos situaciones son reales y **este corpus
prueba la peligrosa**. La regla 8 de §7 es la que sobrevive; §2.7 no debería presentar el caso
"misma pantalla" como el típico.

### Pantallas por grupo

`<GROUP-1>` (webOS 6.7.2601.2300): **2 pantallas en 4 archivos** — A (`20260219-0`, `20260222-0`) y
B (`20260220-0`, `20260222-0 (1)`); declara **7 miembros** en `Members:`. `<GROUP-2>` (webOS):
2 pantallas, 1 archivo cada una. `<GROUP-3>` (webOS 6.7.2508.0100): 3 pantallas, 1 archivo cada una,
mismo día y rango horario. `<GROUP-4>` (Tizen): 2 pantallas distintas. `<GROUP-5>` (Tizen): solo P3
emite bloque de sync. **Ninguna pantalla del corpus es la del corpus de `log-format.md`.**

### Dos casos que rompen supuestos de identidad

1. **`Machine:` puede no ser un nombre.** `QMC32 QA 2.log:32` repite el valor de `Hostname:` (`:29`):
   ```
   2025-10-09 12:00:51.70 INFO [Server Manager] Hostname: <IP> <MAC>
   2025-10-09 12:00:52.79 INFO [Server Manager] Machine: <IP> <MAC>
   ```
   `QMC32 QA 1.log:32` sí trae nombre. La regla 8 de §7 debe tolerar un `Machine:` con forma
   `<IP> <MAC>` y no tratarlo como nombre de pantalla.
2. **Dos archivos no tienen bloque de estado**: `TimHortonsTransistmicaP1.log` y
   `…P4 MASTER.log` tienen `^={54}$` = 0 y ningún `Machine ID:`. Ahí la identidad solo sale del
   `Machine:` del handshake.

### Split-brain: §6-15 cae en webOS

`Members:` aparece 12 veces en webOS y 2 en Tizen. De las 12 webOS, **5 traen más de un `[Master]`**
y **1 no trae ninguno** → **41,7 %**, por encima del 25 % de `scripts-idea/`.

`20260219-0.log:32891` — tres masters en una línea (nótese el **espacio final**):
```
2026-02-19 10:54:49.81 INFO [Player] [Sync] Version: 1.9.1 - Group: <GROUP-1> - Members: <IP> [Master] <IP> <IP> <IP> <IP> <IP> [Master] <IP> [Master] 
```
`20260222-0.log` — el caso contrario, grupo vacío y sin master:
```
2026-02-22 11:11:01.42 INFO [Player] [Sync] Version: 1.9.1 - Group: undefined - Members: 
```

§6-15 ("0 %: 17 de 18 `Members:` con exactamente un `[Master]`") es cierto solo en Tizen.
Las filas del bloque sync mantienen la forma de §3.3 **verbatim** (`20260219-0.log:32893-32895`):
doble espacio antes de `(MASTER)`, espacio final en las filas no-master, y los dos formatos de
timestamp conviviendo en la misma fila (`Playlist: 67161 [2026-02-16T17:05:57.217Z]` con dos puntos
y `Z`, frente a los puntos de `Playlist To Change:`).

## 10. Veredicto sobre `docs/log-format.md`

### Se sostiene en webOS

§2.1 (formato, atomicidad, un espacio, centésimas, LF, sin BOM, sin blancos, `WARNING` nunca `WARN`)
sobre 178.415/178.415 líneas · §2.2 nivel posicional · §2.5 `^={53}$` = 2 × arranques y `^={54}$` =
2 × bloques de estado + cierres de sync, con la apertura de sync que no matchea `^={54}$`, verificado
en los 14 por separado · §2.7 "la identidad viene del contenido" · §3.2 handshake · §3.3 forma de los
bloques con sus dobles espacios y espacios finales · §4 cadencias · reglas 1, 2, 7, 8, 9, 10, 11 y 12 de §7.

### Cae o se limita en webOS

| § | Afirmación | Qué pasa acá |
|---|---|---|
| 1 | un solo player `6.4.2408.2600` | 3 versiones, dos de ellas 6.7.x |
| 2.1 | "ASCII only" | 4 de 14 archivos con UTF-8 multibyte (`ñ`, `í`, `é`) |
| 2.3 / 2.4 / 6-2 | `[MENUBOARD_TPL] [INFO]`, 3 grupos, status anidado | **0 status anidados en 178.415 líneas**; profundidad máx. 2; `[DataManager]` es el 2.º grupo |
| 2.5 | `^Dex Player [\d.]+$` | Matchea sobre el mensaje, nunca sobre la línea; el documento no lo aclara |
| 2.6 | ventana de época | 0 líneas en 30 arranques; **no verificable acá** |
| 2.7 | ` (1)` cuelga de la carpeta, misma pantalla | Los dos pares ` (1)` son **pantallas distintas** |
| 6-3 | stack traces 0 %, fenómeno webOS | Confirmado como webOS: 21,5 %–49,6 % de ERROR en 3 archivos |
| 6-6 | techo de 325 chars sin DEBUG | 356 en 3 archivos webOS, por `[Global Error Handler]` |
| 6-8 | el piso de RAM 648 Mb es falso | En estos 5 Tizen **ninguna** muestra baja de 648 |
| 6-9 | CPU máx. 54 %, el 98 % no existe | 98–99 % post-arranque en los **5** Tizen; ~75 % en webOS |
| 6-10 | cero timeouts de heartbeat | 79 timeouts en `20260223-0.log`, mayoría sobre network error |
| 6-12 | `(Remote Control\|Panel) enabled` no matchea nada | Matchea literalmente en los 9 webOS |
| 6-15 | 0 % de split-brain | 5 de 12 snapshots webOS con más de un `[Master]` (41,7 %) |
| 6-16 | 8 formas "todas 0" | 5 de las 8 aparecen en webOS, una con 660 ocurrencias |

### No verificable con este corpus

La ventana de época (§2.6): ausente en las dos plataformas — no hay evidencia de que sea exclusiva de
Tizen, solo de que no es universal en Tizen. Un status anidado que difiera del nivel de línea (§2.4):
**el caso sigue sin observarse nunca**. La cascada de pantalla negra y el segundo tenant: fuera de alcance.
