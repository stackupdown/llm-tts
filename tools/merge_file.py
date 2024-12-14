import os
from tqdm import tqdm
import argparse
import re
import sys
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
    for oline in original_lines:
        # "<sos/eos> i4 <sos/eos>" ->
        # <speaker>|<style_prompt/emotion_prompt/content>|<phoneme>|<content>.
        line = oline.strip()
        text = re.match(pattern, line)
        if text is not None:
            speaker = text.group(1)
        else:
            # keep the previous speaker
            pass

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
        v += 1
        tag_texts.append(tag_text)
        # get emotion by prompt id
    # return chunks
    return tag_texts

def main(args):
    with open(args.f1, 'r') as f:
        original_lines = f.readlines()

    merge_text = merge_text_sound(original_lines)
    print(args.output_file)
    with open(args.output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(merge_text))

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('-f1', type=str, required=True, help='original text file', default='')
    p.add_argument('-o', '--output_file', type=str, required=True, help='the output file')
    args = p.parse_args()
    main(args)
