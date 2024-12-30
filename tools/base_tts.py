
#coding=utf-8
# https://console.volcengine.com/speech/service/8
# https://www.volcengine.com/docs/6561/79820
'''
requires Python 3.6 or later
pip install requests
'''
import base64
import json
import uuid
import requests

# 填写平台申请的appid, access_token以及cluster
voice_types = [
    'BV700_V2_streaming',     # 灿灿 2.0
    "BV705_streaming",      # 炀炀
    "BV701_V2_streaming",   # 擎苍 2.0
    "BV001_V2_streaming",   # 通用女声 2.0
    "BV700_streaming",      # 灿灿
    "BV406_V2_streaming",   # 超自然音色-梓梓2.0
    "BV406_streaming",      # 超自然音色-梓梓
    "BV407_V2_streaming",   # 超自然音色-燃燃2.0
    "BV407_streaming",      # 超自然音色-燃燃
    "BV001_streaming",      # 通用女声
    # "BV002_streaming",      # 通用男声
    "BV701_streaming",      # 擎苍 (AI味)
    "BV123_streaming",      # 阳光青年
    "BV120_streaming",      # 反卷青年 (懒洋洋)
    "BV119_streaming",      # 通用赘婿 (老练沉稳)
    "BV115_streaming",      # 古风少御
    "BV107_streaming",      # 霸气青叔
    "BV100_streaming",      # 质朴青年
    "BV104_streaming",      # 温柔淑女
    "BV004_streaming",      # 开朗青年
    "BV113_streaming",      # 甜宠少御
    "BV102_streaming",      # 儒雅青年
    'BV426_streaming',  # 懒小羊
    'BV428_streaming',  # 清新文艺女声
    'BV403_streaming',  # 鸡汤女声
    'BV158_streaming',  # 智慧老者
    'BV157_streaming',  # 慈爱姥姥
    'BV410_streaming',  # 活力解说男
    'BV411_streaming',  # 影视解说小帅
    'BV227_streaming',  # 台普男声,
    # 'BV213_streaming',  # 广西
    'BV002_24k_streaming', 
    'BV056',            # 阳光男声
    'BV021',            # 东北老铁
    'BV006_streaming',  # 磁性配音
]

appid = "2449278375"
atk = "Py-HCJ1xPU5B5vzyCTV0imILHDPHIo0w"
cluster = "volcano_tts"
host = "openspeech.bytedance.com"
api_url = f"https://{host}/api/v1/tts"

header = {"Authorization": f"Bearer;{atk}"}

request_json = {
    "app": {
        "appid": appid,
        "token": "access_token",
        "cluster": cluster
    },
    "user": {
        "uid": "123456789"
    },
    "audio": {
        "voice_type": "BV411_streaming",
        "encoding": "wav",
        "speed_ratio": 1.0,
        "emotion": "scared",
        "volume_ratio": 1.0,
        "pitch_ratio": 1.0,
    },
    "request": {
        "reqid": str(uuid.uuid4()),
        "text": "麦康娜教授，一年级新生都在这儿了。",
        "text_type": "plain",
        "operation": "query",
        "with_frontend": 1,
        "frontend_type": "unitTson"
    }
}

import copy
import tqdm

def tts_all_voice():
    copy_request = copy.deepcopy(request_json)
    texts = [
        # '麦康娜教授，一年级新生都在这儿了。',
        '谢谢你，哈格力，我会带他们进去的。',
        """你们也许觉得我不算漂亮，但千万不要以貌取人，如果你们能找到比我更漂亮的帽子，我可以把自己吃掉。"""
    ]

    resp = None
    text = texts[1]
    voice_type = voice_types[-1]
    copy_request["request"]["text"] = text
    copy_request["audio"]["voice_type"] = voice_type
    resp = requests.post(api_url, json.dumps(copy_request), headers=header)

    if "data" in resp.json():
        data = resp.json()["data"]
        with open("test_{}_{}.mp3".format(voice_type, 0), "wb") as file_to_save:
            file_to_save.write(base64.b64decode(data))
    else:
        print("error:", resp.json())

if __name__ == '__main__':
    tts_all_voice()
