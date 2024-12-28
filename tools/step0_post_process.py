# post_process.py
import json

def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

data = load_json('./output.json')
mp = {}
emotions = []
emotion = ''
tag_texts = []
pid_map = {}
def update_character(item):
    if '罗恩' in item['C']:
        item['C'] = '罗恩·韦斯莱'
        # item['sid'] = 1028
        item['sid'] = 3796
    if item['C'] == '哈利・波特' or '哈利' in item['C']:
        item['sid'] = 1028
        item['C'] = '哈利·波特'
    if '邓布利多' in item['C']:
        # item['sid'] = 3571 稍粗犷
        item['sid'] = 6713
        item['C'] = '阿布思·邓布利多'
    if '赫敏' in item['C']:
        item['sid'] = 6627
        item['C'] = '赫敏·格兰杰'
    if '珀西' in item['C']:
        item['sid'] = 1018
        item['C'] = '珀西·韦斯莱'
    return

for idx, item in enumerate(data):
    sid = item['sid']
    if sid not in mp:
        mp[item['C']] = sid
    else:
        assert mp[item['C']] == sid, 'found {} new sid {}'.format(item['C'], sid)
    pid = item['pid']
    if pid not in pid_map:
        pid_map[item['pid']] = item['E']
    else:
        item['E'] = pid_map[pid]
    item["tid"] = idx + 1
    tag_id = len(tag_texts) + 1
    tag_text = '{}|{}|{}|{}|p{}|t{}'.format(item['sid'], pid_map[pid], item['pinyin'], item['text'], item['pid'], tag_id)
    tag_texts.append(tag_text)

print(mp)

def save_json(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def save_txt(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(data))

save_json('./output.json', data)
# save_txt('./harry_porter_merge.txt', tag_texts)
