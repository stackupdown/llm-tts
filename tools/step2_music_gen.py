# music gen
import scipy
import json
import os
from collections import Counter
import torch
from pydub.utils import mediainfo

os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
print("start...")
prefix = './output/harry'
music_dir = f'{prefix}/music/'
# TODO: step1 inference generate
audio_dir = f'{prefix}/audio/'
json_file = 'output.json'
updated_json_file = 'output_addid.json'
device = 'cuda' if torch.cuda.is_available() else 'cpu'

if not os.path.exists(music_dir):
    os.makedirs(music_dir)

if not os.path.exists(audio_dir):
    os.makedirs(audio_dir)

from audiocraft.models import musicgen
from audiocraft.data.audio import audio_write
import tqdm

def get_model():
    global device
    model = musicgen.MusicGen.get_pretrained('small', device=device)
    print("load model, sample_rate", model.sample_rate)
    return model

def generate_music(model, pid, music_prompt, duration, most_common_word):
    global sampling_rate
    if music_prompt == '' or music_prompt == '无' or most_common_word in music_prompt or duration < 10:
        return

    audio_file_path = os.path.join(music_dir, f"{pid}.wav")
    songs = [music_prompt]
    wav = model.generate(songs, progress=True)
    # write res to file
    for song, one_wav in zip(songs, wav):
        # Will save under {idx}.wav, with loudness normalization at -14 db LUFS.
        audio_write(audio_file_path, one_wav.cpu(), model.sample_rate, strategy="loudness")
        print("audio_write to ", audio_file_path)

def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_audio_length(audio_path):
    info = mediainfo(audio_path)
    # 单位: 秒
    return float(info["duration"])

def save_json(data, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def update_json_with_audio_info(data, audio_folder):
    # format of path is []
    # from idx to audio id

    if not os.path.exists(audio_folder):
        raise Exception(f"not found {audio_folder}")

    for idx, cell in enumerate(data):
        audio_path = os.path.join(audio_folder, f"{idx + 1}.wav")
        print("audio path", audio_path)
        if not os.path.exists(audio_path):
            raise Exception(f"not found {audio_path}")

        audio_time_length = get_audio_length(audio_path)
        print("audio time is ", audio_time_length)
        # TODO: can this be automatically decied as insert?
        cell["insert_type"] = 'overlay'
        cell["audio_time_length"] = audio_time_length
    return data


def whole_generate():
    model = get_model()
    items = load_json(json_file)
    pid_duration = {}
    music_style = []
    items = update_json_with_audio_info(items, audio_dir)
    save_json(items, updated_json_file)
    print(f"更新完成, 已经保存到 {updated_json_file}")

    for item in items:
        pid = item['pid']
        music_prompt = item['music']
        time = item['audio_time_length']
        if pid in pid_duration:
            # pid_duration[pid] += time + 0.5
            pid_duration[pid] += time # no need to add 0.5
        else:
            pid_duration[pid] = time
            music_style.append(music_prompt)

    words = [word.strip() for phrase in music_style for word in phrase.split(',')]
    print(words)
    word_counts = Counter(words)

    most_common = word_counts.most_common(5)
    most_common_word = [word for word, count in most_common][0]
    print(most_common_word)

    for item in tqdm.tqdm(items):
        music_prompt = item['music']
        pid = item['pid']
        duration = pid_duration[pid]
        print("duration", duration, music_prompt)
        if duration > 30:
            duration = 30
        model.set_generation_params(duration=duration)
        generate_music(model, pid, music_prompt, duration, most_common_word)


if __name__ == '__main__':
    whole_generate()
