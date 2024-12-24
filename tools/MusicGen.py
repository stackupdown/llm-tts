#!/usr/bin/env python
# coding: utf-8


from transformers import AutoProcessor, MusicgenForConditionalGeneration

from IPython.display import Audio
import scipy
from collections import Counter
import numpy as np

import json


processor = AutoProcessor.from_pretrained("facebook/musicgen-large")
model = MusicgenForConditionalGeneration.from_pretrained("facebook/musicgen-large")


with open('output_AddID.json', 'r', encoding='utf-8') as json_file:
    items = json.load(json_file)
    
pid_duration = {}
music_style = []
for item in items:
    pid = item['pid']
    text = item['text']
    music_prompt = item['music']
    time = item['audio_time_length']
    if pid in pid_duration:
        pid_duration[pid] += time+0.5
    else:
        pid_duration[pid] = time

        music_style.append(music_prompt)

words = [word.strip() for phrase in music_style for word in phrase.split(',')]
word_counts = Counter(words)

most_common = word_counts.most_common(1)
most_common_word = [word for word, count in most_common][0]
print(most_common_word)


sampling_rate = 22050
for item in items:
    
    music_prompt = item['music']
    pid = item['pid']

    duration = pid_duration[pid]
    if duration > 30:
        duration = 30
    if music_prompt == '' or music_prompt == '无' or most_common_word in music_prompt or duration < 10:
        continue
    inputs = processor(text=["50s"+music_prompt], padding=True, return_tensors="pt")

    max_tokens = int(22050 * duration / 617)
    audio_values = model.generate(**inputs, max_new_tokens=max_tokens)

    audio_file_path = f"./music/{item['pid']}.wav" 
    scipy.io.wavfile.write(audio_file_path, rate=sampling_rate, data=audio_values[0, 0].numpy())


inputs = processor(text=["500s "+most_common_word+"and smooth and diverse background music for the play"], padding=True, return_tensors="pt")
max_new_tokens = 1000
audio_values = model.generate(**inputs, max_new_tokens=max_new_tokens)

audio_data = (audio_values[0, 0].numpy() * 32767).astype(np.int16)

sampling_rate = 22050




Audio(audio_values[0].numpy(), rate=sampling_rate)


scipy.io.wavfile.write("./music/total_musicgen_out.wav", rate=sampling_rate, data=audio_values[0, 0].numpy())


sampling_rate = 22050
for item in items:
    
    music_prompt = item['sound']
    audio_id = item['audio_id']
    duration = item['audio_time_length']
    if duration > 30:
        duration = 30
    if music_prompt == '' or music_prompt == '无' :
        continue
    inputs = processor(text=["50s"+music_prompt], padding=True, return_tensors="pt")

    max_tokens = int(22050 * duration / 617)
    audio_values = model.generate(**inputs, max_new_tokens=max_tokens)

    audio_file_path = f"./audio/{item['audio_id']}.wav" 
    scipy.io.wavfile.write(audio_file_path, rate=sampling_rate, data=audio_values[0, 0].numpy())




