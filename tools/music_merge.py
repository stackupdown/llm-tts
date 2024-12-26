# -*- coding: utf-8 -*-
import os
from pydub import AudioSegment
import numpy as np
import matplotlib.pyplot as plt

BASE_DATA_PATH = '../data/'
audio_folder_path = os.path.join(BASE_DATA_PATH, "harry/audio/")
music_folder_path = os.path.join(BASE_DATA_PATH, "music_demo/")
music_file = os.path.join(music_folder_path, 'earth.wav')
# filelist_txt = os.path.join(BASE_DATA_PATH, "music_demo/filelist.txt")
output_file = './merge_output2.wav'
# read all wav files
# read filelist.txt
# read based on filelist.txt
# output to new file

audio_files = [f for f in os.listdir(audio_folder_path) if f.endswith('.wav')]

def sorted_audio(audio_folder_path):
    audio_files = [f for f in os.listdir(audio_folder_path) if f.endswith('.wav')]
    return sorted(audio_files, key=lambda x: int(x[:-4]))

import tqdm
def merge_and_mix_audio(audio_folder_path, music_file, output_file):
    # 合并 audio_folder_path 中的所有 wav 文件
    audio_segments = []
    audio_files = sorted_audio(audio_folder_path)

    silence = AudioSegment.silent(duration=800)

    for file_path in tqdm.tqdm(audio_files):
        file_path = os.path.join(audio_folder_path, file_path)
        audio_segment = AudioSegment.from_wav(file_path)
        audio_segment = silence + audio_segment
        audio_segments.append(audio_segment)

    audio = sum(audio_segments)  # 合并音频

    # 加载 music 文件
    music = AudioSegment.from_wav(music_file)
    k = len(audio) // len(music)
    repeated_music = music * k

    # 播放 music 一段时间，这里假设播放前 20 秒
    music_first_part = repeated_music[:10 * 1000]
    # 剩余部分
    music_remaining = repeated_music[10 * 1000:]
    print(music_remaining)
    # 调整 music_remaining 的音量，例如将音量减半
    music_remaining = music_remaining - 20  # 降低 6dB

    # 混合 music_remaining 和 audio
    final_audio = music_remaining.overlay(audio)

    # 组合最终的音频
    final_audio = music_first_part + final_audio

    # 导出最终音频文件
    final_audio.export(output_file, format='wav')


def play_audio_wav_graph(music_file_path):
    # 读取音频文件
    music = AudioSegment.from_wav(music_file_path)
    repeated_seconds = 40000
    print(len(music))
    seconds = int(len(music) / 1000)
    # clip to seconds
    for duration in range(3, seconds):
        print("duration: ", duration)
        repeated_music = AudioSegment.silent(duration=100)
        offset = duration * 1000
        next_music = music[:offset]
        k = repeated_seconds // offset

        for _ in range(k):
            # 淡入淡出效果
            repeated_music += next_music

        # 导出最终音频文件
        repeated_music.export(f"repeated_{duration}.wav", format='wav')

    # samples = np.array(repeated_music.get_array_of_samples())
    # plt.figure(figsize=(14, 5))
    # plt.plot(samples)
    # plt.title("Repeated Music Waveform")
    # plt.xlabel("Sample")
    # plt.ylabel("Amplitude")
    # plt.show()

def repeat_fade_audio_wav(music_file_path, repeated_seconds=40000):
    # 读取音频文件
    music = AudioSegment.from_wav(music_file_path)
    print(len(music))
    seconds = len(music)
    # clip to seconds
    duration = 2
    faded_in_duration = 2000
    faded_out_duration = 2000

    repeated_music = music
    # the duration is [mlen, mlen - d, mlen - d, ... mlen - d]
    # so calculation is (repeated - mlen + d) // (mlen - d) + 1
    k = (repeated_seconds - seconds + faded_in_duration) // (seconds - faded_in_duration)
    print(k)

    for _ in range(k):
        # 淡入淡出效果
        # repeated_music from high to low,
        # overlay repeated_music[-d:] with music[0:d]
        music_one = repeated_music.fade_out(faded_out_duration)
        music_two = music.fade_in(faded_in_duration)
        music_one = music_one.overlay(music_two, position=max(len(music_one) - faded_in_duration, 0))
        repeated_music = music_one + music_two[faded_in_duration:]

    # 导出最终音频文件
    repeated_music.export(f"repeated_faded_{duration}.wav", format='wav')

if __name__ == '__main__':
    # 示例使用
    # merge_and_mix_audio(audio_folder_path, music_file, output_file)
    repeat_fade_audio_wav(music_file)
