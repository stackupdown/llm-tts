import torch
import torchaudio
from einops import rearrange
from stable_audio_tools import get_pretrained_model
from stable_audio_tools.inference.generation import generate_diffusion_cond
import json
import os

# 定义文件路径
input_json_path = "output_translated.json"
output_audio_dir = "./AudioEffect"
log_file_path = "generation_log.txt"

# 检查设备
device = "cuda" if torch.cuda.is_available() else "cpu"

# 下载预训练模型
model, model_config = get_pretrained_model("stabilityai/stable-audio-open-1.0")
sample_rate = model_config["sample_rate"]
sample_size = model_config["sample_size"]
model = model.to(device)


# 裁剪音频到目标时长
def trim_to_duration(audio, sample_rate, target_duration):
    """
    裁剪音频到目标时长。
    Parameters:
    - audio: torch.Tensor, 形状为 [channels, samples]
    - sample_rate: int, 采样率
    - target_duration: float, 目标时长（秒）
    Returns:
    - 裁剪后的音频
    """
    target_samples = int(sample_rate * target_duration)
    total_samples = audio.shape[1]
    return audio[:, :target_samples] if total_samples > target_samples else audio


# 生成音效并保存
def generate_audio(prompt, duration, output_path):
    """
    根据提示词生成音效并保存。
    Parameters:
    - prompt: str, 生成音效的提示词
    - duration: float, 音效时长（秒）
    - output_path: str, 输出音频文件路径
    """
    conditioning = [{"prompt": prompt, "seconds_start": 0, "seconds_total": duration}]
    output = generate_diffusion_cond(
        model,
        steps=100,
        cfg_scale=7,
        conditioning=conditioning,
        sample_size=sample_size,
        sigma_min=0.3,
        sigma_max=500,
        sampler_type="dpmpp-3m-sde",
        device=device
    )
    output = rearrange(output, "b d n -> d (b n)")
    output = trim_to_duration(output, sample_rate, duration)
    output = output.to(torch.float32).div(torch.max(torch.abs(output))).clamp(-1, 1).mul(32767).to(torch.int16).cpu()
    torchaudio.save(output_path, output, sample_rate)


# 主函数
def main():
    # 确保输出目录存在
    os.makedirs(output_audio_dir, exist_ok=True)

    # 打开日志文件
    with open(log_file_path, "w", encoding="utf-8") as log_file:
        try:
            # 加载 JSON 文件
            with open(input_json_path, "r", encoding="utf-8") as f:
                json_data = json.load(f)

            # 遍历 JSON 数据
            for cell in json_data:
                sound = cell.get("sound")
                # audio_time_length = cell.get("audio_time_length")
                audio_time_length = 1
                audio_id = cell.get("tid")

                if sound and sound.lower() != "none":
                    # 输出文件路径
                    output_audio_path = os.path.join(output_audio_dir, f"{audio_id}.wav")

                    # 日志信息
                    log_message = f"Generating audio for ID {audio_id}: {sound} ({audio_time_length}s)\n"

                    # 写入日志并输出到控制台
                    log_file.write(log_message)
                    print(log_message.strip())  # 打印到控制台

                    # 生成音效
                    generate_audio(sound, audio_time_length, output_audio_path)

                    # 成功记录
                    print(f"Audio generated: {output_audio_path}")

        except Exception as e:
            error_message = f"Error occurred: {e}\n"
            log_file.write(error_message)
            print(error_message)


if __name__ == "__main__":
    main()
