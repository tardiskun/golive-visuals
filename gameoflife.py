"""
Game of Life Isométrico con Mutaciones y Audio-Reactivo
===========================================================
Proyecto para LM Studio Bionic + Processing Python mode

Funcionalidades:
- Isometría configurable (teclas 1, 2, 3)
- Game of Life con mutaciones (no muerte)
- Campo de estrellas vibrantes al audio
- MIDI bridge para Reaper + Kaos nanoKONTROL2
- Efectos glow según tonalidad MIDI

Configuración:
- Ventana: 1920x1080, FPS: 60
- Rejilla: 50x50 células (ajustable)
- Estrellas: ~300 partículas
"""

from pyo import *
import time
import math
import random

# ============================================================
# CONFIGURACIÓN GLOBAL
# ============================================================

# Ventana y ventana de trabajo
width = 1920
height = 1080
fps = 60

# Rejilla Game of Life
COLS = 50
ROWS = 50
CELL_SIZE = min(width, height) / max(COLS, ROWS) * 0.75
CELL_INTERVAL = CELL_SIZE / 2

# Estados del juego (los números son colores)
STATE_EMPTY = 0    # Color: negro/transparente
STATE_ALIVE = 1   # Color: verde claro
STATE_MUTANT_A = 2 # Color: azul
STATE_MUTANT_B = 3 # Color: rojo
STATE_GLOW = 4    # Estado de glow (efecto visual)

# Tiempo de mutación mínimo en segundos
MUTATION_INTERVAL = 0.5
MIN_LIFE_TIME = 30.0  # Mínimo 30 segundos por individuo

# Parámetros de la rejilla
GRID_W = COLS * CELL_SIZE
GRID_H = ROWS * CELL_SIZE
GRID_OFFSET_X = (width - GRID_W) / 2
GRID_OFFSET_Y = (height - GRID_H) / 2

# Estrellas
NUM_STARS = 300
STAR_SPEED_BASE = 0.5
STAR_SPEED_MAX = 2.0
STAR_SPEED_MIN = 0.1

# Audio reactivo
AUDIO_REACTIVE = True
MIDI_RECEPTOR = True  # Activar si hay Reaper conectado vía MIDI

# ============================================================
# CLASE INDIVIDUAL (Célula del Game of Life)
# ============================================================

class Individual:
    """Representa un individuo en el juego de la vida con mutaciones"""
    
    def __init__(self, col, row):
        self.col = col
        self.row = row
        self.state = STATE_ALIVE  # Inicialmente vivo
        self.birth_time = time.time()
        self.last_mutation = time.time()
        self.glow_intensity = 0.0  # Para efecto glow
        self.mutation_count = 0
    
    def get_pos(self, camera_mode=1):
        """Calcular posición isométrica basada en modo de cámara"""
        if camera_mode == 1:  # Frontal (2D)
            return (self.col * CELL_SIZE, self.row * CELL_SIZE)
        elif camera_mode == 2:  # Diagonal izquierda
            angle = math.radians(-30)
            x = (self.col - self.row) * CELL_SIZE * 0.5 + GRID_OFFSET_X
            y = (self.col + self.row) * CELL_SIZE * 0.5 + GRID_OFFSET_Y
            return (x, y)
        else:  # Camera_mode == 3 (top-down/isometric)
            angle = math.radians(45)
            x = (self.col - self.row) * CELL_SIZE * 0.7 + GRID_OFFSET_X
            y = (self.col + self.row) * CELL_SIZE * 0.15 + GRID_OFFSET_Y
            return (x, y)
    
    def get_color(self):
        """Obtener color según estado actual"""
        if self.state == STATE_EMPTY:
            return (0, 0, 0)
        elif self.state == STATE_ALIVE:
            return (128, 255, 128)  # Verde claro
        elif self.state == STATE_MUTANT_A:
            return (64, 128, 255)    # Azul
        elif self.state == STATE_MUTANT_B:
            return (255, 64, 64)     # Rojo
        else:  # State_GLOW
            r = int(100 * (self.glow_intensity + 1.0))
            g = int(150 * (self.glow_intensity + 1.0))
            b = int(200 * (self.glow_intensity + 1.0))
            return (r, g, b)
    
    def mutate(self):
        """Mutar el individuo a otro estado"""
        current_time = time.time()
        
        if current_time - self.last_mutation < MUTATION_INTERVAL:
            return
        
        # Elegir nuevo estado diferente al actual
        possible_states = [s for s in range(1, 5) if s != self.state]
        new_state = random.choice(possible_states)
        
        self.state = new_state
        self.last_mutation = current_time
        self.glow_intensity = 0.5
        
        # Si es estado glow, decrementarlo gradualmente en el loop principal
        if new_state == STATE_GLOW:
            self.last_mutation = time.time() + 0.3  # Dura 0.3 segundos
    
    def update(self, audio_input):
        """Actualizar estado del individuo basado en audio"""
        current_time = time.time()
        
        # Decaimiento del glow
        if self.state == STATE_GLOW:
            self.glow_intensity -= 0.1
        
        # Efecto de desprendimiento según tono MIDI
        if AUDIO_REACTIVE and hasattr(self, 'audio_moving'):
            moving = audio_input.get('bass', 0) * 0.5 + audio_input.get('mid', 0) * 0.3
            if random.random() < moving:
                # Mover el individuo (cambiar estado temporalmente)
                self.state = STATE_GLOW
        
        # Cambio de color según agudo MIDI
        if AUDIO_REACTIVE and hasattr(self, 'audio_glow'):
            high_freq = audio_input.get('high', 0)
            if high_freq > 0.5:
                if self.state != STATE_GLOW:
                    self.mutate()

# ============================================================
# CLASE REJILLA (Game of Life Grid)
# ============================================================

class GameOfLifeGrid:
    """Implementa el algoritmo de Conway con mutaciones"""
    
    def __init__(self, cols=COLS, rows=ROWS):
        self.cols = cols
        self.rows = rows
        self.grid = []  # Grid de Individuals
        self.individuals = []
        self.next_grid = []
        
        # Inicializar la rejilla
        for i in range(rows):
            row = []
            for j in range(cols):
                individual = Individual(j, i)
                row.append(individual)
                self.individuals.append(individual)
            self.grid.append(row)
    
    def get_neighbors(self, col, row):
        """Contar vecinos en el grid"""
        count = 0
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr = (row + dr) % self.rows
                nc = (col + dc) % self.cols
                neighbor = self.grid[nr][nc]
                if neighbor.state != STATE_EMPTY:
                    count += 1
        return count
    
    def update_step(self, audio_input=None):
        """Ejecutar un paso del juego de la vida"""
        current_time = time.time()
        
        # Crear nuevo grid para evitar conflictos
        for i in range(self.rows):
            self.next_grid[i] = []
            for j in range(self.cols):
                individual = Individual(j, i)
                self.next_grid[i][j] = individual
        
        for i in range(self.rows):
            for j in range(self.cols):
                individual = self.grid[i][j]
                
                # Actualizar estado con audio reactivo
                if audio_input:
                    individual.update(audio_input)
                
                neighbors = self.get_neighbors(j, i)
                
                # Lógica del juego de la vida (modificada para mutaciones)
                if individual.state == STATE_EMPTY:
                    # Regenerar individuals aleatorios
                    if random.random() < 0.02 or neighbors == 3:
                        new_state = random.choice([STATE_ALIVE, STATE_MUTANT_A, STATE_MUTANT_B])
                        self.next_grid[i][j].state = new_state
                        self.next_grid[i][j].birth_time = current_time
                else:
                    # Individual vivo: aplicar reglas modificadas
                    if neighbors == 2 or neighbors == 3:
                        # Sobrevive
                        self.next_grid[i][j].state = individual.state
                        self.next_grid[i][j].birth_time = individual.birth_time
                        self.next_grid[i][j].mutation_count += individual.mutation_count
                    else:
                        # Mutación en lugar de muerte (no se vuelve EMPTY)
                        new_state = random.choice([STATE_ALIVE, STATE_MUTANT_A, STATE_MUTANT_B])
                        self.next_grid[i][j].state = new_state
                        self.next_grid[i][j].birth_time = current_time
    
    def get_individuals(self):
        """Devolver todos los individuos vivos"""
        result = []
        for i in range(self.rows):
            for j in range(self.cols):
                individual = self.grid[i][j]
                if individual.state != STATE_EMPTY:
                    result.append(individual)
        return result

# ============================================================
# CLASE CAMPO DE ESTRELLAS REACTIVO AL AUDIO
# ============================================================

class StarFieldAudioReactive:
    """Campo de estrellas que vibra y se transforma según el audio MIDI"""
    
    def __init__(self, num_stars=NUM_STARS):
        self.stars = []
        
        for i in range(num_stars):
            self.stars.append({
                'x': random.uniform(0, width),
                'y': random.uniform(0, height),
                'size': random.uniform(1, 3),
                'speed': random.uniform(STAR_SPEED_MIN, STAR_SPEED_BASE),
                'brightness': random.uniform(0.3, 1.0),
                'phase': random.uniform(0, 2 * math.pi),
                'original_x': random.uniform(0, width),
                'original_y': random.uniform(0, height),
                'depth': random.uniform(0.5, 1.0)  # Para efecto isométrico
            })
    
    def update(self, audio_input=None):
        """Actualizar posición y parámetros de las estrellas"""
        current_time = time.time()
        
        for star in self.stars:
            # Movimiento base
            if random.random() < 0.3:  # No mover todas las veces para rendimiento
                star['x'] += (star['speed'] * random.uniform(-1, 1)) / 60.0
                star['y'] += (star['speed'] * random.uniform(-1, 1)) / 60.0
                
                # Wrapping en bordes del canvas
                if star['x'] < 0:
                    star['x'] = width
                elif star['x'] > width:
                    star['x'] = 0
                if star['y'] < 0:
                    star['y'] = height
                elif star['y'] > height:
                    star['y'] = 0
            
            # Efecto de vibración según audio MIDI
            if AUDIO_REACTIVE and audio_input:
                bass = audio_input.get('bass', 0)
                mid = audio_input.get('mid', 0)
                high = audio_input.get('high', 0)
                
                # Vibración según frecuencias
                star['brightness'] = (star['brightness'] + 
                                     bass * 0.5 + mid * 0.3 + high * 0.2) % 1.2
                
                # Efecto de desprendimiento en base a graves
                if bass > 0.7:
                    star['x'] += random.uniform(-2, 2)
                    star['y'] += random.uniform(-2, 2)
    
    def draw(self):
        """Dibujar el campo de estrellas"""
        for star in self.stars:
            x = star['x']
            y = star['y']
            size = star['size'] * star['brightness']
            
            # Color según profundidad (efecto isométrico)
            r = int(200 * star['depth'])
            g = int(210 * star['depth'])
            b = min(int(255 * star['depth']), 255)
            
            fill(r, g, b)
            ellipse(x, y, size, size)

# ============================================================
# CLASE REJILLA VISUAL (Isometría)
# ============================================================

class IsometricGrid:
    """Dibuja la rejilla isométrica con el juego de vida"""
    
    def __init__(self):
        self.grid = GameOfLifeGrid()
        
    def draw_grid(self, camera_mode=1):
        """Dibujar la rejilla isométrica con los individuos vivos"""
        # Dibujar líneas de la rejilla (opcional, para visualización)
        stroke(50, 50, 50)
        strokeWeight(1)
        
        for i in range(self.grid.rows + 1):
            if camera_mode == 1:  # Frontal
                line(GRID_OFFSET_X, GRID_OFFSET_Y + i * CELL_SIZE,
                    GRID_OFFSET_X + GRID_W, GRID_OFFSET_Y + i * CELL_SIZE)
            
            elif camera_mode == 2:  # Diagonal izquierda
                x1 = GRID_OFFSET_X + (self.grid.cols - i) * CELL_SIZE * 0.5
                y1 = GRID_OFFSET_Y + (self.grid.rows - i) * CELL_SIZE * 0.5
                line(x1, y1, width, height)
        
        # Dibujar individuos vivos
        for individual in self.grid.get_individuals():
            if individual.state != STATE_EMPTY:
                x, y = individual.get_pos(camera_mode)
                
                # Ajustar posición para que esté dentro del viewport
                if 0 <= x <= width and 0 <= y <= height:
                    color = individual.get_color()
                    
                    fill(color[0], color[1], color[2])
                    stroke(255, 255, 255)
                    strokeWeight(2)
                    
                    # Dibujar el individuo como un círculo o rectángulo isométrico
                    if camera_mode == 3:  # Top-down / Isometric
                        ellipse(x, y, CELL_SIZE * 0.6, CELL_SIZE * 0.4)
                    elif camera_mode == 2:  # Diagonal izquierda
                        ellipse(x, y, CELL_SIZE * 0.5, CELL_SIZE * 0.3)
                    else:  # Frontal (2D)
                        rect(x - CELL_SIZE * 0.2, y - CELL_SIZE * 0.2, 
                           CELL_SIZE * 0.4, CELL_SIZE * 0.4)

# ============================================================
# CLASE AUDIO/MIDI REACTIVE
# ============================================================

class AudioMidiReactive:
    """Maneja audio MIDI de Reaper via pyo"""
    
    def __init__(self):
        self.audio_input = {
            'bass': 0.0,
            'mid': 0.0,
            'high': 0.0,
            'volume': 0.0,
            'tracks_active': 0
        }
        
        # Estado de reproducción
        self.is_playing = False
        
        # MIDI listener para Reaper
        self.midi_listeners = {}
    
    def process_midi_message(self, msg_type, msg_data):
        """Procesar mensajes MIDI desde Reaper"""
        if msg_type == 'note_on':
            note = msg_data[0]
            velocity = msg_data[1]
            
            # Mapeo de notas a frecuencias (bajo=26-47, medio=48-79, alto=80+)
            if 26 <= note <= 47:
                self.audio_input['bass'] += velocity / 127.0 * 0.5
            elif 48 <= note <= 79:
                self.audio_input['mid'] += velocity / 127.0 * 0.3
            elif note >= 80:
                self.audio_input['high'] += velocity / 127.0 * 0.2
            
        elif msg_type == 'note_off':
            note = msg_data[0]
            
            if 26 <= note <= 47:
                self.audio_input['bass'] -= velocity / 127.0 * 0.5
            elif 48 <= note <= 79:
                self.audio_input['mid'] -= velocity / 127.0 * 0.3
            elif note >= 80:
                self.audio_input['high'] -= velocity / 127.0 * 0.2
        
        # Normalizar valores
        for key in ['bass', 'mid', 'high']:
            if self.audio_input[key] < 0:
                self.audio_input[key] = 0
    
    def update_audio(self):
        """Actualizar nivel de audio con decay"""
        for key in ['bass', 'mid', 'high']:
            self.audio_input[key] *= 0.95  # Decay suave
    
    def is_reaper_connected(self):
        """Verificar si Reaper está conectado vía MIDI"""
        return len(self.midi_listeners) > 0

# ============================================================
# CLASE MANAGER DE CAMERA ISOMETRICA
# ============================================================

class CameraManager:
    """Gestiona las vistas isométricas con teclas 1, 2, 3"""
    
    def __init__(self):
        self.current_mode = 1  # 1=Frontal (2D), 2=Diagonal izquierda, 3=Top-down
    
    def switch_to_camera(self, mode):
        """Cambiar a la vista isométrica correspondiente"""
        self.current_mode = mode
        
        # Mostrar mensaje visual de cambio
        if mode == 1:
            print("Camera Mode 1: Frontal (2D)")
        elif mode == 2:
            print("Camera Mode 2: Diagonal izquierda (-30°)")
        elif mode == 3:
            print("Camera Mode 3: Top-down isométrico")

# ============================================================
# CLASE PRINCIPAL DE PROYECCIÓN
# ============================================================

class GameOfLifeProjection:
    """Proyección completa del juego de la vida"""
    
    def __init__(self):
        self.grid = IsometricGrid()
        self.star_field = StarFieldAudioReactive(NUM_STARS)
        self.audio_midi = AudioMidiReactive()
        self.camera_manager = CameraManager()
        
        # Estado de reproducción
        self.start_time = time.time()
        self.duration = 8 * 60  # 8 minutos
    
    def draw_background(self):
        """Dibujar el fondo del espacio"""
        fill(10, 15, 30)  # Negro profundo (espacio)
    
    def draw_space_stars(self):
        """Dibujar estrellas del espacio en el fondo"""
        for i in range(200):
            x = random.uniform(0, width)
            y = random.uniform(0, height)
            
            # Variación suave de brillo (efecto de estrellas)
            brightness = 0.5 + random.random() * 0.5
            
            fill(int(brightness * 200), int(brightness * 210), int(brightness * 230))
            ellipse(x, y, random.uniform(0.5, 1.5), random.uniform(0.5, 1.5))
    
    def update(self):
        """Actualizar todo el sistema"""
        current_time = time.time()
        
        # Actualizar el grid de Game of Life (un paso por segundo)
        if int(current_time % 1) == 0:
            self.grid.grid.update_step(
                audio_input=self.audio_midi.audio_input.copy()
            )
        
        # Actualizar estrellas reactivas al audio
        self.star_field.update(self.audio_midi.audio_input)
        
        # Procesar MIDI si está activo
        if self.audio_midi.is_reaper_connected():
            self.audio_midi.update_audio()

    def draw(self):
        """Dibujar todo el sistema"""
        # Fondo espacial
        self.draw_background()
        
        # Estrellas del espacio (fondo)
        self.draw_space_stars()
        
        # Campo de estrellas reactivas al audio (sobre la rejilla)
        self.star_field.draw()
        
        # Rejilla isométrica con individuos
        self.grid.draw_grid(self.camera_manager.current_mode)

# ============================================================
# SETUP y MAIN LOOP
# ============================================================

def setup():
    """Inicialización del proyecto"""
    size(width, height)
    
    # Crear el sistema principal
    global game_of_life
    
    game_of_life = GameOfLifeProjection()
    
    # Registrar teclas para cambio de cámara
    register_key('1', lambda: game_of_life.camera_manager.switch_to_camera(1))
    register_key('2', lambda: game_of_life.camera_manager.switch_to_camera(2))
    register_key('3', lambda: game_of_life.camera_manager.switch_to_camera(3))

def draw():
    """Bucle principal de la proyección"""
    # Actualizar y dibujar
    game_of_life.update()
    game_of_life.draw()
    
    # Verificar si debemos terminar (duración)
    current_time = time.time()
    if current_time - game_of_life.start_time >= game_of_life.duration:
        print("\nProyección finalizada. Duración:", 
              int((current_time - game_of_life.start_time) / 60), "minutos")

# ===========================================================
# INTEGRACIÓN MIDI CON REAPER (Vía pyo)
# ===========================================================

def setup_midi_bridge():
    """Configurar bridge MIDI con Reaper"""
    
    # Crear listener de MIDI en pyo
    midi_in = InputMIDI()
    
    # Procesar mensajes MIDI
    def process_midi(msg):
        msg_type, msg_data = msg
        game_of_life.audio_midi.process_midi_message(msg_type, msg_data)
    
    # Registrar callback
    midi_in.add_callback(process_midi)

def run():
    """Iniciar la proyección"""
    print("=" * 50)
    print("Game of Life Isométrico con Audio-Reactivo")
    print("=" * 50)
    print("\nTeclas:")
    print("  1 - Vista frontal (2D)")
    print("  2 - Vista diagonal izquierda (-30°)")
    print("  3 - Vista top-down isométrico")
    print()
    print(f"Rejilla: {COLS}x{ROWS}")
    print(f"Estrellas reactivas: {NUM_STARS}")
    print(f"Duración mínima: {MIN_LIFE_TIME} segundos")
    print("=" * 50)
    
    # Setup MIDI bridge con Reaper
    setup_midi_bridge()
    
    # Iniciar el loop
    draw()

# ============================================================
# ENTRADA PRINCIPAL
# ============================================================

if __name__ == "__main__":
    run()
