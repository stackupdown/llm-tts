from openai import OpenAI
import os
import json
import re

MOONSHOT_API_KEY = "sk-Ijehx0X7HEKfeVJQuBa79GWzT7VtYOCizQ6k3OSYDAKIypP6"
client = OpenAI(
    api_key=MOONSHOT_API_KEY,
    base_url="https://api.moonshot.cn/v1",
)

# 全局变量，用于存储对话的历史记录
messages = []

# 第一次对话的提示
prompt_summary = """
你好，我将给你一段文字，请帮我做文章总结。文章总结是指需要将本段剧本的情节进行简单总结。

示例:
来到老笔斋门口，朝小树看着铺内的少年与小侍女微微一笑，揖手一礼道：“宁老板，有礼了。”宁缺看着被堵死的店铺门口，还有那些围在人群外看热闹的民众，微涩一笑，也学他那样装模作样揖手还礼，和声道：“见过朝二哥。”

返回：
    朝小树在老笔斋门口与店主宁缺以及小侍女相遇，朝小树礼貌地向宁缺打招呼，两人互相问候.
"""

# 第二次对话的提示
prompt_annotation = """
你好，我将给你一段小说的文字，请帮我做句子的标注。句子标注的格式是以下形式的列表：
{"text": 原文句子, "emotion": 句子的情绪, "speaker": 句子的说话人，"speaker_id": 句子说话人的唯一标识，"pinyin": 拼音, "audio": 背景声音, "music": 音乐}
1.背景声音是指自然声音，人物笑声，脚步声，枪声等。如果没有声音，对应"无"。
2.句子的说话人：如果是人物说的话，则用人物名字表示；否则则对应"旁白"；
3.原文句子，每一个的长度适中，如果一个句子（由句号，问号等分割）内超过3句，就要分开成多个text；
4.以完整准确的json格式输出

示例:

来到老笔斋门口，朝小树看着铺内的少年与小侍女微微一笑，揖手一礼道：“宁老板，有礼了。”宁缺看着被堵死的店铺门口，还有那些围在人群外看热闹的民众，微涩一笑，也学他那样装模作样揖手还礼，和声道：“见过朝二哥。”

返回：
{
    "data": [
        {"text": "来到老笔斋门口", "emotion": "平静", "speaker": "旁白", "speaker_id": "0", "audio": "无", "pinyin": "lái dào lǎo bǐ zhāi mén kǒu", "music": "quiet"},
        {"text": "朝小树看着铺内的少年与小侍女微微一笑", "emotion": "平静", "speaker": "旁白", "speaker_id": "0", "audio": "无", "pinyin": "cháo xiǎo shù kàn zhe pù nèi de shào niáng yǔ xiǎo shì nǚ wēi wēi yī xiào", "music": "quiet"},
        {"text": "揖手一礼道", "emotion": "平静", "speaker": "旁白", "speaker_id": "0", "audio": "无", "pinyin": "yī shǒu yī lǐ dào", "music": "quiet"},
        {"text": "宁老板，有礼了", "emotion": "喜悦", "speaker": "朝小树", "speaker_id": "1", "audio": "无", "pinyin": "níng lǎo bǎn, yǒu lǐ le", "music": "happy"},
        {"text": "宁缺看着被堵死的店铺门口，还有那些围在人群外看热闹的民众，微涩一笑", "emotion": "有趣", "speaker": "旁白", "speaker_id": "0", "audio": "人群声", "pinyin": "níng quē kàn zhe bèi dǔ sǐ de dianp铺 mén kǒu, hái yǒu nà xiē wéi zài rén qún wài kàn nào nào de mín zhòng, wēi sè yī xiào", "music": "funny"},
        {"text": "也学他那样装模作样揖手还礼，和声道", "emotion": "有趣", "speaker": "旁白", "speaker_id": "0", "audio": "人群声", "pinyin": "yě xué tā yàng zhuàng mó zuò yàng yī shǒu huán lǐ, hé sháo dào", "music": "funny"},
        {"text": “见过朝二哥。”, "emotion": "有趣", "speaker": "宁缺", "speaker_id": "2", "audio": "无", "pinyin": "kàn jiù cháo èr gē.", "music": "funny"}
    ]
}
"""


def chat(query, prompt, n=20):
    global messages

    # 构造新的消息列表
    user_message = {"role": "user", "content": query}
    messages.append(user_message)

    new_messages = [{"role": "system",
                     "content": "你是 Kimi，由 Moonshot AI 提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一切涉及恐怖主义，种族歧视，黄色暴力等问题的回答。Moonshot AI 为专有名词，不可翻译成其他语言。"}]
    new_messages.append({"role": "system", "content": prompt})

    if len(messages) > n:
        messages = messages[-n:]

    new_messages.extend(messages)

    completion = client.chat.completions.create(
        model="moonshot-v1-auto",
        messages=new_messages,
        temperature=0.8,
        response_format={"type": "json_object"},
    )

    assistant_message = completion.choices[0].message
    messages.append(assistant_message)

    resp = {}
    try:
        resp = json.loads(assistant_message.content)
    except Exception as e:
        print(e)
        print(completion.choices[0].finish_reason)
        print(completion.choices[0].message.content)
    return resp


def split_text_into_chunks(text, max_chunk_size):
    # 使用正则表达式将文本按句子分割
    sentences = re.split(r'(?<=[。！？ " " “ ”])', text)
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= max_chunk_size:
            current_chunk += sentence
        else:
            chunks.append(current_chunk)
            current_chunk = sentence

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def process_file(input_file_path, summary_output_file_path, annotation_output_file_path, max_chunk_size=100):
    # 读取输入文件
    with open(input_file_path, 'r', encoding='UTF-8') as f:
        query = f.read()

    # 清空历史消息
    global messages
    messages = []

    # 第一次对话：获取总结
    summary_resp = chat(query, prompt_summary)
    summary = summary_resp.get("summary", "")
    # 将总结添加到文本开头
    full_text = f"{summary}\n{query}"
    # 分割文本为较小的块
    chunks = split_text_into_chunks(full_text, max_chunk_size)
    all_annotations = []

    for chunk in chunks:
        # 第二次对话：获取标注
        annotation_resp = chat(chunk, prompt_annotation)
        data = annotation_resp.get("data", [])
        all_annotations.extend(data)

    # 保存第一次对话结果
    with open(summary_output_file_path, 'w', encoding='UTF-8') as f:
        f.write(full_text)

    # 保存第二次对话结果
    with open(annotation_output_file_path, 'w', encoding='UTF-8') as f:
        json.dump(all_annotations, f, ensure_ascii=False, indent=4)


# 使用示例
input_file_path = "harry_porter-small.txt"
summary_output_file_path = "summary_output.txt"
annotation_output_file_path = "annotation_output.json"

process_file(input_file_path, summary_output_file_path, annotation_output_file_path)