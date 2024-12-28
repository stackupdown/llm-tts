# -*- coding: utf-8 -*-
import json
import os
from pydub.utils import mediainfo
import logging

BASE_DATA_PATH = "../data/"
BASE_OUTPUT_PATH = "./"
# TODO: harry should be changed
audio_folder_path = os.path.join(BASE_OUTPUT_PATH, "harry/audio/")
music_folder_path = os.path.join(BASE_OUTPUT_PATH, "harry/music/")
output_audio_file = 'merge_output.wav'
input_json_path = "output.json"
output_json_path = "output_addid.json"
MILLI_PER_SEC = 1000

def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(data, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

from pydub import AudioSegment

def fade_in_out_merge(source, other, duration, max_length):
    # source and other overlap duration
    assert len(source) <= max_length, 'source is too long {}:{}'.format(len(source), max_length)
    assert len(source) > duration, 'source is too short {}:{}'.format(len(source), duration)
    if len(source) == max_length:
        return source
    assert len(other) > duration

    # fill until max_length
    # if len_other > source, concat[source, len_other] should be [source, other[:duration]]
    if len(source) + len(other) - duration > max_length:
        other = other[:max_length + duration - len(source)]

    k = (max_length - len(source)) // (len(other) - duration)
    for _ in range(k):
        music_one = source.fade_out(duration)
        music_one = music_one.overlay(other.fade_in(duration), position=len(music_one) - duration)
        source = music_one + other[duration:]

    # the left
    left = max_length - len(source)
    if left > 0:
        music_one = source.fade_out(left)
        music_one = music_one.overlay(other.fade_in(left), position=len(music_one) - left)
        source = music_one + other[:left]
    return source

def merge_all_music_and_audio():
    # music_prompt, repeat 1, time, overlay_type
    # add first music

    head_music_path = os.path.join(music_folder_path, "1.wav")
    if not os.path.exists(head_music_path):
        head_music_path = os.path.join(BASE_DATA_PATH, "music_demo/default1.wav")

    empty_duration = 0.5
    head_music = AudioSegment.from_file(head_music_path)
    silent = AudioSegment.silent(empty_duration * 1000)
    music_buffer = [head_music]

    result_music_audio = head_music
    result_speak_audio = AudioSegment.silent(len(head_music))

    # result audio
    items = load_json(output_json_path)
    for idx, item in enumerate(items):
        audio_path = os.path.join(audio_folder_path, f"{idx + 1}.wav")
        if not os.path.exists(audio_path):
            print(audio_path)
            raise Exception("not found {}".format(audio_path))
        audio = AudioSegment.from_file(audio_path)
        print("length ", len(audio), len(result_music_audio), len(result_speak_audio))

        if item['play_music']:
            music_path = os.path.join(music_folder_path, f"{item['pid']}.wav")
            music = AudioSegment.from_file(music_path)
            music_buffer.append(music)
            if item['insert_type'] == 'overlay':
                result_speak_audio += silent + audio
            elif item['insert_type'] == 'insert':
                # music -> audio
                result_speak_audio += AudioSegment.silent(len(music)) + silent + audio
        else:
            result_speak_audio += silent + audio

        music = music_buffer[-1]
        print("  length ", len(audio), len(result_music_audio), len(result_speak_audio), len(music))
        result_music_audio = fade_in_out_merge(result_music_audio, music, 1000, len(result_speak_audio))
        # audio_time_length = item["audio_time_length"] * MILLI_PER_SEC
    result_music_audio -= 18
    result_music_audio.export("merge_music.wav", format="mp3", bitrate="32k")
    result_speak_audio.export("merge_speaker.wav", format="mp3", bitrate="32k")
    result_music_audio = result_speak_audio.overlay(result_music_audio, position=0)
    result_music_audio.set_frame_rate(22050)

    # samples = np.array(result_music_audio.get_array_of_samples())
    # plt.figure(figsize=(14, 5))
    # plt.plot(samples)
    # plt.title("Repeated Music Waveform")
    # plt.xlabel("Sample")
    # plt.ylabel("Amplitude")
    # plt.show()
    # result_music_audio.export(output_audio_file, format='wav')
    result_music_audio.export("merge_output.wav", format="mp3", bitrate="32k")
    return result_music_audio


if __name__ == "__main__":
    # update_json_with_audio_info(input_json_path, audio_folder_path)
    merge_all_music_and_audio()
    # Step2. generate json file
    # input is json file and wav file
    # music_prompt, repeat 1, time, overlay_type
    # output updated.json
    # repeat the music and write to music demo
    # merge the audio and output to harry_merge.wav
