from demo_page import get_models, tts
from frontend import g2p_cn_en, ROOT_DIR, read_lexicon, G2p
from config.joint.config import Config
import pyrubberband as pyrb
import simpleaudio as sa
import numpy as np

config = Config()
speakers = config.speakers
models = get_models()
lexicon = read_lexicon(f"{ROOT_DIR}/lexicon/librispeech-lexicon.txt")
g2p = G2p()

content = "hello"
text =  g2p_cn_en(content, g2p, lexicon)
path = tts(text, "开心", content, "8051", models)
# 转为0.75倍速
new_data = pyrb.time_stretch(path, 16_000, 0.75)
if new_data.dtype != np.int16:
    new_data = (new_data * 32768).astype(np.int16)
play_obj = sa.play_buffer(new_data, 1, 2, 16_000)
#play_obj.wait_done()
