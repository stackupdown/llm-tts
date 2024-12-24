import os
import json
import subprocess
import re  # 添加此行
# 文件夹路径
input_folder = r".\audio"
output_folder = r"."
output_file = os.path.join(output_folder, "merge_character_v1.wav")
silence_file = os.path.join(output_folder, "silence.wav")
music_dir = r'./music'
combined_output = 'combined_output.wav'
final_output = 'final_audio.wav'
json_file = 'output_AddID.json'

# 创建 0.5 秒静音文件
def create_silence():
    cmd = [
        "ffmpeg",
        "-f", "lavfi",
        "-i", "anullsrc=r=16000:cl=mono",
        "-ar", "16000",
        "-ac", "1",
        "-t", "0.5",
        silence_file
    ]
    subprocess.run(cmd, check=True)

# 自定义排序函数：按文件名中的数字排序
def natural_sort(file_name):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', file_name)]

# 批量转换音频格式
def convert_audio(input_folder):
    wav_files = [f for f in os.listdir(input_folder) if f.endswith(".wav")]
    for wav_file in wav_files:
        input_path = os.path.join(input_folder, wav_file)
        temp_path = os.path.join(input_folder, f"converted_{wav_file}")
        cmd = [
            "ffmpeg",
            "-i", input_path,
            "-ar", "16000",
            "-ac", "1",
            temp_path
        ]
        subprocess.run(cmd, check=True)
        os.replace(temp_path, input_path)  # 替换原文件

# 生成 FFmpeg concat 文件列表
def generate_file_list(input_folder, silence_file, file_list_path):
    wav_files = sorted([f for f in os.listdir(input_folder) if f.endswith(".wav")], key=natural_sort)
    with open(file_list_path, "w") as file:
        for wav_file in wav_files:
            file.write(f"file '{os.path.join(input_folder, wav_file)}'\n")
            file.write(f"file '{silence_file}'\n")

# 合并音频文件
def merge_audio(file_list_path, output_file):
    cmd = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", file_list_path,
        "-ar", "16000",
        "-ac", "1",
        "-c:a", "pcm_s16le",
        output_file
    ]
    subprocess.run(cmd, check=True)

# 合并音频文件的主函数
def merge_audio_files(input_folder, output_file):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 转换音频
    convert_audio(input_folder)

    # 创建静音文件
    create_silence()

    # 生成文件列表
    file_list_path = os.path.join(output_folder, "file_list.txt")
    generate_file_list(input_folder, silence_file, file_list_path)

    # 合并音频
    merge_audio(file_list_path, output_file)

    # 清理临时文件
    os.remove(silence_file)
    os.remove(file_list_path)
    print(f"合并完成，输出文件位于：{output_file}")
# 步骤 2：计算背景音乐时间轴
def calculate_music_timeline(data, music_dir):
    music_timeline = []
    for item in data:
        pid = item['pid']
        audio_id = item['audio_id']

        # 计算当前音频的开始时间（包括之前的总时长和时延，但不包括当前音频）
        audio_start_time = sum([d['audio_time_length'] + 0.5 for d in data if int(d['audio_id']) < int(audio_id)])

        # 确认音乐文件路径
        music_path = os.path.join(music_dir, f"{pid}.wav")

        # 避免重复添加背景音乐
        if os.path.exists(music_path) and pid not in [m['pid'] for m in music_timeline]:
            music_timeline.append({
                'pid': pid,
                'audio_id': audio_id,  # 保存 audio_id
                'audio_start_time': audio_start_time,
                'music_path': music_path
            })
    return music_timeline

# 将 music_timeline 写入到文件中，并记录每个 music 对应的 audio_id
def save_music_timeline_to_file(music_timeline, output_file, audio_id_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        for music in music_timeline:
            f.write(f"PID: {music['pid']}, Start Time: {music['audio_start_time']}, Path: {music['music_path']}\n")

    # 记录每个 music 对应的 audio_id 和计算过程
    with open(audio_id_file, 'w', encoding='utf-8') as f:
        for music in music_timeline:
            f.write(f"PID: {music['pid']} -> Audio ID: {music['audio_id']}\n")
            f.write(f"Calculation for {music['pid']} (audio_id {music['audio_id']}):\n")
            f.write(f"Start Time Calculation: ")
            # 记录计算过程
            calc_process = [f"audio_time_length of audio {d['audio_id']} = {d['audio_time_length']} + 0.5s" for d in data if int(d['audio_id']) < int(music['audio_id'])]
            f.write(" + ".join(calc_process) + f" = {music['audio_start_time']}s\n\n")

# 步骤 3：合成 final_audio.wav
def add_music_to_existing_audio(base_audio, music_timeline, output_file):
    # 获取基准音频的时长
    audio_info = subprocess.run(
        ['ffprobe', '-i', base_audio, '-show_entries', 'format=duration', '-v', 'quiet', '-of', 'csv=p=0'],
        capture_output=True, text=True)
    total_duration = float(audio_info.stdout.strip())

    # 构建 FFmpeg 命令
    overlay_cmd = ['ffmpeg', '-i', base_audio]
    filter_complex = []

    # 添加基准音频流标签，并设置音量为1.0
    filter_complex.append(f"[0:a]volume=1.0[a0];")

    # 为每个音乐文件添加延迟和处理
    for idx, music in enumerate(music_timeline):
        music_start = music['audio_start_time']
        music_file = music['music_path']
        overlay_cmd += ['-i', music_file]

        # 音乐延时加入，并截断至基准音频长度，同时降低音乐音量
        filter_complex.append(
            f"[{idx + 1}:a]adelay={int(music_start * 1000)}|{int(music_start * 1000)},atrim=duration={total_duration - music_start},volume=0.3[a{idx + 1}];"
        )

    # 混合所有音频流，使用normalize=0参数以避免音量缩小
    audio_mix = ''.join(f"[a{idx}]" for idx in range(len(music_timeline) + 1)) + f"amix=inputs={len(music_timeline) + 1}:duration=longest:normalize=0[out]"
    filter_complex.append(audio_mix)

    # 完整的 FFmpeg 命令
    overlay_cmd += ['-filter_complex', ''.join(filter_complex), '-map', '[out]', '-y', output_file]

    # 运行 FFmpeg，捕获输出和错误信息
    result = subprocess.run(overlay_cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"FFmpeg error: {result.stderr}")
    else:
        print(f"Audio file successfully saved to {output_file}")

# 主函数
if __name__ == "__main__":
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Step 1: Merge audio files
    merge_audio_files(input_folder, combined_output)

    # Step 2: Calculate music timeline
    music_timeline = calculate_music_timeline(data, music_dir)

    # Save music timeline and audio ID mapping
    save_music_timeline_to_file(music_timeline, 'music_timeline.txt', 'audio_id_mapping.txt')

    # Step 3: Add music to merged audio
    add_music_to_existing_audio(combined_output, music_timeline, final_output)


