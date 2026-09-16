# 07 — Cluster / Sync Group

> Sección **específica**. Dominio `SYNC`. Es el dominio más grande del catálogo.
> Responde: ¿quién es el master? ¿están todas las pantallas en la misma playlist? ¿hay split-brain?

---

## 7.1 Los dos componentes del sync

No son lo mismo y confundirlos lleva a diagnósticos equivocados:

| Componente | Qué es | Líneas |
|---|---|---:|
| `[Node] [Sync]` | **El nodo local de sincronización.** Descubre miembros, decide el master, manda las ráfagas | 2.006 |
| `[Player] [Sync]` | **El player recibiendo órdenes** de ese nodo | 14.985 |
| `[Server Manager]` | **El servidor central.** No tiene nada que ver con el sync | 6.255 |

> ⚠️ `Heartbeat Sync failed` viene de `[Server Manager]`: es el servidor, **no** el grupo sync. Ver [05 §5.2](05-GENERAL-red-servidor.md).

---

## 7.2 La línea que más información da del cluster

Una sola línea te dice el grupo entero:

```regex
^\[Player\] \[Sync\] Version: (?<version>[\d.]+) - Group: (?<grupo>.+?) - Members: (?<miembros>.*)$
```

```
[Player] [Sync] Version: 1.9.1 - Group: TAR PLVE | Mall Plaza Vespucio | 7PV | TPL - Members: <IP6> <IP5> [Master] <IP1> [Master] <IP3> <IP4> <IP2> [Master]
```

De acá sacás:
- **La versión de Dex Sync** (`1.9.1`, `1.7.2` o `1.6.21` en el corpus).
- **El nombre del grupo**, que suele traer tienda y ubicación.
- **La lista de miembros por IP**.
- **Quiénes están marcados como `[Master]`** ← esto es lo importante.

### Detectar split-brain: contar los `[Master]`

**Esta es la forma correcta, y se ve en un solo archivo.**

```regex
\[Master\]        ← contar cuántas veces aparece en la línea Members
```

| Masters | Líneas en el corpus | Diagnóstico |
|---:|---:|---|
| **1** | 18 | ✅ Normal |
| **2** | 2 | 🔴 **Split-brain**: dos nodos se creen master |
| **3** | 3 | 🔴 **Split-brain severo** |
| **0** | 1 | 🔴 **Grupo sin master**: nadie coordina |

> **El 25 % de los snapshots del corpus mostró un cluster mal formado.** No es un caso raro.

> ⚠️ **Lo que NO funciona:** la documentación previa proponía detectar split-brain por la tasa de comandos PLAY (por ejemplo, más de 4 por minuto). **Eso da falso positivo permanente.** El intervalo entre PLAY es la duración del medio: una pantalla sana con clips de 15 segundos emite 4 PLAY por minuto todo el día. Medido: el p50 va de 4,4 s a 60 s según la pantalla.

---

## 7.3 El bloque SYNC GROUP INFO

Es el snapshot más completo del cluster. Aparece de forma **esporádica**, no periódica: en el corpus, el tiempo entre bloques va de 4 minutos a 6,4 horas.

```
INFO ======================================================                    ← 54 signos "="
INFO [Player] [Sync] Version: 1.9.1 - Group: … - Members: …
INFO ===================SYNC GROUP INFO====================
INFO <IP6> | PLAYING | Playlist: 67161 [2026-02-16T17:05:57.217Z] | Schedule:  [] | Playlist To Change: [67161_2026-02-16T17.05.57.217.json]
INFO <IP5> | PLAYING | Playlist: 67161 [2026-02-16T17:05:57.217Z] | Schedule:  [] | Playlist To Change: [67161_…json,67161_…json]  (MASTER)
INFO <IP1> | PLAYING | Playlist: 67161 [2026-02-16T17:05:57.217Z] | Schedule:  [] | Playlist To Change: […]  (MASTER)
INFO ======================================================                    ← 54 signos "="
```

**Variante con calendario asignado** (el campo `Schedule` trae id y timestamp propios):

```
INFO <IP> | PLAYING | Playlist: 59711 [2025-09-18T14:50:17.88Z] | Schedule: 4092 [2025-09-19T…Z] | Playlist To Change: [59711_…json]  (MASTER)
                                                                  └── id ──┘ └──── ts ─────┘
```

### Cómo parsearlo

| Elemento | Regex sobre `message` |
|---|---|
| Apertura y cierre | `^={54}$` |
| Header de la tabla | `^=+SYNC GROUP INFO=+$` |
| **Fila de miembro** | `^(?<ip>\d{1,3}(?:\.\d{1,3}){3}) \| (?<estado>[A-Z]+) \| Playlist: (?<playlist>\d+\|undefined) \[(?<plTs>[^\]]*)\] \| Schedule:\s*(?<schedId>\d+)?\s*\[(?<schedTs>[^\]]*)\] \| Playlist To Change: \[(?<pending>[^\]]*)\]\s*(?<master>\(MASTER\))?` |

> ⚠️ **Tres advertencias sobre la fila. Cada una hace desaparecer miembros del análisis:**
> 1. **Tiene que aceptar `undefined` como playlist.** Existe en los logs (`Playlist: undefined []`, en un miembro `READY`). Si tu regex exige `\d+`, esa fila no matchea y **el miembro desaparece** — justo el que está en estado anómalo.
> 2. **El campo `Schedule` tiene dos formas:** vacío (`Schedule:  []`, 105 filas) y **con id y timestamp** (`Schedule: 4092 [2025-09-19T…Z]`, 4 filas). Si tu regex solo contempla la primera, **perdés exactamente las pantallas que sí tienen calendario asignado**, que suelen ser las más interesantes. Por eso `(?<schedId>\d+)?` va como opcional.
> 3. **Dejá el estado abierto (`[A-Z]+`), no lo cierres en un enum.** Observados: `PLAYING` (105) y `READY` (4). La documentación previa incluía `NEW`, que nunca apareció.

> ⚠️ **El cierre del bloque (54 `=`) se parece al banner de arranque (53 `=`).** Se distinguen por la cantidad exacta de signos. Ver [01 §1.5](01-LECTURA-BASE.md).

### Variante corta

**13 de los 35 bloques no traen tabla**: solo la apertura, la línea `Version/Group/Members` y el cierre. Tu parser tiene que tolerarlo.

### Cómo evaluar consistencia

> **Evaluá por bloque, no por ventana de tiempo.** Cada bloque ya es un snapshot atómico y coherente de todos los miembros. Poner una ventana de 5, 15 o 60 minutos no tiene sentido cuando los bloques aparecen cada 4 minutos o cada 6 horas.

Dentro de un bloque, compará entre miembros:

| Campo | Qué significa que difiera |
|---|---|
| `Playlist` (id) | 🔴 **Pantallas mostrando contenido distinto** |
| Timestamp de la playlist | 🟡 Misma playlist, versiones distintas: un update a medio propagar |
| `Playlist To Change` | 🟡 Cola de cambios pendientes. Una cola larga es un nodo que se quedó atrás |
| `estado` | 🟡 Un `READY` entre `PLAYING` está por entrar |
| `(MASTER)` | 🔴 Más de uno es split-brain |

**Ejemplo real del corpus:** todos los miembros en `Playlist: 67161` con el mismo timestamp (bien), pero dos tenían 4 archivos en `Playlist To Change` y el resto solo 1 (se quedaron atrás), **y había 3 masters** (split-brain).

---

## 7.4 Descubrimiento de miembros y elección de master

```regex
^\[Node\] \[Sync\] Joining multicast group$
^\[Node\] \[Sync\] New member discovered: (?<ip>\S+) \| State: (?<estado>\w+) \| Channel: (?<channel>\d+) \| Is Master: (?<master>true|false) \| MachineId: (?<machineId>\d+)$
^\[Node\] \[Sync\] Master (?<master>\w+) \| memberInfo (?<info>\w+) \| masterDetermined (?<determinado>\w+)$
^\[Node\] \[Sync\] Member (?<ip>\S+) is not active$
^\[Node\] \[Sync\] Next candidates check in (?<seg>\d+) seconds$
^\[Node\] \[Sync\] Fail over disabled$
```

**Lo que descubrimos de estos campos:**
- **`Channel`** existe y toma valores numéricos chicos (5, 7). Parece identificar sub-grupos de sincronización.
- **`MachineId`** es un id numérico de 5 dígitos (98309, 98311), distinto del nombre de `Machine:`.
- **`Is Master`** viene en el descubrimiento: así se entera cada nodo de quién manda.
- **`Member <IP> is not active`** (60 casos) es la señal **explícita** de nodo caído. No hace falta inferirlo por ausencia de eventos.

### Quién es el master, de verdad

```regex
^\[Node\] \[Sync\] Sending command PLAY burst to all members$
```

> **El master es el que manda las ráfagas.** Verificación contundente: de 14 archivos, solo 3 emiten esta línea, y el que más tiene (479 de 693) es literalmente `TimHortonsTransistmicaP4 MASTER.log`.

Tres formas de determinar el rol, por confiabilidad:

| Método | Confiabilidad |
|---|---|
| Emite `PLAY burst to all members` | ✅ **La más directa** |
| Su fila del bloque tiene `(MASTER)` | ✅ Confiable |
| `Master true \| …` en la línea de determinación | ⚠️ En el corpus **siempre dio `false`**: la emiten los nodos que no son master |

---

## 7.5 Propagación de un cambio de playlist en el grupo

```
[Node] [Sync] Playlist stopped
[Node] [Sync] PLAYLIST ID = 67161
[Node] [Sync] New Playlist received
[Node] [Sync] Checking playlist to play...
[Node] [Sync] Decision : 67161_2026-02-16T17.05.57.217
[Node] [Sync] Member <IP> is ready to change Playlist
[Player] Received playlist:change from node
```

| Patrón | Regex sobre `message` |
|---|---|
| Evaluando | `^\[Node\] \[Sync\] Checking playlist to play\.\.\.$` |
| Decisión | `^\[Node\] \[Sync\] Decision : (?<playlist>.+)$` |
| Miembro listo | `^\[Node\] \[Sync\] Member (?<ip>\S+) is ready to change Playlist$` |
| Propagación | `^\[Player\] Received playlist:change from node$` |
| Sin canales | `^\[Node\] \[Sync\] Channels empty$` |

**Cómo leerlo:** el flujo sano es que todos los miembros reporten `is ready to change Playlist` y después el bloque `SYNC GROUP INFO` los muestre a todos en la playlist nueva. Si un miembro nunca reporta, se quedó atrás y su cola de `Playlist To Change` va a crecer.

---

## 7.6 Errores propios del sync

| Patrón | Regex sobre `message` | Nivel | Lectura |
|---|---|---|---|
| Nodo caído | `^\[Node\] \[Sync\] Member (?<ip>\S+) is not active$` | INFO | Un miembro se cayó |
| Bug del player | `^\[Player\] \[Sync\] Error checking group content (?<causa>.+)$` | ERROR | Excepción de JS: `Cannot read property 'indexOf' of undefined`. Es un defecto del player, no de la red |
| Node local caído | `^\[Player\] Node server not Running$` | ERROR | Sin nodo local no hay sync |
| Failover apagado | `^\[Node\] \[Sync\] Fail over disabled$` | INFO | Si el master cae, **nadie lo reemplaza** |

---

## 7.7 Cómo diagnosticar el cluster

```
1. Buscá la línea "Members:" más reciente.
2. Contá los [Master]:
     1 → sano    |    0 o >1 → split-brain, y ahí está el problema
3. Buscá el último bloque SYNC GROUP INFO.
4. Compará entre filas: ¿misma Playlist? ¿mismo timestamp?
5. Mirá "Playlist To Change": una cola larga en un miembro = se quedó atrás.
6. Buscá "Member <IP> is not active" → miembros caídos.
7. ¿Este player manda "PLAY burst to all members"? → es el master.
8. ¿"Fail over disabled"? → si el master cae, el grupo queda sin coordinación.
```

**Limitación importante:** un solo archivo te da la visión de **ese nodo**. El split-brain sí se detecta con un archivo (contando `[Master]`), pero para confirmar qué está mostrando cada pantalla conviene tener los logs de todo el grupo. Los archivos `(1)` del mismo día son exactamente eso ([01 §1.6](01-LECTURA-BASE.md)).

---

## 7.8 Referencia rápida

| Patrón | Regex sobre `message` | Señal |
|---|---|---|
| **Grupo y masters** | `^\[Player\] \[Sync\] Version: (?<v>[\d.]+) - Group: (?<g>.+?) - Members: (?<m>.*)$` | **Máxima** |
| Delimitador de bloque | `^={54}$` | Estructura |
| Header | `^=+SYNC GROUP INFO=+$` | Estructura |
| **Fila de miembro** | ver §7.3 | **Máxima** |
| **Master real** | `^\[Node\] \[Sync\] Sending command PLAY burst to all members$` | **Máxima** |
| Miembro descubierto | `^\[Node\] \[Sync\] New member discovered: (?<ip>\S+) \| State: (?<st>\w+) \| Channel: (?<ch>\d+) \| Is Master: (?<ma>true\|false) \| MachineId: (?<mid>\d+)$` | Alta |
| **Nodo caído** | `^\[Node\] \[Sync\] Member (?<ip>\S+) is not active$` | **Alta** |
| Determinación de master | `^\[Node\] \[Sync\] Master (?<m>\w+) \| memberInfo (?<i>\w+) \| masterDetermined (?<d>\w+)$` | Media |
| Miembro listo | `^\[Node\] \[Sync\] Member (?<ip>\S+) is ready to change Playlist$` | Media |
| Decisión | `^\[Node\] \[Sync\] Decision : (?<pl>.+)$` | Media |
| Multicast | `^\[Node\] \[Sync\] Joining multicast group$` | Baja |
| Failover apagado | `^\[Node\] \[Sync\] Fail over disabled$` | Media |
| Sin canales | `^\[Node\] \[Sync\] Channels empty$` | Media |
| Próximo chequeo | `^\[Node\] \[Sync\] Next candidates check in (?<s>\d+) seconds$` | Baja |
| Error de grupo | `^\[Player\] \[Sync\] Error checking group content (?<c>.+)$` | Alta |
| Versión de Nodejs | `^\[Node\] \[Sync\] Nodejs v(?<v>[\d.]+)$` | Baja |

---

**Anterior:** [06 — Ruido](06-GENERAL-ruido.md) · **Siguiente:** [08 — Templates](08-TEMPLATES.md)
