import re

def d_multi_split(string, separator = "", *ignore_regexs):
    pass

def d_filter_until(strings:list[str], stop="\""):
    ready = False
    res = []
    for string in strings:
        res.append(string)
        if string.find(stop) >= 0:
            if ready or string.count(stop)%2 == 0:
                break
            ready = True
    return res

def d_find_all_calls(strings:list[str]):
    res = []
    for string in strings:
        res.extend(map(lambda x: x.strip(), re.findall(" [a-zA-Z]+[\w\.]+[a-zA-Z]+ ", string)))
    return res

def d_split(string, separator=" ", ignore_regex='"[^"]*"'):
    matches = list(re.finditer(ignore_regex, string))
    sep_found = False
    if len(matches) > 0:
        sep_found = True
    else:
        matches = [re.match(".*", string)]
    res = []
    index = 0
    for match in matches:
        res.extend(re.split(separator, string[index:match.span()[0]]))
        if sep_found:
            res.append(match[0])
        else:
            res.extend(re.split(separator, match[0]))
        index += match.span()[1]
    return (len(res) == 0 and [string]) or list(filter(lambda x: x != "", res))