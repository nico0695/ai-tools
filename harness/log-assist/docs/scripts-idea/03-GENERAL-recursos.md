# 03 — Recursos: CPU y RAM

> Sección **General**. Dominio `TEL`.
> Responde: ¿está escalando la RAM? ¿hay fuga de memoria? ¿la CPU está saturada?

---

## 3.1 La única línea de telemetría

```regex
^\[System Manager\] CPU: (?<cpu>[\d.]+)%\. Used RAM: (?<ram>[\d.]+) Mb$
```

```
2026-02-22 11:16:32 INFO [System Manager] CPU: 14.50%. Used RAM: 1217.40 Mb
```

Es la **única** fuente de CPU y RAM. No hay otra métrica de recursos en el log.

---

## 3.2 La cadencia depende de la plataforma

| Plataforma | Intervalo de reporte | Muestras en 8 h |
|---|---:|---:|
| **webOS** | **300 s** (5 min) | ~96 |
| **Tizen** | **60 s** (1 min) | ~480 |

> Esto sirve para dos cosas. Primero, **detectar la plataforma** sin leer el banner. Segundo, y más importante: **detectar huecos**. Si en webOS pasan 20 minutos sin una línea de CPU, faltan 3 muestras y ahí pasó algo (reinicio, congelamiento o pantalla apagada).

---

## 3.3 La línea base es distinta en cada plataforma

Esto es crítico: **un umbral único de RAM da falsos positivos garantizados.**

| Plataforma | RAM observada | Nota |
|---|---|---|
| **webOS** | **1.064 – 1.288 Mb** | Rango estrecho y estable |
| **Tizen** | **648 – 885 Mb** | ~400 Mb menos que webOS |

Una pantalla webOS a 1.200 Mb está perfectamente sana. Una Tizen a 1.200 Mb estaría muy fuera de rango.

**Cómo trabajarlo sin un umbral absoluto:** calculá el rango de la propia pantalla y buscá desvíos contra su propia historia, no contra un número fijo.

---

## 3.4 Detectar escalado de RAM (fuga de memoria)

**Qué medir:** la pendiente de la RAM dentro de una misma sesión, en Mb por hora.

```
pendiente = (RAM_última − RAM_primera) / horas_de_la_sesión
```

**Cómo interpretarla, con la referencia del corpus analizado:**

| Pendiente observada | Archivos | Lectura |
|---|---:|---|
| −21 a +6,4 Mb/h | 12 de 14 | **Comportamiento normal.** La RAM oscila y cambia de signo |
| Picos aislados | — | Normal: el arranque de un template levanta RAM y después la libera |

> **En todo el corpus no hubo ninguna fuga de memoria.** La RAM sube y baja sin tendencia sostenida. Esto es importante como línea base: si ves una pendiente **positiva y sostenida a lo largo de horas**, es anómalo respecto de lo que hace un player normal.

**Señal de fuga real** (las tres condiciones juntas):
1. Pendiente positiva sostenida durante más de una hora.
2. Sin que baje nunca (una fuga no libera).
3. Acercándose al techo histórico de esa pantalla.

**Y el cierre del caso:** si después de eso aparece un arranque sin countdown previo, tenés la historia completa. Es el flujo **F-RAM** de [11 — Catálogo](11-CATALOGO.md).

---

## 3.5 CPU: cuándo preocuparse y cuándo no

| Situación | Lectura |
|---|---|
| **CPU 98 % en los primeros 30 s tras el arranque** | **Normal.** Es el pico de inicialización. Verificado en Tizen a +9,3 s del boot |
| CPU alta durante la carga de un template | Normal, es transitorio |
| CPU alta sostenida fuera de esas ventanas | **Investigar** |

**Regla práctica:** descartá siempre los primeros 30 segundos después de cada banner de arranque antes de calcular estadísticas de CPU. Si no, cada reinicio te mete un 98 % que no significa nada.

---

## 3.6 Cómo leer la telemetría en la práctica

```
1. Separá las muestras por sesión (cada banner abre una).
2. Descartá los primeros 30 s de cada sesión.
3. Por sesión, calculá de la RAM: mínimo, máximo, primera, última y pendiente.
4. Compará contra el rango histórico de ESA pantalla, no contra un absoluto.
5. Buscá huecos: en webOS, más de 300 s sin muestra; en Tizen, más de 60 s.
```

**Correlación que vale la pena:** poné en la misma línea de tiempo las muestras de RAM y los banners de arranque. Una pendiente que sube y termina en un banner es la firma de un reinicio por memoria.

---

## 3.7 Referencia rápida

| Patrón | Regex sobre `message` | Uso |
|---|---|---|
| CPU y RAM | `^\[System Manager\] CPU: (?<cpu>[\d.]+)%\. Used RAM: (?<ram>[\d.]+) Mb$` | Única fuente de recursos |

| Parámetro | Valor | Origen |
|---|---|---|
| Cadencia webOS | 300 s | **Medido** |
| Cadencia Tizen | 60 s | **Medido** |
| Rango webOS | 1.064 – 1.288 Mb | **Medido** |
| Rango Tizen | 648 – 885 Mb | **Medido** |
| Ventana a descartar tras el arranque | 30 s | **Recomendado** |
| Umbral absoluto de RAM | *sin definir* | Requiere criterio del producto |
| Umbral absoluto de CPU | *sin definir* | Requiere criterio del producto |
| Pendiente que marca fuga | *sin definir* | Referencia medida: lo normal va de −21 a +6,4 Mb/h |

---

**Anterior:** [02 — Sesiones y reinicios](02-GENERAL-sesiones-reinicios.md) · **Siguiente:** [04 — Contenido y playlists](04-GENERAL-contenido-playlists.md)
