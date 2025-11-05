"""
src/output_layer/alert_module.py

Audio alert system for fatigue detection
"""

import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame
import threading
import os
import time
from typing import Optional
from enum import Enum

class AlertSound(Enum):
    """Alert sound types"""
    LOW = "alert_low.wav"
    MEDIUM = "alert_medium.wav"
    HIGH = "alert_high.wav"
    CRITICAL = "alert_critical.wav"

class AudioAlertManager:
    """Manages audio alerts for fatigue detection"""
    
    def __init__(self, sounds_dir: str = "assets/sounds"):
        self.sounds_dir = sounds_dir
        self.is_initialized = False
        self.sounds = {}
        self.last_alert_time = {}
        self.alert_cooldown = 1.0  # Shorter cooldown for more frequent alerts
        
        self._initialize_pygame()
        self._load_sounds()
        
    def _initialize_pygame(self):
        """Initialize pygame mixer"""
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            pygame.mixer.set_num_channels(8)  # More channels for multiple sounds
            self.is_initialized = True
            pass  # Audio system initialized successfully
        except Exception as e:
            pass  # Failed to initialize audio
            self.is_initialized = False
            
    def _load_sounds(self):
        """Load alert sound files"""
        if not self.is_initialized:
            return
            
        # Create default sounds if they don't exist
        self._create_default_sounds()
        
        # Load all sound files
        for alert_type in AlertSound:
            sound_path = os.path.join(self.sounds_dir, alert_type.value)
            if os.path.exists(sound_path):
                try:
                    self.sounds[alert_type] = pygame.mixer.Sound(sound_path)
                    self.sounds[alert_type].set_volume(1.0)  # Maximum volume
                    pass  # Loaded sound successfully
                except Exception as e:
                    pass  # Failed to load sound
            else:
                pass  # Sound file not found
                
    def _create_default_sounds(self):
        """Create default alert sounds using pygame"""
        if not self.is_initialized:
            return
            
        os.makedirs(self.sounds_dir, exist_ok=True)
        
        # Generate different frequency alarm patterns for each alert level
        sound_configs = {
            AlertSound.LOW: (800, 0.5, 2, "pulse"),       # Mid tone, 0.5s, 2 pulses
            AlertSound.MEDIUM: (1000, 0.8, 3, "rising"),  # Rising tone, 0.8s, 3 cycles
            AlertSound.HIGH: (1200, 1.2, 4, "siren"),     # Siren pattern, 1.2s, 4 cycles
            AlertSound.CRITICAL: (1500, 2.0, 6, "alarm")  # Emergency alarm, 2.0s, 6 cycles
        }
        
        for alert_type, (freq, duration, cycles, pattern) in sound_configs.items():
            sound_path = os.path.join(self.sounds_dir, alert_type.value)
            if not os.path.exists(sound_path):
                try:
                    self._generate_alarm_sound(sound_path, freq, duration, cycles, pattern)
                    pass  # Generated alarm sound successfully
                except Exception as e:
                    pass  # Failed to generate alarm sound
                    
    def _generate_alarm_sound(self, filepath: str, base_frequency: int, duration: float, cycles: int, pattern: str):
        """Generate powerful alarm sound with different patterns"""
        import numpy as np
        import wave
        
        sample_rate = 44100  # Higher quality
        total_frames = int(sample_rate * duration)
        
        # Generate time array
        t = np.linspace(0, duration, total_frames, False)
        
        # Create different alarm patterns
        if pattern == "pulse":
            # Rapid pulse pattern
            audio_data = np.zeros(total_frames)
            pulse_length = int(sample_rate * 0.1)  # 0.1s pulses
            gap_length = int(sample_rate * 0.05)   # 0.05s gaps
            
            pos = 0
            while pos < total_frames:
                end_pos = min(pos + pulse_length, total_frames)
                pulse_t = np.linspace(0, 0.1, end_pos - pos, False)
                audio_data[pos:end_pos] = np.sin(2 * np.pi * base_frequency * pulse_t) * 0.8
                pos += pulse_length + gap_length
                
        elif pattern == "rising":
            # Rising frequency siren
            freq_end = base_frequency * 1.5
            freq_sweep = np.linspace(base_frequency, freq_end, total_frames)
            audio_data = np.sin(2 * np.pi * freq_sweep * t) * 0.8
            
        elif pattern == "siren":
            # Classic two-tone siren
            freq_low = base_frequency * 0.8
            freq_high = base_frequency * 1.2
            switch_rate = 4  # Hz - how fast it switches
            freq_pattern = np.where(np.sin(2 * np.pi * switch_rate * t) > 0, freq_high, freq_low)
            audio_data = np.sin(2 * np.pi * freq_pattern * t) * 0.9
            
        elif pattern == "alarm":
            # Emergency alarm - multiple tones
            tone1 = np.sin(2 * np.pi * base_frequency * t) * 0.4
            tone2 = np.sin(2 * np.pi * (base_frequency * 1.25) * t) * 0.4
            tone3 = np.sin(2 * np.pi * (base_frequency * 1.5) * t) * 0.3
            
            # Add amplitude modulation for intensity
            modulation = 1 + 0.5 * np.sin(2 * np.pi * 8 * t)  # 8 Hz modulation
            audio_data = (tone1 + tone2 + tone3) * modulation * 0.9
            
        else:
            # Default - simple sine wave
            audio_data = np.sin(2 * np.pi * base_frequency * t) * 0.8
        
        # Add fade in/out to prevent clicks
        fade_samples = int(sample_rate * 0.01)  # 10ms fade
        fade_in = np.linspace(0, 1, fade_samples)
        fade_out = np.linspace(1, 0, fade_samples)
        
        audio_data[:fade_samples] *= fade_in
        audio_data[-fade_samples:] *= fade_out
        
        # Convert to 16-bit integers with higher volume
        audio_data = np.clip(audio_data, -1, 1)  # Prevent clipping
        audio_data = (audio_data * 32767 * 0.95).astype(np.int16)  # 95% max volume
        
        # Save as WAV file
        with wave.open(filepath, 'w') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 2 bytes per sample
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
            
    def play_alert(self, alert_level: str, force: bool = False):
        """Play alert sound only for HIGH and CRITICAL levels"""
        if not self.is_initialized:
            return
            
        # Only play audio for HIGH and CRITICAL alerts
        if alert_level.upper() not in ['HIGH', 'CRITICAL']:
            return  # Skip audio for LOW and MEDIUM alerts
            
        # Map alert levels to sound types
        level_map = {
            "HIGH": AlertSound.HIGH,
            "CRITICAL": AlertSound.CRITICAL
        }
        
        sound_type = level_map.get(alert_level.upper())
        if not sound_type or sound_type not in self.sounds:
            return
            
        # Check cooldown
        current_time = time.time()
        if not force and sound_type in self.last_alert_time:
            if current_time - self.last_alert_time[sound_type] < self.alert_cooldown:
                return
                
        # Play sound in separate thread to avoid blocking
        def play_sound():
            try:
                if alert_level.upper() == 'CRITICAL':
                    # Play 3 beeps for CRITICAL alert
                    for i in range(3):
                        self.sounds[sound_type].play()
                        if i < 2:  # Don't sleep after last beep
                            time.sleep(0.3)  # Short pause between beeps
                else:
                    # Play 1 beep for HIGH alert
                    self.sounds[sound_type].play()
                    
                self.last_alert_time[sound_type] = current_time
            except Exception as e:
                pass  # Error playing sound
                
        threading.Thread(target=play_sound, daemon=True).start()
        
    def test_sounds(self):
        """Test all alert sounds"""
        print("🔊 Testing alert sounds...")
        for alert_type in AlertSound:
            if alert_type in self.sounds:
                print(f"Playing {alert_type.name}...")
                self.sounds[alert_type].play()
                time.sleep(1.5)
                
    def set_volume(self, volume: float):
        """Set volume for all sounds (0.0 to 1.0)"""
        if not self.is_initialized:
            return
            
        volume = max(0.0, min(1.0, volume))
        for sound in self.sounds.values():
            sound.set_volume(volume)
            
    def cleanup(self):
        """Cleanup pygame mixer"""
        if self.is_initialized:
            pygame.mixer.quit()
            self.is_initialized = False

# Global audio manager instance
audio_manager = AudioAlertManager()

def play_fatigue_alert(alert_level: str):
    """Convenience function to play fatigue alert"""
    audio_manager.play_alert(alert_level)

if __name__ == "__main__":
    # Test the audio system
    manager = AudioAlertManager()
    manager.test_sounds()
