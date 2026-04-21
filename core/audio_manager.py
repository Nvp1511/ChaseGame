import json
import os
import random

import pygame


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOUNDS_DIR = os.path.join(BASE_DIR, "assets", "sounds")
AUDIO_SETTINGS_PATH = os.path.join(BASE_DIR, "config", "audio_settings.json")

DEFAULT_VOLUME = 0.8

_SOUNDS = {}
_VOLUME = DEFAULT_VOLUME
_AUDIO_READY = False
_MUSIC_VOLUME_SCALE = 0.35
_LOOPING_CHANNELS = {}


SOUND_FILES = {
    "start_up": "start_up.wav",
    "eat": "eat.wav",
    "death": "death.wav",
    "round_end": "round_end.wav",
    "danger": "danger.mp3",
}

BACKGROUND_MUSIC_FILE = "music_game.wav"


def _clamp_volume(volume):
    return max(0.0, min(1.0, float(volume)))


def _load_saved_volume():
    if not os.path.exists(AUDIO_SETTINGS_PATH):
        return DEFAULT_VOLUME

    try:
        with open(AUDIO_SETTINGS_PATH, "r", encoding="utf-8") as file:
            data = json.load(file)
            return _clamp_volume(data.get("volume", DEFAULT_VOLUME))
    except (json.JSONDecodeError, OSError, ValueError, TypeError):
        return DEFAULT_VOLUME


def save_audio_settings():
    os.makedirs(os.path.dirname(AUDIO_SETTINGS_PATH), exist_ok=True)
    payload = {"volume": _clamp_volume(_VOLUME)}
    with open(AUDIO_SETTINGS_PATH, "w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=True, indent=2)


def init_audio():
    global _AUDIO_READY, _VOLUME

    if _AUDIO_READY:
        return

    _VOLUME = _load_saved_volume()

    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
    except pygame.error:
        _AUDIO_READY = False
        return

    for sound_key, file_name in SOUND_FILES.items():
        sound_path = os.path.join(SOUNDS_DIR, file_name)
        if not os.path.exists(sound_path):
            continue
        try:
            _SOUNDS[sound_key] = pygame.mixer.Sound(sound_path)
        except pygame.error:
            continue

    _AUDIO_READY = True
    set_master_volume(_VOLUME, persist=False)


def get_master_volume():
    return _VOLUME


def set_master_volume(volume, persist=True):
    global _VOLUME

    _VOLUME = _clamp_volume(volume)
    for sound in _SOUNDS.values():
        sound.set_volume(_VOLUME)
    for _sound_key, (_channel, _scale) in list(_LOOPING_CHANNELS.items()):
        if _channel is None or (not _channel.get_busy()):
            _LOOPING_CHANNELS.pop(_sound_key, None)
            continue
        _channel.set_volume(_clamp_volume(_VOLUME * _scale))

    if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
        pygame.mixer.music.set_volume(_clamp_volume(_VOLUME * _MUSIC_VOLUME_SCALE))

    if persist:
        try:
            save_audio_settings()
        except OSError:
            pass


def play_sound(sound_key, volume_scale=1.0, vary=False):
    if not _AUDIO_READY:
        return

    sound = _SOUNDS.get(sound_key)
    if sound is None:
        return

    try:
        scale = _clamp_volume(volume_scale)
        if vary:
            scale = _clamp_volume(scale * random.uniform(0.92, 1.08))

        channel = sound.play()
        if channel is not None:
            channel.set_volume(_clamp_volume(_VOLUME * scale))
    except pygame.error:
        return


def play_loop_sound(sound_key, volume_scale=1.0):
    if not _AUDIO_READY:
        return

    sound = _SOUNDS.get(sound_key)
    if sound is None:
        return

    existing = _LOOPING_CHANNELS.get(sound_key)
    if existing is not None:
        channel, scale = existing
        if channel is not None and channel.get_busy():
            channel.set_volume(_clamp_volume(_VOLUME * scale))
            return
        _LOOPING_CHANNELS.pop(sound_key, None)

    try:
        scale = _clamp_volume(volume_scale)
        channel = sound.play(loops=-1)
        if channel is None:
            return
        channel.set_volume(_clamp_volume(_VOLUME * scale))
        _LOOPING_CHANNELS[sound_key] = (channel, scale)
    except pygame.error:
        return


def stop_loop_sound(sound_key, fade_ms=120):
    existing = _LOOPING_CHANNELS.pop(sound_key, None)
    if existing is None:
        return

    channel, _scale = existing
    if channel is None:
        return

    try:
        if fade_ms > 0:
            channel.fadeout(fade_ms)
        else:
            channel.stop()
    except pygame.error:
        return


def play_background_music(loop=True, volume_scale=0.35):
    global _MUSIC_VOLUME_SCALE

    if not _AUDIO_READY:
        return

    music_path = os.path.join(SOUNDS_DIR, BACKGROUND_MUSIC_FILE)
    if not os.path.exists(music_path):
        return

    try:
        _MUSIC_VOLUME_SCALE = _clamp_volume(volume_scale)
        pygame.mixer.music.load(music_path)
        pygame.mixer.music.set_volume(_clamp_volume(_VOLUME * _MUSIC_VOLUME_SCALE))
        pygame.mixer.music.play(-1 if loop else 0)
    except pygame.error:
        return


def stop_background_music(fade_ms=250):
    if not pygame.mixer.get_init():
        return
    try:
        if pygame.mixer.music.get_busy():
            if fade_ms > 0:
                pygame.mixer.music.fadeout(fade_ms)
            else:
                pygame.mixer.music.stop()
    except pygame.error:
        return
