# https://colab.research.google.com/drive/1fxGqfg96RBUvGxZ1XXN07s3DthrKUl4-?usp=sharing#scrollTo=ku0ui5lKwpF7
# https://huggingface.co/spaces/facebook/MusicGen
# https://huggingface.co/facebook/musicgen-medium
# !python3 -m pip install -U git+https://github.com/facebookresearch/audiocraft#egg=audiocraft
# !python3 -m pip install -U audiocraft
import logging
logging.basicConfig(level=logging.DEBUG)
from audiocraft.utils.notebook import display_audio
from audiocraft.data.audio import audio_write
import torch
import os
import json
# os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
print("start...")
device = "cuda" if torch.cuda.is_available() else "cpu"

from datetime import datetime
def write_song():
    from audiocraft.models import musicgen
    model = musicgen.MusicGen.get_pretrained('small', device=device)
    model.set_generation_params(duration=8)
    now = datetime.now()
    songs = [
        # "轻柔,笛声，风铃",
        # 'crazy EDM, heavy bang', 
        # 'classic reggae track with an electronic guitar solo',
        # 'lofi slow bpm electro chill with organic samples',
        # 'rock with saturated guitars, a heavy bass line and crazy drum break and fills.',
        'earthy tones, environmentally conscious, ukulele-infused, harmonic, breezy, easygoing, organic instrumentation, gentle grooves',
        'splendid',
        'hi-fi synth space solo with shamanic vibers',
        "Morin Khuur, String Vibration, Long Tones, Mongolian Folk Melody",
        # 文学化
        # 天籁般的竖琴回音，迷人的琴弦细语，流畅的琶音流转，抒情的滑音轨迹，宁静的和弦交融，闪耀的和声涟漪，神秘的拨弦样式，静谧的旋律交织，天体般的音符舞动，轻柔的揉弦轻抚
        "Heavenly Harp Echoes, Enchanted String Whispers, Melting Arpeggio Flows, Lyrical Glissando Trails, Serene Chord Embrace, Sparkling Harmonic Ripples",
        # 专业名词
        # 半音滑音、泛音、分解和弦、持续音、哨音、颤音拨奏、分解和弦（不完全和弦）、自然音阶跑动、双音演奏、共鸣延音
        "Chromatic Glissando, Harmonic Overtones, Arpeggiated Chords, Pedal Tones, Flageolet Tones, Tremolo Picking, Broken Chords, Diatonic Scale Runs, Double Stops, Resonant Sustain",
        "Mysterious castle, spacious hall, bright torches, fluttering flags, noisy voices, magic academy, tense atmosphere, college sorting, marble staircase",
        "a hammer hitting a wooden surface.",
    ]
    songs = songs[-1:]
    end = datetime.now()
    print(end - now, "seconds")
    wav = model.generate(songs, progress=True)

    # write res to file

    for song, one_wav in zip(songs, wav):
        # Will save under {idx}.wav, with loudness normalization at -14 db LUFS.
        song = song[:5]
        audio_write(f'{song}', one_wav.cpu(), model.sample_rate, strategy="loudness")

write_song()
