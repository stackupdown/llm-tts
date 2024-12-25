# music gen
import scipy
import json
import os
from collections import Counter
from audiocraft.models import musicgen
from audiocraft.data.audio import audio_write

os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
print("start...")

music_dir = './music/'
json_file = 'output_AddID.json'

def load_data():
    global music_dir
    global json_file
    with open(json_file, 'r', encoding='utf-8') as f:
        items = json.load(f)

    if not os.path.exists(music_dir):
        os.makedirs(music_dir)
    return items

items = load_data()
sampling_rate = 22050

def get_model():
    model = musicgen.MusicGen.get_pretrained('small', device='cpu')
    return model

def generate_music(model, pid, music_prompt, duration, most_common_word):
    global sampling_rate
    if duration > 30:
        duration = 30
    if music_prompt == '' or music_prompt == '无' or most_common_word in music_prompt or duration < 10:
        return

    audio_file_path = f"./music/{pid}.wav"
    songs = [music_prompt]
    wav = model.generate(songs, progress=True)
    # write res to file
    for song, one_wav in zip(songs, wav):
        # Will save under {idx}.wav, with loudness normalization at -14 db LUFS.
        audio_write(audio_file_path, one_wav.cpu(), model.sample_rate, strategy="loudness")
        break


def whole_generate():

    global sampling_rate
    model = get_model()

    pid_duration = {}
    music_style = []
    for item in items:
        pid = item['pid']
        text = item['text']
        music_prompt = item['music']
        time = item['audio_time_length']
        if pid in pid_duration:
            pid_duration[pid] += time + 0.5
        else:
            pid_duration[pid] = time
            music_style.append(music_prompt)

    words = [word.strip() for phrase in music_style for word in phrase.split(',')]
    print(words)
    word_counts = Counter(words)

    most_common = word_counts.most_common(5)
    most_common_word = [word for word, count in most_common][0]
    print(most_common_word)

    for item in items:
        music_prompt = item['music']
        pid = item['pid']
        duration = pid_duration[pid]
        model.set_generation_params(duration=duration)
        print("duration", duration)
        generate_music(model, pid, music_prompt, duration, most_common_word)


if __name__ == '__main__':
    whole_generate()
