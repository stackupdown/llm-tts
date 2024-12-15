import os
from tqdm import tqdm
import argparse
import re
import sys
from moonshoot import mark_sentence
import json

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
    return characters.get(speaker, 0)

def get_emotion(text):
    # TODO: replace this code
    if len(text) > 10:
        return '平静'
    if len(text) >= 2 and len(text) < 5:
        return '喜悦'
    return text

from frontend import g2p_cn_en, G2p, read_lexicon

BASE_DIR = os.path.join(os.path.dirname(__file__), '..')
LINE_TOKEN_LIMIT = 150

def merge_text_sound(original_lines):
    # pattern = re.compile(r'^(?:(\w+·\w+)|(\w+))')
    # 捕获组 ?:
    pattern = re.compile(r'^(\w+(?:·\w+)?)')
    split_pattern = re.compile(r'[。！？]')
    tag_texts = []
    sid = 0
    speaker = ''
    v = 0
    chunks = []
    lexicon = read_lexicon(f"{BASE_DIR}/lexicon/librispeech-lexicon.txt")
    g2p = G2p()
    for v, oline in enumerate(original_lines):
        # "<sos/eos> i4 <sos/eos>" ->
        # <speaker>|<style_prompt/emotion_prompt/content>|<phoneme>|<content>.
        line = oline.strip()
        text = re.match(pattern, line)
        if text is not None:
            speaker = text.group(1)
        # else keep the previous speaker

        line = line[len(speaker):].strip()
        if line in '，；。':
            continue

        tmp_id = get_speaker_id(speaker)
        # if first line, then ignore
        if tmp_id != 0:
            sid = tmp_id

        print('speaker', speaker, v, tmp_id, sid)
        sound = g2p_cn_en(line, g2p, lexicon)
        tag_text = '{}|{}|{}|{}'.format(sid, get_emotion(line), sound, line)
        tag_texts.append(tag_text)
        # get emotion by prompt id
    # return chunks
    return tag_texts


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


def general_merge_text_sound(original_lines):
    tag_texts = []
    speaker = ''
    v = 0
    chunks = []
    lexicon = read_lexicon(f"{BASE_DIR}/lexicon/librispeech-lexicon.txt")
    g2p = G2p()
    tags = []
    original_lines = split_lines(original_lines)

    for v, oline in enumerate(original_lines):
        # "<sos/eos> i4 <sos/eos>" ->
        # <speaker>|<style_prompt/emotion_prompt/content>|<phoneme>|<content>.
        line = oline.strip()

        resp, success = mark_sentence(line)
        if success:
            # break or result?
            items = resp['data']
        else:
            raise Exception('moonshoot failed')
        for item in items:
            item['pinyin'] = g2p_cn_en(item['text'], g2p, lexicon)
            # TODO by WCY
            item['sound'] = None
            # TODO
            item['sid'] = get_speaker_id(item.get('C', ''))
            tag_text = '{}|{}|{}|{}'.format(item['sid'], item['E'], item['pinyin'], item['text'])
            tag_texts.append(tag_text)

        print(items)
        tags.extend(items)

    return tags, tag_texts

def main(args):
    if not os.path.exists(os.path.dirname(args.output_file)):
        os.makedirs(os.path.dirname(args.output_file))
        print('create output dir', os.path.dirname(args.output_file))

    with open(args.main_file, 'r') as f:
        original_lines = f.readlines()

    tags, merge_text = general_merge_text_sound(original_lines)
    with open(args.output_json, "w", encoding='utf-8') as f:
        json.dump(tags, f, ensure_ascii=False, indent=4)

    print(args.output_file)

    with open(args.output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(merge_text))

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--main_file', type=str, required=True, help='original text file', default='')
    p.add_argument('--output_json', type=str,help='the temp output json', default='output.json')
    p.add_argument('-o', '--output_file', type=str, required=True, help='the output file')
    args = p.parse_args()
    main(args)
