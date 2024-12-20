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


"""
This function `general_merge_text_sound` processes the original text by adding a summary, sound, and speaker information. It takes two parameters: `original_text` (the text to be processed) and `file` (the file path of the original text). The function returns a tuple containing two lists: `tags` (a list of processed items) and `tag_texts` (a list of formatted tag texts).

- Summary: The function uses an agent to add a summary to the original text.
- Sound and Speaker: For each line in the original text, the function interacts with the agent to get music prompts and processes items to include sound, speaker ID, and pinyin.
- Output: Processed items are formatted into tag texts and returned along with the list of items.
"""
def general_merge_text_sound(original_text, args):
    tag_texts = []
    speaker = ''
    v = 0
    chunks = []
    lexicon = read_lexicon(f"{BASE_DIR}/lexicon/librispeech-lexicon.txt")
    g2p = G2p()

    tags = []
    # step1. add summary
    agent = get_doubao_agent()
    result, success = agent.add_preprocess(original_text)
    summary = result.get('summary', '')
    if not summary:
        logging.warning("get summary empty")
    else:
        print("summary: ", summary)


    new_text = summary + "\n" + original_text
    # save content to file
    file = args.main_file
    new_file = file[:file.rindex('.')] + ".new.txt"
    with open(new_file, 'w', encoding='utf-8') as f:
        f.write(new_text)

    original_lines = original_text.split('\n')
    original_lines = split_lines(original_lines)
    v_cnt = 0
    # step2. add sound and speaker
    for v, oline in enumerate(original_lines):
        # "<sos/eos> i4 <sos/eos>" ->
        # <speaker>|<style_prompt/emotion_prompt/content>|<phoneme>|<content>.
        line = oline.strip()
        if not line:
            continue

        v_cnt += 1
        resp, success = agent.chat(line)
        if success:
            # break or result?
            items = resp['data']
        else:
            raise Exception('moonshoot failed')

        music_prompt, success = agent.get_music(line)

        print("=" * 20 + " result " + "=" * 20, v, '\nmusic:', music_prompt)
        print(items)
        if len(items) > 0:
            emotion = items[0]['E']

        for i, item in enumerate(items):
            if i == 0:
                item['music'] = music_prompt
            else:
                item['music'] = ''

            item['pid'] = v_cnt
            item['pinyin'] = g2p_cn_en(item['text'], g2p, lexicon)
            # TODO by WCY
            item['sound'] = item['A']
            # TODO
            item['sid'] = get_speaker_id(item.get('C', ''))
            tag_id = len(tag_texts)
            tag_text = '{}|{}|{}|{}|p{}|t{}'.format(item['sid'], emotion, item['pinyin'], item['text'], v_cnt, tag_id)
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
