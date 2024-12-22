#!/usr/bin/env python
# coding: utf-8

# input: output.json
# 生成的音乐.wav文件名最后的数字是output.json文件中的”pid“字段，也就是每句话的ID
# 还有一个总体的背景音乐，提取output.json的music中出现次数最多的单词生成的一段长音乐（28s）
# 时长不够应该可以循环


from transformers import AutoProcessor, MusicgenForConditionalGeneration


# In[34]:


from IPython.display import Audio
import scipy
from collections import Counter
import numpy as np


# In[20]:


import json


# In[7]:


processor = AutoProcessor.from_pretrained("facebook/musicgen-large")
model = MusicgenForConditionalGeneration.from_pretrained("facebook/musicgen-large")


# In[48]:


with open('output.json', 'r', encoding='utf-8') as json_file:
    items = json.load(json_file)

music_style = []
sampling_rate = model.config.audio_encoder.sampling_rate
for item in items:
    music_prompt = item['music']
    if music_prompt == '' or music_prompt == '无':
        continue
    music_style.append(music_prompt)
    inputs = processor(text=["50s"+music_prompt], padding=True, return_tensors="pt")

    audio_values = model.generate(**inputs, max_new_tokens=256)

    audio_file_path = f"./music/generated_music_{item['pid']}.wav" 
    scipy.io.wavfile.write(audio_file_path, rate=sampling_rate, data=audio_values[0, 0].numpy())


# In[41]:


words = [word.strip() for phrase in music_style for word in phrase.split(',')]
word_counts = Counter(words)

most_common = word_counts.most_common(1)
most_common_word = [word for word, count in most_common][0]
print(most_common_word)


# In[62]:


inputs = processor(text=["500s "+most_common_word+"and smooth and diverse background music for the play"], padding=True, return_tensors="pt")
max_new_tokens = 1000
audio_values = model.generate(**inputs, max_new_tokens=max_new_tokens)

audio_data = (audio_values[0, 0].numpy() * 32767).astype(np.int16)

sampling_rate = 22050


# In[63]:


Audio(audio_values[0].numpy(), rate=sampling_rate)


# In[65]:


scipy.io.wavfile.write("./music/total_musicgen_out.wav", rate=sampling_rate, data=audio_values[0, 0].numpy())




