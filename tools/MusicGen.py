#!/usr/bin/env python
# coding: utf-8

# In[1]:


from transformers import AutoProcessor, MusicgenForConditionalGeneration


# In[2]:


from IPython.display import Audio
import scipy
from collections import Counter
import numpy as np


# In[3]:


import json


# In[4]:


processor = AutoProcessor.from_pretrained("facebook/musicgen-large")
model = MusicgenForConditionalGeneration.from_pretrained("facebook/musicgen-large")


# In[ ]:


with open('output.json', 'r', encoding='utf-8') as json_file:
    items = json.load(json_file)
    
pid_character_count = {}
music_style = []
for item in items:
    pid = item['pid']
    text = item['text']
    music_prompt = item['music']
    text_length = len(text)
    if pid in pid_character_count:
        pid_character_count[pid] += text_length
    else:
        pid_character_count[pid] = text_length

        music_style.append(music_prompt)

words = [word.strip() for phrase in music_style for word in phrase.split(',')]
word_counts = Counter(words)

most_common = word_counts.most_common(1)
most_common_word = [word for word, count in most_common][0]
print(most_common_word)


# In[14]:


sampling_rate = 22050
for item in items:
    print(1)
    music_prompt = item['music']
    pid = item['pid']
    duration = pid_character_count[pid] * 0.3 # one character: 0.3s
    if duration > 30:
        duration = 30
    if music_prompt == '' or music_prompt == '无' or most_common_word in music_prompt or duration < 10:
        continue
    inputs = processor(text=["50s"+music_prompt], padding=True, return_tensors="pt")

    max_tokens = int(22050 * duration / 617)
    audio_values = model.generate(**inputs, max_new_tokens=max_tokens)

    audio_file_path = f"./music/generated_music_{item['pid']}_{int(duration)}s.wav" 
    scipy.io.wavfile.write(audio_file_path, rate=sampling_rate, data=audio_values[0, 0].numpy())


# In[62]:


inputs = processor(text=["500s "+most_common_word+"and smooth and diverse background music for the play"], padding=True, return_tensors="pt")
max_new_tokens = 1000
audio_values = model.generate(**inputs, max_new_tokens=max_new_tokens)

audio_data = (audio_values[0, 0].numpy() * 32767).astype(np.int16)

sampling_rate = 22050


# In[63]:


Audio(audio_values[0].numpy(), rate=sampling_rate)


scipy.io.wavfile.write("./music/total_musicgen_out.wav", rate=sampling_rate, data=audio_values[0, 0].numpy())





