# music gen
import scipy
import json
import os
from collections import Counter
import torch
from pydub.utils import mediainfo
import logging

os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
print("start...")
prefix = './output/harry'
music_dir = f'{prefix}/music/'
# TODO: step1 inference generate
audio_dir = f'{prefix}/audio/g_00140000'
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
    # if music_prompt == '' or music_prompt == '无' or most_common_word in music_prompt or duration < 10:
    #     return
    if music_prompt == '' or music_prompt == '无' or duration < 10:
        return
    if duration > 30:
        duration = 30
    model.set_generation_params(duration=duration)
    audio_file_path = os.path.join(music_dir, str(pid)) # no need to add .wav

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

    if not os.path.exists(audio_folder):
        raise Exception(f"not found {audio_folder}")
    print("audio folder", audio_folder)
    pid_duration = {}
    for idx, cell in enumerate(data):
        audio_path = os.path.join(audio_folder, f"{idx + 1}.wav")
        cell['play_music'] = 0
        pid = cell['pid']
        if not os.path.exists(audio_path):
            raise Exception(f"not found {audio_path}")

        audio_time_length = get_audio_length(audio_path)
        cell["audio_time_length"] = audio_time_length
        print("audio path", audio_path, audio_time_length)
        if pid in pid_duration:
            pid_duration[pid] += audio_time_length # no need to add 0.5
        else:
            pid_duration[pid] = audio_time_length

    # add logic
    pid_idx = {}
    music_candidates = [(1, 0)]
    # 记录候选集
    for idx, cell in enumerate(data):
        pid = cell['pid']
        if cell['music'] == '' or pid_duration[pid] < 10:
            continue
        if pid in pid_idx:
            continue
        # add to last
        pid_idx[pid] = idx
        music_candidates.append((pid, idx))

    result_candidates = music_candidates[::len(music_candidates) // 10]
    for cand in result_candidates:
        cell = data[cand[1]]
        cell["insert_type"] = 'insert'
        cell['play_music'] = 1

    print("success set play music", result_candidates)

    return data

def update_json_with_sound_effect(data, music_folder):
    if not os.path.exists(music_folder):
        raise Exception(f"not found {music_folder}")
    print("music folder", music_folder)
    pid_music = {}
    for idx, cell in enumerate(data):
        music_path = os.path.join(music_folder, f"{idx + 1}.wav")
        cell['play_music'] = 0
        pid = cell['pid']
        if not os.path.exists(music_path):
            raise Exception(f"not found {music_path}")

def get_all_words(music_style):
    return [word.strip() for phrase in music_style for word in phrase.split(',')]

def whole_generate():
    model = get_model()
    items = load_json(json_file)
    pid_duration = {}
    music_style = []
    if os.path.exists(updated_json_file):
        items = load_json(updated_json_file)
        logging.info(f"already exist {updated_json_file}, if you want to update, please delete it")
    else:
        # generate at most music per minute
        # 开场有音乐；说话太短不要有音乐；总体生成10个音乐循环播放；
        # 有说话声的时候必须减小音量；
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

    words = get_all_words(music_style)
    print(words)
    word_counts = Counter(words)

    most_common = word_counts.most_common(5)
    most_common_word = [word for word, count in most_common][0]
    print(most_common_word)
    cnt = 1
    for item in tqdm.tqdm(items):
        music_prompt = item['music']
        pid = item['pid']
        duration = pid_duration[pid]
        if item['play_music']:
            print("duration {}, {} for {}".format(duration, music_prompt, pid))
            generate_music(model, pid, music_prompt, duration, most_common_word)
        else:
            print("ignore {}, {} for {}".format(duration, music_prompt, pid))

    print(cnt)


if __name__ == '__main__':
    whole_generate()
