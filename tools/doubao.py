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

class DoubaoAgentClient(object):
    # API endpoint
    url = 'https://api.coze.cn/v1/conversation/create'

    def __init__(self, api_key, window_size=2):
        # Headers

        # 从环境变量中读取您的方舟API Key。
        self.url = "https://ark.cn-beijing.volces.com/api/v3"

        self.client = Ark(base_url=self.url, api_key=api_key)
        self.prompt = """
你好，我将给你多段小说的文字，请帮我做句子的标注。标注的格式是以下形式的列表：{"text": 原文句子, "E": 句子的情绪, "C": 句子的说话人，"A": 背景声音}
解释: 
1.背景声音是指自然声音，人物背景笑声，脚步声，枪声等。如果没有声音，设为"无"。
2.句子的说话人：如果是人物直接说的话，则用人物表示；否则对应"旁白"；
3.原文句子：每一个标点符号分隔开的句子，如果一个句子（由句号，问号等分割）内超过3句，就要分开成多个text；

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
        self.window_messages = []
        self.WINDOW_LENGTH = window_size
        self.messages = [
            {"role": "system", "content": "你是 Doubao AI，由 字节跳动 提供的人工智能助手，你更擅长中文的对话。你会为用户提供安全，有帮助，准确的回答。"},
            {"role": "system", "content": self.prompt}
        ]

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
        print("messages:", new_messages)

        completion = self.client.chat.completions.create(
            # 您的方舟推理接入点。
            model="ep-20241217230300-z4h68",
            messages=new_messages,
            temperature=0.8,
            response_format={"type": "json_object"}
        )

        print(completion.choices[0].message.content)
        resp = {}
        success = True
        try:
            resp = json.loads(completion.choices[0].message.content)
        except Exception as e:
            print(e)
            print(completion.choices[0].finish_reason)
            print(completion.choices[0].message.content)
            success = False

        print("resp:\n", resp)
        self.window_messages.append({
            "role": "user",
            "content": str(resp)
        })

        return resp, success



if __name__ == "__main__":
    query = """
    春风亭老朝手中不知有多少条像临四十七巷这样的产业，他往日交往的枭雄达官不知凡几，似这等人物若要离开长安城，需要告别的对象绝对不应该是临四十七巷里的这些店铺老板。
    然而今天他离开之前，却特意来到临四十七巷，与那些店铺老板们和声告别，若在帝国那些上层贵人们眼中，
    """
    agent = DoubaoAgentClient(api_key=os.environ.get('ARK_API_KEY'))
    print(agent.chat(query=query))
