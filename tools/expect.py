import re



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
    # 如果按标点符号分割无法满足要求，那就直接按照长度n进行简单切割

str_example = "春风亭老朝手中不知有多少条像临四十七巷这样的产业，他往日交往的枭雄达官不知凡几，似这等人物若要离开长安城，需要告别的对象绝对不应该是临四十七巷里的这些店铺老板。然而今天他离开之前，却特意来到临四十七巷，与那些店铺老板们和声告别，若在帝国那些上层贵人们眼中，"
n_value = 5
result = split_string(str_example, n_value)
print(result)
