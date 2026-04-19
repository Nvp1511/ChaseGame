import json
import os

import pygame


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOUNDS_DIR = os.path.join(BASE_DIR, "assets", "sounds")
AUDIO_SETTINGS_PATH = os.path.join(BASE_DIR, "config", "audio_settings.json")

DEFAULT_VOLUME = 0.8

_SOUNDS = {}
_VOLUME = DEFAULT_VOLUME
_AUDIO_READY = False


SOUND_FILES = {
    "start_up": "start_up.wav",
    "eat": "eat.wav",
    "death": "death.wav",
    "round_end": "round_end.wav",
}


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

    if persist:
        try:
            save_audio_settings()
        except OSError:
            pass


def play_sound(sound_key):
    if not _AUDIO_READY:
        return

    sound = _SOUNDS.get(sound_key)
    if sound is None:
        return

    try:
        sound.play()
    except pygame.error:
        return
