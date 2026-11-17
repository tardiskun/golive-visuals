# Game of Life Isométrico - Audio-Reactivo y MIDI-Reactivo

## Descripción

Proyección de arte generativo que combina el algoritmo de Conway Game of Life con:
- Vista isométrica configurable (3 perspectivas)
- Campo de estrellas reactivas al audio
- Integración completa con Reaper vía MIDI

## Requisitos

### Software
- Processing 4.x con modo Python enabled
- Reaper Audio (para control MIDI)
- Kaos nanoKONTROL2 MIDI controller

### Hardware
- Computer con GPU suficiente para renderizado en tiempo real

## Configuración

### 1. Preparar Reaper con MIDI Control
En Reaper, configura:
```
MIDI → Input → nanoKONTROL2
MIDI → Output → [dispositivo o loopback]
```

### 2. Mapeo de Control MIDI
| Nota MIDI | Efecto Visual | Frecuencia |
|-----------|--------------|------------|
| C1-C4 (26-39) | Desprendimiento del fondo | Bajo |
| D4-G5 (48-67) | Movimiento suave | Medio |
| G5-B7+ (72+) | Glow y mutaciones rápidas | Alto |

### 3. Activar el Proyecto
```bash
# En la terminal de Processing:
python -m processing GameOfLife/gameoflife.py
```

## Teclas de Control

- **1**: Vista frontal (2D) - Rejilla plana
- **2**: Diagonal izquierda (-30°) - Perspectiva isométrica
- **3**: Top-down isométrico - Vista desde arriba

## Arquitectura del Sistema

```
Reaper MIDI → Kaos nanoKONTROL2 → Processing Python Mode
                ↓
        Audio Reactivo (pyo)    Estrellas Reactivas    Game of Life Mutado
```

## Parámetros Clave

- `MUTATION_INTERVAL`: Tiempo mínimo entre mutaciones (0.5s)
- `MIN_LIFE_TIME`: Duración mínima de la proyección (30s)
- `NUM_STARS`: Número de estrellas reactivas al audio (300)
- `COLS/ROWS`: Dimensiones de la rejilla (50x50)

## Integración con Reaper

Para sincronizar todo el sistema:
1. En Reaper, carga tu track de fondo
2. Configura MIDI Out → nanoKONTROL2
3. Abre el archivo GameOfLife.py en Processing Python mode
4. Inicia la proyección y reproduce Reaper simultáneamente

Los cambios en el volumen de canales de Reaper se traducirán automáticamente en efectos visuales en la rejilla y las estrellas.

## Extensión del Proyecto

Para añadir más funcionalidades:
- Modificar `MUTATION_INTERVAL` para más/lento mutaciones
- Ajustar `NUM_STARS` según el rendimiento
- Añadir nuevos estados de mutación en la clase `Individual`
- Implementar efectos 3D adicionales con P3D

## Notas Técnicas

- El sistema usa pyo para procesamiento MIDI y audio
- Los mensajes MIDI son procesados en tiempo real por pyo
- La sincronización es automática: el mismo evento MIDI afecta tanto audio como visual
- La mutación no es aleatoria completamente; responde a los patrones de MIDI
