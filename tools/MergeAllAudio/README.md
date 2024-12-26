<!-- # 准备
需要在电脑中装载ffmpeg，并将"./ffmpeg/bin"导入到Path中
生成的人声音频放入"./audio" 文件夹下
命名标号为audio_id
生成的背景音乐放在"./music" 文件夹下
命名标号为pid
主文件夹"."还需要放入output.json文件


# Add_time_length.py代码说明
这个代码会解析output.json文件，额外加入关键词audio_id、audio_time_length
audio_id是人声音频对应标号，audio_time_length是每条人声音频长度
最后导出output_AddID.json文件放入主文件夹中

# Merge_BGM.py代码说明
这个代码可以将人声和背景音乐合成在一起
首先先将人声音频以0.5s为间隔生成合成音频combined_output.wav
然后由解析output_AddID.json文件，将music中的pid标号与audio_id匹配，计算背景音乐延时，导出的audio_id_mapping.txt和music_timeline.txt可查看中间计算过程
最后根据该延时将背景音乐与combined_output.wav音频进行混音，归一化控制音频音量大小，导出最终音频final_audio.wav

# 文件格式
生成output.json文件; 
music = output.id.json
audio = music -->

ffmpeg: 
~~~shell
sudo apt install ffmpeg
# 安装ffmpeg-python
pip install -r requirements.txt
~~~

#### 步骤
1.执行完merge_file.py后，生成output.json和harry_porter_merge.txt文件

2.
执行music_gen.py，读取output.json并生成对应的music文件到data/music下面；

执行start_inference_hamlet.sh, 读取harry_porter_merge.txt生成对应的audio文件；

3.
~~~shell
python step3_update_time_and_combine_output.py

~~~

执行上述文件，会读取output.json和audio,music文件，生成最后的合并文件merge_output.wav文件。

生成音乐必须大于2s;
