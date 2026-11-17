"""
Configuración avanzada de MIDI/Reaper para Game of Life Isométrico
=============================================================
Este archivo configura la integración MIDI entre Reaper, Kaos nanoKONTROL2 y el sistema visual.

Para uso directo en Processing Python mode:
1. Importa los módulos necesarios desde este archivo
2. Configura los mapeos de notes para tus necesidades
3. Ajusta los umbrales de reactividad

Nota: Este archivo asume que Reaper está configurado con MIDI Out conectado a nanoKONTROL2.
"""

from pyo import *

class ReaperMidiBridge:
    """Puente MIDI para Reaper + nanoKONTROL2"""
    
    def __init__(self):
        # Configurar listener de MIDI
        self.midi_in = InputMIDI()
        
        # Umbrales de activación (ajusta según tu preferencia)
        self.bass_threshold = 0.7
        self.mid_threshold = 0.5
        self.high_threshold = 0.6
        
        # Estado actual
        self.current_bass = 0.0
        self.current_mid = 0.0
        self.current_high = 0.0
        
        # Callback para procesamiento MIDI
        self.callbacks = []
        
    def add_callback(self, callback):
        """Registrar un callback para recibir datos MIDI"""
        self.callbacks.append(callback)
    
    def process_note_on(self, note, velocity):
        """Procesar nota MIDI entrante"""
        if note >= 26 and note <= 47:  # Bajo (C1-C4)
            self.current_bass = max(0, min(1.0, self.current_bass + (velocity/127.0)*0.5))
            
        elif note >= 48 and note <= 79:  # Medio (D4-G5)
            self.current_mid = max(0, min(1.0, self.current_mid + (velocity/127.0)*0.3))
            
        elif note >= 80:  # Alto (G5-B7+)
            self.current_high = max(0, min(1.0, self.current_high + (velocity/127.0)*0.2))
    
    def process_note_off(self, note):
        """Procesar nota MIDI saliente"""
        if note >= 26 and note <= 47:
            self.current_bass = max(0, self.current_bass - (self.current_bass * 0.95))
            
        elif note >= 48 and note <= 79:
            self.current_mid = max(0, self.current_mid - (self.current_mid * 0.95))
            
        elif note >= 80:
            self.current_high = max(0, self.current_high - (self.current_high * 0.95))
    
    def get_state(self):
        """Obtener estado actual de los canales MIDI"""
        return {
            'bass': self.current_bass,
            'mid': self.current_mid,
            'high': self.current_high,
            'volume': (self.current_bass + self.current_mid + self.current_high) / 3.0
        }

# Instancia global para uso en el archivo principal
midi_bridge = ReaperMidiBridge()

def register_midi_callback(callback):
    """Registrar un callback global para MIDI"""
    midi_bridge.add_callback(callback)

# Ejemplo de uso:
# def on_midi(state):
#     print(f"Bajo: {state['bass']:.2f}, Medio: {state['mid']:.2f}, Alto: {state['high']:.2f}")
# 
# register_midi_callback(on_midi)
