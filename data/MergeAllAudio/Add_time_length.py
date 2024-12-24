import json
import os
from pydub.utils import mediainfo

# 定义文件路径
input_json_path = "output.json"
audio_folder_path = "./audio/g_00140000"
output_json_path = "output_AddID.json"


# 加载 JSON 文件
def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


# 保存 JSON 文件
def save_json(data, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# 获取音频文件时长
def get_audio_length(audio_path):
    info = mediainfo(audio_path)
    return float(info["duration"])


# 更新 JSON 数据
def update_json_with_audio_info(json_data, audio_folder):
    audio_files = sorted(os.listdir(audio_folder), key=lambda x: int(os.path.splitext(x)[0]))

    for idx, cell in enumerate(json_data):
        audio_file = audio_files[idx]
        audio_path = os.path.join(audio_folder, audio_file)

        audio_id = os.path.splitext(audio_file)[0]
        audio_time_length = get_audio_length(audio_path)

        cell["audio_id"] = audio_id
        cell["audio_time_length"] = audio_time_length

    return json_data


# 主函数
def main():
    # 加载 JSON 数据
    json_data = load_json(input_json_path)

    # 更新 JSON 数据
    updated_data = update_json_with_audio_info(json_data, audio_folder_path)

    # 保存更新后的 JSON 数据
    save_json(updated_data, output_json_path)
    print(f"更新完成，结果已保存到 {output_json_path}")


if __name__ == "__main__":
    main()
