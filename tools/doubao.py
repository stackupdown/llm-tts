# 创建推理接入点 https://www.volcengine.com/docs/82379/1099522
# ChatCompletions https://www.volcengine.com/docs/82379/1302008
from openai import OpenAI
import os

from dotenv import load_dotenv  # 用于加载环境变量
import json
import copy
import requests
load_dotenv()  # 加载 .env 文件中的环境变量

from volcenginesdkarkruntime import Ark
from volcenginesdkarkruntime._exceptions import ArkAPIError

def load_content(f):
    with open(f, 'r', encoding='utf-8') as f:
        return f.read()

class ProcessText(object):
    system_prompt = """你是 Doubao AI，由 字节跳动 提供的人工智能助手，你更擅长中文的对话。你会为用户提供安全，有帮助，准确的回答。"""
    summary_prompt = """
你好，我将给你一段文字，请帮我做文章总结。请不要用分点的格式进行总结，而是用自然交流的方式进行总结，并以 剧情梗概： 开头。
    """

    annotate_prompt = """
你好，我将给你多段小说的文字，请帮我做句子的标注。标注的格式是以下形式的列表：{"text": 原文句子, "E": 句子的情绪, "C": 句子的说话人，"A": 背景声音}
解释: 
1.背景声音是指自然声音，背景声，脚步声，枪声等，不包括单人的说话声、呼吸声。如果没有声音，设为"无"。
2.句子的说话人：如果是人物直接说的话，则用人物表示；否则对应"旁白"；
3.原文句子：每一个标点符号分隔开的完整句子，如果一个句子有多个说话人，也要分成多个text；

示例:
来到老笔斋门口，朝小树看着铺内的少年与小侍女微微一笑，揖手一礼道：“宁老板，有礼了。”宁缺看着被堵死的店铺门口，还有那些围在人群外看热闹的民众，微涩一笑，也学他那样装模装样揖手还礼，和声道：“见过朝二哥。”

返回：
{
    "data": [{"text": "来到老笔斋门口", "E": "平静", "C": "旁白"，"A": "无"},
        {"text": "朝小树看着铺内的少年与小侍女微微一笑", "E": "平静", "C": "旁白"，"A": "无"},
        {"text": "揖手一礼道", "E": "平静", "C": "旁白"，"A": "无"},
        {"text": "宁老板，有礼了", "E": "喜悦", "C": "朝小树"，"A": "无"},
        {"text": "宁缺看着被堵死的店铺门口，还有那些围在人群外看热闹的民众，微涩一笑", "E": "有趣", "C": "旁白", "A": "人群声"},
        {"text": "也学他那样装模装样揖手还礼，和声道", "E": "有趣",  "C": "旁白", "A": "人群声"},
        {"text": “见过朝二哥。”, "E": "有趣",  "C": "宁缺", "A": "无"}
    ]
}
"""

    music_prompt = """
我将给你一段小说，请根据以下的文字生成背景音乐的提示词，注意背景音乐应该跟人物情绪相关，格式是4-10个英文词形容词或名词，用逗号分隔。如果没有具体内容，请直接返回'无'。
"""

class DoubaoAgentClient(object):

    def __init__(self, api_key, window_size=3):
        # Headers

        # 从环境变量中读取您的方舟API Key。
        self.url = "https://ark.cn-beijing.volces.com/api/v3"

        self.client = Ark(base_url=self.url, api_key=api_key)
        self.prompt = ProcessText.annotate_prompt
        self.window_messages = []
        self.WINDOW_LENGTH = window_size
        self.messages = [
            {"role": "system", "content": ProcessText.system_prompt},
            {"role": "system", "content": self.prompt}
        ]

        self.summary_messages = [
            {"role": "system", "content": ProcessText.system_prompt},
            {"role": "system", "content": ProcessText.summary_prompt}
        ]
        self.music_messages = [
            {"role": "system", "content": ProcessText.system_prompt},
            {"role": "system", "content": ProcessText.music_prompt}
        ]
        self.model = "ep-20241217230300-z4h68"

    def chat(self, query):
        # https://www.volcengine.com/docs/82379/1099455
        new_messages: list = copy.deepcopy(self.messages)

        if len(self.window_messages) > self.WINDOW_LENGTH:
            self.window_messages = self.window_messages[-self.WINDOW_LENGTH:]

        new_messages.extend(self.window_messages)
        new_messages.append({
            "role": "user",
            "content": query
        })
        # print("messages:", new_messages)

        completion = self.client.chat.completions.create(
            # 您的方舟推理接入点。
            model=self.model,
            messages=new_messages,
            temperature=0.8,
            response_format={"type": "json_object"}
        )

        resp = {}
        success = True
        try:
            resp = json.loads(completion.choices[0].message.content)
        except Exception as e:
            print("fail on loads:", e)
            print(completion.choices[0].finish_reason)
            print(completion.choices[0].message.content)
            success = False

        # print("resp:\n", resp)
        self.window_messages.append({
            "role": "user",
            "content": completion.choices[0].message.content
        })

        return resp, success

    def add_preprocess(self, query):
        # reset window_messages
        new_messages: list = copy.deepcopy(self.summary_messages)

        new_messages.append({
            "role": "user",
            "content": query
        })

        resp = {}
        success = True
        try:
            completion = self.client.chat.completions.create(
                # 您的方舟推理接入点。
                model=self.model,
                messages=new_messages,
                temperature=0.8,
                response_format={"type": "json_object"}
            )
            summary = completion.choices[0].message.content
        except ArkAPIError as e:
            print("fail on create:", e)
            summary = ""
            success = False
        # reason = completion.choices[0].finish_reason
        # if reason != "stop":
        #     result = reason
        #     success = False

        return {"summary": summary}, success

    def get_music(self, query):
        new_messages: list = copy.deepcopy(self.music_messages)

        new_messages.append({
            "role": "user",
            "content": query
        })

        resp = {}
        success = True
        try:
            completion = self.client.chat.completions.create(
                # 您的方舟推理接入点。
                model=self.model,
                messages=new_messages,
                temperature=0.8,
                response_format={"type": "json_object"}
            )
        except ArkAPIError as e:
            print("fail on create:", e)
            success = False

        music_prompt = completion.choices[0].message.content
        return music_prompt, success

    def get_completion(self, messages):
        return self.client.chat.completions.create(
                # 您的方舟推理接入点。
                model=self.model,
                messages=messages,
                temperature=0.8,
                response_format={"type": "json_object"}
        )

    def init_all_speakers(self, file):
        article = load_content(file)

        prompt = """请直接列出这篇文章中，所有在里面说过话的人物的全名，用逗号分隔。不要加多余的解释或括号。"""

        messages = [
            {"role": "system", "content": ProcessText.system_prompt},
            {"role": "user", "content": prompt + "\n" + article},
        ]
        speakers = []
        success = True
        try:
            completion = self.get_completion(messages)
        except ArkAPIError as e:
            print("fail on create:", e)
            success = False
            return [], success

        print(completion.choices[0].message.content)
        speakers = completion.choices[0].message.content
        # TODO
#         speakers = """哈利·波特，罗恩·威斯里，荷米恩·格林佐，尼维尔·兰博顿，马尔夫，克来伯，高尔，哈格力，麦康娜教授，
# 费艾尔，伯希·威斯里，艾伯斯·丹伯多，屈拉教授，莉沙·特萍，布雷斯·扎毕尼，谢默斯·范尼更，尼古拉斯·德·米姆西·波平顿爵士，吸血鬼巴伦，史纳皮教授，费驰先生，胡施女士，皮维斯"""
        speakers = "麦格教授，海格，汉娜・艾博，苏珊・彭斯，泰瑞・布特，曼蒂・布洛贺，拉文德・布朗，米里森・伯斯德，贾斯廷・芬列里，赫敏・格兰杰，纳威・隆巴顿，马尔福，克拉布，高尔，莫恩，诺特，帕金森，佩蒂尔孪生姐妹，莎莉安・波克斯，哈利・波特，阿不思・邓布利多，珀西・韦斯莱，韦斯莱家的孪生兄弟，敏西－波平顿的尼古拉斯爵士，西莫・斐尼甘，阿尔吉伯父，艾妮伯母，奇洛教授，斯内普教授，费尔奇先生，霍琦夫人，皮皮鬼，血人巴罗，胖修士幽灵，穿轮状皱领紧身衣的幽灵，达力，佩妮姨妈，弗农姨父，莉莎・杜平，布雷司・沙比尼，罗恩・韦斯莱，德思礼先生，德思礼太太"
        self.prompt += """\n另外，由于文章中人物众多，为了避免你标注错误，请仅在我给定的人物范围内进行说话人标注：{}""".format(speakers)

        speakers = [s.strip() for s in speakers.split('，')]
        self.messages = [
            {"role": "system", "content": ProcessText.system_prompt},
            {"role": "system", "content": self.prompt}
        ]
        return speakers, success

    def fill_default_items(self, items):
        for _, item in enumerate(items):
            item['C'] = '旁白'
            item['E'] = '平静'
            item['A'] = ''
        return items

def get_doubao_agent():
    return DoubaoAgentClient(api_key=os.environ.get('ARK_API_KEY'))

class DoubaoTTSAgent(object):
    def __init__(self):
        self.url = ''
        self.client = None
    def text_to_speech(self, speaker_id, text):
        content = ''
        return content

def get_tts_agent():
    # 每10k token 4.5元;
    return DoubaoAgentClient(api_key=os.environ.get('ARK_API_KEY'))


if __name__ == "__main__":
    query = """
    春风亭老朝手中不知有多少条像临四十七巷这样的产业，他往日交往的枭雄达官不知凡几，似这等人物若要离开长安城，需要告别的对象绝对不应该是临四十七巷里的这些店铺老板。
    然而今天他离开之前，却特意来到临四十七巷，与那些店铺老板们和声告别，若在帝国那些上层贵人们眼中，
    """
    agent = DoubaoAgentClient(api_key=os.environ.get('ARK_API_KEY'))
    # print(agent.add_preprocess(query=query))
    # 大文本;
    agent.init_all_speakers("harry_porter.txt")
