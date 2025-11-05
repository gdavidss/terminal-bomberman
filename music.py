#!/usr/bin/env python3
"""Music and sound effects player for Bomberman"""

import pygame
import os
import time
import numpy as np

# Initialize pygame mixer for MIDI/music playback and sound effects
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

class MusicPlayer:
    def __init__(self, music_type='battle'):
        self.playing = False
        self.volume = 0.35  # Default volume (reduced to 50%)
        self.music_type = music_type
        self.music_file = None
        
        # Find the music file based on type
        script_dir = os.path.dirname(os.path.abspath(__file__))
        music_dir = os.path.join(script_dir, "music")
        
        # Map music types to file names
        music_files = {
            'battle': 'battle.mid',
            'stage-start': 'stage-start.mid',
            'game-over': 'game-over.mid',
            'victory': 'victory.mid'
        }
        
        if music_type in music_files:
            filename = music_files[music_type]
            self.music_path = os.path.join(music_dir, filename)
            
            if not os.path.exists(self.music_path):
                # Try without music/ subdirectory (backward compatibility)
                self.music_path = os.path.join(script_dir, filename)
                
            if not os.path.exists(self.music_path):
                print(f"⚠️ Music file '{filename}' not found!")
                self.music_path = None
        else:
            print(f"⚠️ Unknown music type: {music_type}")
            self.music_path = None
    
    def play_music(self, loops=-1):
        """Play the music file (loops=-1 for infinite, 0 for once)"""
        if not self.music_path:
            # No music file available - fail silently
            return None
            
        if not self.playing:
            try:
                self.playing = True
                
                # Load and play the MIDI file
                pygame.mixer.music.load(self.music_path)
                pygame.mixer.music.set_volume(self.volume)
                
                # Play with specified loops
                pygame.mixer.music.play(loops)
                
                # Music is playing, no need to print messages
                return True
            except Exception as e:
                # Could not play music - fail silently
                self.playing = False
                return None
    
    def stop_music(self):
        """Stop the music"""
        if self.playing:
            pygame.mixer.music.stop()
            self.playing = False
            pass  # Music stopped silently
    
    def pause_music(self):
        """Pause the music"""
        if self.playing:
            pygame.mixer.music.pause()
    
    def unpause_music(self):
        """Resume the music"""
        if self.playing:
            pygame.mixer.music.unpause()
    
    def set_volume(self, volume):
        """Set music volume (0.0 to 1.0)"""
        self.volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.volume)
    
    def toggle_music(self):
        """Toggle music on/off"""
        if self.playing:
            self.stop_music()
            return False
        else:
            return self.play_music()

# Global music player instances
music_players = {}
music_enabled = True
current_music = None

def play_music(music_type='battle', loops=-1):
    """Play specific music type"""
    global music_players, music_enabled, current_music
    
    if not music_enabled:
        return False
    
    # Stop current music if playing
    stop_current_music()
    
    try:
        player = MusicPlayer(music_type)
        if player.music_path:
            music_players[music_type] = player
            current_music = music_type
            return player.play_music(loops)
        else:
            # Music not available - fail silently
            return False
    except Exception as e:
        # Could not play music - fail silently
        return False

def stop_current_music():
    """Stop the currently playing music"""
    global music_players, current_music
    
    if current_music and current_music in music_players:
        music_players[current_music].stop_music()
        del music_players[current_music]
        current_music = None

def start_jungle_music():
    """Start playing the battle music (backward compatibility)"""
    return play_music('battle', loops=-1)

def stop_jungle_music():
    """Stop playing the music (backward compatibility)"""
    stop_current_music()

def play_stage_start():
    """Play stage start music (once)"""
    return play_music('stage-start', loops=0)

def play_game_over():
    """Play game over music (once)"""
    return play_music('game-over', loops=0)

def play_victory():
    """Play victory music (once)"""
    return play_music('victory', loops=0)

def toggle_music():
    """Toggle music on/off"""
    global music_enabled, current_music
    
    if music_enabled:
        # Turn off
        stop_current_music()
        music_enabled = False
        pass  # Music turned off silently
    else:
        # Turn on - resume battle music
        music_enabled = True
        start_jungle_music()
        pass  # Music turned on silently

def pause_music():
    """Pause the currently playing music"""
    global music_players, current_music
    
    if current_music and current_music in music_players:
        music_players[current_music].pause_music()

def unpause_music():
    """Resume the currently playing music"""
    global music_players, current_music
    
    if current_music and current_music in music_players:
        music_players[current_music].unpause_music()

def set_music_volume(volume):
    """Set the music volume (0.0 to 1.0)"""
    global music_players, current_music
    
    if current_music and current_music in music_players:
        music_players[current_music].set_volume(volume)

# Wait for music to finish (for non-looping tracks)
def wait_for_music():
    """Wait for current music to finish playing"""
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)

# ============ SOUND EFFECTS ============

class SoundEffect:
    """Handles sound effects for the game"""
    def __init__(self):
        self.bomb_sounds = []
        self.scream_sound = None
        self.pause_sound = None
        self.select_sound = None
        self.i_won_sound = None
        self.nooo_sound = None
        self.bomb_up_sound = None
        self.volume = 0.4  # Reduced to 50%
        self._load_sound_effects()
    
    def _load_sound_effects(self):
        """Load all sound effect files"""
        try:
            import random
            script_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Load bomb sounds (randomly choose between large and medium)
            bomb_files = ['bomb_large.wav', 'bomb_medium.wav']
            for bomb_file in bomb_files:
                bomb_path = os.path.join(script_dir, 'music', bomb_file)
                if os.path.exists(bomb_path):
                    sound = pygame.mixer.Sound(bomb_path)
                    sound.set_volume(self.volume)
                    self.bomb_sounds.append(sound)
            
            # Load scream sound
            scream_path = os.path.join(script_dir, 'music', 'bomberman_scream.wav')
            if os.path.exists(scream_path):
                self.scream_sound = pygame.mixer.Sound(scream_path)
                self.scream_sound.set_volume(self.volume)
            
            # Load pause sound
            pause_path = os.path.join(script_dir, 'music', 'pause.wav')
            if os.path.exists(pause_path):
                self.pause_sound = pygame.mixer.Sound(pause_path)
                self.pause_sound.set_volume(self.volume)
            
            # Load select sound
            select_path = os.path.join(script_dir, 'music', 'select.wav')
            if os.path.exists(select_path):
                self.select_sound = pygame.mixer.Sound(select_path)
                self.select_sound.set_volume(self.volume)
            
            # Load i_won sound
            i_won_path = os.path.join(script_dir, 'music', 'i_won.wav')
            if os.path.exists(i_won_path):
                self.i_won_sound = pygame.mixer.Sound(i_won_path)
                self.i_won_sound.set_volume(self.volume)
            
            # Load nooo sound
            nooo_path = os.path.join(script_dir, 'music', 'nooo.wav')
            if os.path.exists(nooo_path):
                self.nooo_sound = pygame.mixer.Sound(nooo_path)
                self.nooo_sound.set_volume(self.volume)
            
            # Load bomb_up sound
            bomb_up_path = os.path.join(script_dir, 'music', 'bomb_up.wav')
            if os.path.exists(bomb_up_path):
                self.bomb_up_sound = pygame.mixer.Sound(bomb_up_path)
                self.bomb_up_sound.set_volume(self.volume)
            
        except Exception as e:
            # Could not load sound effects - fail silently
            pass
    
    def play_explosion(self):
        """Play a random explosion sound effect"""
        if self.bomb_sounds:
            try:
                import random
                # Randomly choose between bomb_large and bomb_medium
                sound = random.choice(self.bomb_sounds)
                sound.play()
            except Exception as e:
                # Could not play explosion sound - fail silently
                pass
    
    def play_scream(self):
        """Play the bomberman scream sound"""
        if self.scream_sound:
            try:
                self.scream_sound.play()
            except Exception:
                pass
    
    def play_pause(self):
        """Play the pause/unpause sound"""
        if self.pause_sound:
            try:
                self.pause_sound.play()
            except Exception:
                pass
    
    def play_select(self):
        """Play the select/menu sound"""
        if self.select_sound:
            try:
                self.select_sound.play()
            except Exception:
                pass
    
    def play_i_won(self):
        """Play the i_won victory sound"""
        if self.i_won_sound:
            try:
                self.i_won_sound.play()
            except Exception:
                pass
    
    def play_nooo(self):
        """Play the nooo death sound"""
        if self.nooo_sound:
            try:
                self.nooo_sound.play()
            except Exception:
                pass
    
    def play_bomb_up(self):
        """Play the bomb_up power-up sound"""
        if self.bomb_up_sound:
            try:
                self.bomb_up_sound.play()
            except Exception:
                pass
    
    def set_volume(self, volume):
        """Set the volume for sound effects (0.0 to 1.0)"""
        self.volume = max(0.0, min(1.0, volume))
        for sound in self.bomb_sounds:
            sound.set_volume(self.volume)
        if self.scream_sound:
            self.scream_sound.set_volume(self.volume)
        if self.pause_sound:
            self.pause_sound.set_volume(self.volume)
        if self.select_sound:
            self.select_sound.set_volume(self.volume)
        if self.i_won_sound:
            self.i_won_sound.set_volume(self.volume)
        if self.nooo_sound:
            self.nooo_sound.set_volume(self.volume)
        if self.bomb_up_sound:
            self.bomb_up_sound.set_volume(self.volume)

# Global sound effects instance
sound_effects = None
sound_effects_enabled = True

def init_sound_effects():
    """Initialize sound effects"""
    global sound_effects, sound_effects_enabled
    
    if sound_effects_enabled and sound_effects is None:
        try:
            sound_effects = SoundEffect()
            # Sound effects initialized successfully
            return True
        except Exception as e:
            # Could not initialize sound effects - fail silently
            sound_effects_enabled = False
            return False
    return sound_effects is not None

def play_bomb_explosion():
    """Play bomb explosion sound effect"""
    global sound_effects, sound_effects_enabled
    
    if not sound_effects_enabled:
        return
    
    # Initialize if needed
    if sound_effects is None:
        init_sound_effects()
    
    # Play the explosion
    if sound_effects:
        sound_effects.play_explosion()

def play_bomberman_scream():
    """Play bomberman scream sound effect"""
    global sound_effects, sound_effects_enabled
    
    if not sound_effects_enabled:
        return
    
    # Initialize if needed
    if sound_effects is None:
        init_sound_effects()
    
    # Play the sound
    if sound_effects:
        sound_effects.play_scream()

def play_pause_sound():
    """Play pause/unpause sound effect"""
    global sound_effects, sound_effects_enabled
    
    if not sound_effects_enabled:
        return
    
    # Initialize if needed
    if sound_effects is None:
        init_sound_effects()
    
    # Play the sound
    if sound_effects:
        sound_effects.play_pause()

def play_select_sound():
    """Play select/menu sound effect"""
    global sound_effects, sound_effects_enabled
    
    if not sound_effects_enabled:
        return
    
    # Initialize if needed
    if sound_effects is None:
        init_sound_effects()
    
    # Play the sound
    if sound_effects:
        sound_effects.play_select()

def play_i_won_sound():
    """Play i_won victory sound effect"""
    global sound_effects, sound_effects_enabled
    
    if not sound_effects_enabled:
        return
    
    # Initialize if needed
    if sound_effects is None:
        init_sound_effects()
    
    # Play the sound
    if sound_effects:
        sound_effects.play_i_won()

def play_nooo_sound():
    """Play nooo death sound effect"""
    global sound_effects, sound_effects_enabled
    
    if not sound_effects_enabled:
        return
    
    # Initialize if needed
    if sound_effects is None:
        init_sound_effects()
    
    # Play the sound
    if sound_effects:
        sound_effects.play_nooo()

def play_bomb_up_sound():
    """Play bomb_up power-up sound effect"""
    global sound_effects, sound_effects_enabled
    
    if not sound_effects_enabled:
        return
    
    # Initialize if needed
    if sound_effects is None:
        init_sound_effects()
    
    # Play the sound
    if sound_effects:
        sound_effects.play_bomb_up()

def toggle_sound_effects():
    """Toggle sound effects on/off"""
    global sound_effects_enabled
    
    sound_effects_enabled = not sound_effects_enabled
    if sound_effects_enabled:
        pass  # Sound effects turned on silently
        init_sound_effects()
    else:
        pass  # Sound effects turned off silently

def set_effects_volume(volume):
    """Set the sound effects volume (0.0 to 1.0)"""
    global sound_effects
    
    if sound_effects:
        sound_effects.set_volume(volume)

if __name__ == "__main__":
    # Test the music and sound effects
    print("🎵 Testing Bomberman Music & Sound System")
    print("="*50)
    
    # Test music
    print("\n📻 Testing Music Files:")
    music_types = ['stage-start', 'battle', 'victory', 'game-over']
    
    for music_type in music_types:
        print(f"  Testing {music_type}...")
        player = MusicPlayer(music_type)
        if player.music_path:
            print(f"  ✅ {music_type} music found")
        else:
            print(f"  ❌ {music_type} music not found")
    
    # Test sound effects
    print("\n💣 Testing Sound Effects:")
    if init_sound_effects():
        print("  ✅ Sound effects initialized")
        print("  Playing explosion sound 3 times...")
        for i in range(3):
            print(f"  💥 Explosion {i+1}")
            play_bomb_explosion()
            time.sleep(0.7)
    else:
        print("  ❌ Sound effects initialization failed")
    
    print("\n🎮 Playing battle music for 3 seconds...")
    if play_music('battle'):
        try:
            time.sleep(3)
            print("🔇 Stopping music...")
            stop_current_music()
        except KeyboardInterrupt:
            print("\n🔇 Stopping music...")
            stop_current_music()
    
    pygame.quit()