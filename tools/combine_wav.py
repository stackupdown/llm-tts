import argparse
import wave
import os
import re
from datetime import datetime


# read the wav
def read_wav(file_path):
    with wave.open(file_path, 'rb') as wav_file:
        frames = wav_file.readframes(wav_file.getnframes())
        framerate = wav_file.getframerate()
        sampwidth = wav_file.getsampwidth()
        return frames, framerate, sampwidth

def merge_wav(input_files, interval, output_file, output_rate):
    output_frames = b''
    width = 2
    for file_path in input_files:
        frames, rate, width = read_wav(file_path)
        # Add silence for the interval
        silence = b'\x00' * int(interval * (rate // 1000 * 2))  # Assuming 16-bit samples
        output_frames += frames + silence

    # Write the merged WAV to the output file
    with wave.open(output_file, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(width)  # 16-bit samples
        wav_file.setframerate(output_rate)
        wav_file.writeframes(output_frames)

def filter_files(input_files):
    pattern = re.compile('\d+\.wav')
    res = []
    for f in input_files:
        basename = os.path.basename(f)
        if re.match(pattern, basename):
            res.append(f)
    return res

def main(args):
    # Get the list of WAV files in the input directory
    input_files = [f for f in os.listdir(args.input_dir) if f.endswith('.wav')]
    # match the format like 123.wav
    input_files = filter_files(input_files)
    # Sort the files if necessary

    input_files = sorted(input_files, key=lambda f: int(f.split('.')[0]))
    input_files = [os.path.join(args.input_dir, f) for f in input_files]
    print(input_files)
    if not input_files:
        print("no input files.")
        return

    # Get the current time
    output_file = os.path.join(args.input_dir, 'merge.wav')
    merge_wav(input_files, args.interval, output_file, 16000)  # Assuming a sample rate of 44100 Hz


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('-i', '--input_dir', type=str, required=True, help='the input directory')
    p.add_argument('-interval', type=float, required=True, help='the interval of each wav in seconds')
    args = p.parse_args()
    main(args)
