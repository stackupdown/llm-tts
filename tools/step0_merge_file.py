import os
from tqdm import tqdm
import argparse
import re
import sys
import logging
from doubao import get_doubao_agent
import json
log_format = '%(asctime)s-[%(levelname)s]: %(message)s'
formatter = logging.Formatter(log_format)
sys.path.append('..')
# accept the first argument as 
# read the first file
# read the second file
import logging

# 基本配置，设置日志级别为 DEBUG，并将日志输出到标准输出

# 创建一个logger对象
logger = logging.getLogger(__name__)

logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
# 将处理器添加到logger
logger.addHandler(console_handler)

def get_speaker_id(speaker):
    characters = {
        '国王': 1374,
        '王后': 1012,
        '哈姆莱特': 1028,
        '波洛涅斯': 1341,
        '吉尔登斯吞': 100,
        '伶甲': 133,
        '罗森·格兰兹': 1018,
        # '罗森': 1160
        # 9136
    }
    return characters.get(speaker, 1028)

class SelectSpeaker(object):
    females = [
        # (6627, 'young'),
        (1012, 'mid'),
        (6620, 'young'),
        (9136, 'mid'),
        (1171, 'mid'),
        (6689, 'young'),
        (6637, 'old'),
        (6695, 'mid'),
        (26, 'mid'),
    ]
    males = [
        # (1028, 'boy', 8),
        (6625, 'boy', 7),
        (3340, 'young', 7),
        (26, 'mid'),
        (7097, 'mid', 7),
        (6097, 'mid'),
        # (6713, 'old'),
        (1341, 'mid'), # 滑稽
        # '波洛涅斯': 1341,
    ]

    story_teller = 1018

    def __init__(self):
        self.main_roles = {}
        self.female_idx = 0
        self.male_idx = 0
        self.characters = {
            '哈利·波特': 1028,
            '邓布利多': 6713,
            '阿不思·邓布利多': 6713,
            '麦格教授': 1012,
            '罗恩・韦斯莱': 3796,
            '罗恩·韦斯莱': 3796,
            '赫敏・格兰杰': 6627,
            '赫敏·格兰杰': 6627,
            '分院帽': 1341,
            '旁白': self.story_teller
        }

    def get_speaker_id(self, speaker, gender='M'):
        if self.characters.get(speaker):
            return self.characters[speaker]
        if gender == 'F':
            self.female_idx += 1
            if self.female_idx > len(self.females):
                return self.story_teller
            # update current map to record
            self.characters[speaker] = self.females[self.female_idx - 1][0]
            return self.characters[speaker]
        else:
            self.male_idx += 1
            if self.male_idx > len(self.males):
                return self.story_teller
            self.characters[speaker] = self.males[self.male_idx - 1][0]
            return self.characters[speaker]


def get_emotion(text):
    # TODO: replace this code
    if len(text) > 10:
        return '平静'
    if len(text) >= 2 and len(text) < 5:
        return '喜悦'
    return text

from frontend import g2p_cn_en, G2p, read_lexicon

BASE_DIR = os.path.join(os.path.dirname(__file__), '..')
LINE_TOKEN_LIMIT = 500

def split_string(s: str, n: int):
    punctuations = ",.;?!。，；;"
    punc_indexes = []
    for i, c in enumerate(s):
        if c in punctuations:
            punc_indexes.append(i)

    if len(punc_indexes) == 0:
        parts = s[:-1:n]
        return parts

    # punc_indexes may be [0, 10, len - 1]
    prev = 0
    j = 0
    length = len(punc_indexes)
    parts = []
    while j < length:
        if prev == punc_indexes[j]:
            j += 1
            continue

        while j < length and punc_indexes[j] - prev + 1 <= n:
            j += 1

        # if punc[j] - prev > n, like 16 - 0 = 16, then
        if j < length:
            if len(s) == punc_indexes[j] + 1:
                j += 1
                continue
            parts.append(s[prev:punc_indexes[j] + 1])
            prev = punc_indexes[j] + 1
        else:
            parts.append(s[prev:])
    return parts

"""
Splits lines of text into smaller chunks based on a specified token limit.

This function processes each line from the input list, `original_lines`, and checks if its length
exceeds `LINE_TOKEN_LIMIT`. If it does, the line is split into multiple smaller lines using the
`split_string` function. Otherwise, the line is added to the output list as is.

Args:
    original_lines (list of str): The list of original lines to be processed.

Returns:
    list of str: A list of lines, potentially split into smaller chunks to fit within the token limit.
"""
def split_lines(original_lines):
    new_lines = []
    for v, oline in enumerate(original_lines):
        # "<sos/eos> i4 <sos/eos>" ->
        # <speaker>|<style_prompt/emotion_prompt/content>|<phoneme>|<content>.
        line = oline.strip()
        if not line:
            continue
        if len(line) > LINE_TOKEN_LIMIT:
            new_lines.extend(split_string(line, LINE_TOKEN_LIMIT))
        else:
            new_lines.append(line)
    return new_lines

def save_file(file, new_text):
    new_file = file[:file.rindex('.')] + ".new.txt"
    with open(new_file, 'w', encoding='utf-8') as f:
        f.write(new_text)
"""
This function `general_merge_text_sound` processes the original text by adding a summary, sound, and speaker information. It takes two parameters: `original_text` (the text to be processed) and `file` (the file path of the original text). The function returns a tuple containing two lists: `tags` (a list of processed items) and `tag_texts` (a list of formatted tag texts).

- Summary: The function uses an agent to add a summary to the original text.
- Sound and Speaker: For each line in the original text, the function interacts with the agent to get music prompts and processes items to include sound, speaker ID, and pinyin.
- Output: Processed items are formatted into tag texts and returned along with the list of items.
"""
def general_merge_text_sound(original_text, args):
    tag_texts = []
    v = 0
    lexicon = read_lexicon(f"{BASE_DIR}/lexicon/librispeech-lexicon.txt")
    g2p = G2p()

    tags = []
    # step0. speaker
    agent = get_doubao_agent()
    speaker_helper = SelectSpeaker()
    all_speakers = agent.init_all_speakers(args.main_file)

    # step1. add summary
    result, success = agent.add_preprocess(original_text)
    summary = result.get('summary', '')
    if not summary:
        logger.warning("get summary empty")
    else:
        logger.info("summary: {}".format(summary))

    new_text = summary + "\n\n" + original_text
    save_file(args.main_file, new_text)

    original_lines = original_text.split('\n')
    summary_lines = [o for o in split_lines([summary]) if o.strip()]
    original_lines = [o for o in split_lines(original_lines) if o.strip()]
    v_cnt = 0

    # step2. add sound and speaker
    for v, oline in enumerate(summary_lines + original_lines):
        # "<sos/eos> i4 <sos/eos>" ->
        # <speaker>|<style_prompt/emotion_prompt/content>|<phoneme>|<content>.
        line = oline.strip()
        assert line, 'line must be non empty'
        print("===> ", line)
        resp, success = agent.chat(line)
        if success:
            items = resp['data']
        else:
            raise Exception('query failed')

        if v < len(summary_lines):
            items = agent.fill_default_items(items)

        # add music
        music_prompt, success = agent.get_music(line)
        print("=" * 20 + " result " + "=" * 20, v, '\nmusic:', music_prompt)
        print(items)

        for i, item in enumerate(items):
            if i == 0:
                item['music'] = music_prompt
                # TODO: another logic
                item['insert_type'] = 'overlay' if music_prompt else ''
            else:
                item['music'] = ''

            item['E'] = items[0]['E']
            item['pid'] = v + 1
            item['pinyin'] = g2p_cn_en(item['text'], g2p, lexicon)
            item['sound'] = item['A']
            item['sid'] = speaker_helper.get_speaker_id(item.get('C', ''))
            tag_id = len(tag_texts) + 1
            item['tid'] = tag_id
            tag_text = '{}|{}|{}|{}|p{}|t{}'.format(item['sid'], items[0]['E'], item['pinyin'], item['text'], v_cnt, tag_id)
            tag_texts.append(tag_text)

        tags.extend(items)

    return tags, tag_texts

def process_error_pinyin(content):
    import thulac
    thu1 = thulac.thulac()
    text = thu1.cut(content, text=False)  #进行一句话分词
    text_list = []
    for o in text:
        if o[0] == '地' and o[1] == 'u':
            o[0] = '的'
        text_list.append(o[0])
    return ''.join(text_list)

def main(args):
    if not os.path.exists(os.path.dirname(args.output_file)):
        os.makedirs(os.path.dirname(args.output_file))
        print('create output dir', os.path.dirname(args.output_file))

    with open(args.main_file, 'r') as f:
        original_text = f.read()

    original_text = process_error_pinyin(original_text)
    tags, merge_text = general_merge_text_sound(original_text, args)
    with open(args.output_json, "w", encoding='utf-8') as f:
        json.dump(tags, f, ensure_ascii=False, indent=4)

    print(args.output_file)

    with open(args.output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(merge_text))

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--main_file', type=str, required=True, help='original text file', default='')
    p.add_argument('--output_json', type=str, help='the temp output json', default='output.json')
    p.add_argument('-o', '--output_file', type=str, required=True, help='the output file')
    args = p.parse_args()
    main(args)
