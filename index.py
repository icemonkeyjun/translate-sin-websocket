# -*- coding: utf-8 -*-

from Hangulpy import *
from Homonyms import *
from konlpy.tag import Okt
import Options

okt = Okt()  # 품사 태깅
okt.pos('금수저가 금수저로 밥을 먹는다.')

def get_tokens(inp):
    while inp[0] == ' ':
        inp = ''.join(list(inp)[1:])
    tokens = okt.pos(inp, norm=True)
    text = inp
    poses = []
    Pos = []
    for tk in tokens:
        Pos.append(tk)
        text = ''.join(list(text)[len(tk[0]):])
        try:
            if text[0] == ' ':
                poses.append(Pos)
                Pos = []
                text = ''.join(list(text)[1:])
        except:
            break
    poses.append(Pos)
    return tokens, poses


def get_db():
    with open(Options.DB_PATH, 'r') as f:
        dbStr = f.read()

    with open(Options.EXPLAIN_PATH) as f:
        explainStr = f.read()
    with open(Options.AUTO_EXPLAIN_PATH, encoding='utf8') as f:
        autoexplain_db = {i.split(' : ')[0]: i.split(' : ')[1].replace('[ENTER]', '') for i in f.read().split('\n')}

    explain_db = {}
    for i in explainStr.split('\n'):  # 신조어 설명 db 전처리
        explain_db[i.split(' : ')[0].replace('()', "<pos[0][1]==Josa and len(pos)==1>")] = i.split(' : ')[1].replace(
            '@', '\n')
    dbStr = dbStr.split('\n')
    db = []
    els = []  # 문장 토큰화 하기 전에 db에 있는 단어들이 그 문장 안에 포함되어 있는지 확인하기 위한 db에 있는 단어들 목록
    for n, i in enumerate(dbStr):
        # ex: "[pos[0][1]=='Noun' and len(pos)==1]각()" : '인것 같'      '가즈아' : '가자'

        i = i.replace('()', "<pos[0][1]==Josa and len(pos)==1>")
        condition = i.split(' : ')[0].replace('"', '').replace("'",
                                                               '')  # "[pos[0][1]=='Noun' and len(pos)==1]각()"        '가즈아'
        original_text = condition
        purpose = i.split(' : ')[1].replace('"', '').replace("'", '')  # '인것 같'      '가자'
        sign = ['"' in i.split(' : ')[0][0], '"' in i.split(' : ')[0][-1]]  # [True      False] x2  # ("인가 '인가)
        ## []조건기호 검사
        startNs = []
        start, finish = None, None
        for listn, listi in enumerate(list(condition)):
            if listi == '<': start = listn
            if listi == '>': finish = listn; startNs.append((start, finish))
        conditions = []
        list_condition = list(condition)
        list_condition2 = []
        discount = 0
        for startN in startNs:
            start, finish = startN
            list_condition.insert(start - discount, '<>')
            discount -= 1
            for delN in range(start, finish + 1):
                list_condition2.append(list_condition[delN - discount])
                del list_condition[delN - discount]
                discount += 1
        list_condition = ''.join(list_condition)

        def del_special(a):
            result = []
            for i in list(a):
                if not i == '<' and not i == '>' and not i == '': result.append(i)
            return ''.join(result)

        list_condition = del_special(list_condition)
        # if list_condition[0] == '': list_condition = list_condition[1:]
        # if list_condition[0] == '<': list_condition = list_condition[1:]
        # if list_condition[-1] == '': list_condition = list_condition[:1]
        list_condition2 = [i.replace('<', '').replace('>', '') for i in ''.join(list_condition2).split('><')]
        list_condition_backup = list_condition
        condition = []
        if i.replace('"', '').replace("'", '')[0] == '<':
            for n in range(max([len(list_condition), len(list_condition2)])):
                try:
                    if not list_condition2[n] == '': condition.append('lambda pos,parpos: ' + list_condition2[n])
                except:
                    pass
                try:
                    condition.append(list_condition); del list_condition
                except:
                    pass
        else:
            for n in range(max([len(list_condition), len(list_condition2)])):
                try:
                    condition.append(list_condition); del list_condition
                except:
                    pass
                try:
                    if not list_condition2[n] == '': condition.append('lambda pos,parpos: ' + list_condition2[n])
                except:
                    pass

        el = []
        for con in condition:
            if 'lambda' in con:
                el.append('<Z>')
            else:
                el.append(con)
        el_count = el.count('<Z>')
        if el_count == 1:
            if el[0] == '<Z>':
                el_count = '0'
            else:
                el_count = '1'
        el = [list_condition_backup, el_count]
        els.append(el)
        db.append([condition, purpose, sign, original_text])

    with open(Options.CHJOSA_PATH, 'r') as f:
        dbStr = f.read().split('\n')

    josadb = []
    for n, i in enumerate(dbStr):
        josadb.append(i.split(' : '))

    with open(Options.JOSA_PATH, 'r') as f:
        dbStr = f.read().split('\n')

    josas = []
    for n, i in enumerate(dbStr):
        josas.append(i.split(','))  # 왼쪽이 받침 없을 때, 오른쪽이 받침 있을 때

    return db, josadb, josas, els, explain_db, autoexplain_db


def del_punctuation(pos):
    result = []
    for i in pos:
        if i[1] == 'Punctuation': continue
        result.append(i)
    return result


def replaces(string, List):
    for l in List:
        string = string.replace(l[0], l[1])
    return string


Noun, Punctuation, Josa, Modifier, Verb, Adjective, Number = 'Noun', 'Punctuation', 'Josa', 'Modifier', 'Verb', 'Adjective', 'Number'


def edit_josa(bpos, pos, josas):
    try:
        if 'Josa' in [i[1] for i in bpos]:
            last = ''
            while pos[-1] in '''~!@#$%^&*()_+-=></?.,;:'"[]{}''':
                last += pos[-1]
                pos = pos[:-1]
            for josa in josas:
                if pos[len(pos) - len(josa[0]):] in josa or pos[len(pos) - len(josa[1]):] in josa:
                    if pos[len(pos) - len(josa[1]):] in josa:
                        j = josa[1]
                    elif pos[len(pos) - len(josa[0]):] in josa:
                        j = josa[0]
                    if is_hangul(pos[len(pos) - len(j):]):
                        if has_jongsung(pos[len(pos) - len(j) - 1]) and pos[len(pos) - len(j):] == josa[0]:
                            pos = pos[:len(pos) - len(j)] + josa[1]
                        elif not has_jongsung(pos[len(pos) - len(j) - 1]) and pos[len(pos) - len(j):] == josa[1]:
                            pos = pos[:len(pos) - len(j)] + josa[0]
                    pos += last;
                    last = ''
                    break
            try:
                pos += last
            except:
                pass
    except:
        print('Hangulpy NotHangulException', '\t', bpos, pos, josas)
    return pos


def replace(db, josadb, josas, poses, TEXT, get_replaces=False):
    inp = []
    for pos in poses:
        inp.append(''.join([i[0] for i in pos]))
    inp = ' '.join(inp)
    result = []
    replace_word_history = []
    for pos in poses:
        for data in db:
            condition, purpose, sign, original_text = data
            bpos = del_punctuation(pos)
            parN = None
            for n in range(len(bpos)):
                pos0 = bpos[:n]
                pos1 = bpos[n + 1:]
                parpos = bpos[n][1]
                condition = [i.replace('&', "'") for i in condition]  # 조건문에서 '&' -> "'"

                if 'lambda' in condition[0]:
                    try:
                        is0 = eval(condition[0])(pos0, parpos)
                    except:
                        is0 = False
                    ispar = (condition[1] == bpos[n][0])
                else:
                    is0 = True; ispar = (condition[0] == bpos[n][0])
                try:
                    if 'lambda' in condition[1]:
                        try:
                            is1 = eval(condition[1])(pos1, parpos)
                        except:
                            is1 = False
                    elif 'lambda' in condition[2]:
                        try:
                            is1 = eval(condition[2])(pos1, parpos)
                        except:
                            is1 = False
                    else:
                        is1 = True
                except IndexError:
                    is1 = True
                err = False
                if len(condition) == 1:
                    true = False
                    bpos_str = ''.join([i[0] for i in bpos])
                    if condition[0] in bpos_str: true = True
                    if true:
                        err = False
                        for idx, model in MODELS.items():  # 동음이의어 예측
                            if data[3] == idx:
                                if TEXT.count(idx) == 1:
                                    predict_result = predict(TEXT, model[0], model[1], idx)
                                    if not np.argmax(predict_result): err = True
                                elif TEXT.count(idx) >= 2:
                                    idx_list = []
                                    for i in TEXT.split(' '):
                                        if idx in i: idx_list.append(i)
                                    for n, i in enumerate(idx_list):
                                        predict_result = predict(TEXT.replace(i, '').replace('  ', ' '), model[0],
                                                                 model[1], idx)
                                        if not np.argmax(predict_result) and ''.join(
                                            [i[0] for i in pos]) != i: err = True
                        if err:
                            true = False
                        else:
                            if sign[0] and not condition[0] == bpos_str[:len(condition[0])]:  # " 계산
                                true = False
                            if sign[1] and not condition[0] == bpos_str[-len(condition[0]):]:  # " 계산
                                true = False
                    if true:
                        pos = ''.join([i[0] for i in pos]).replace(condition[0], purpose)
                        replace_word_history.append(original_text)
                        pos = edit_josa(bpos, pos, josas)
                        parN = False
                        break
                if is0 and ispar and is1 and not err: parN = str(n);break
            if parN != None or parN == False: break
        if parN == None or parN == False:
            result.append(replaces(''.join([i[0] for i in pos]), josadb))
        else:
            inst = pos.copy()
            inst[int(parN)] = [purpose]
            inst = [i[0] for i in inst]
            result.append(replaces(edit_josa(bpos, ''.join(inst), josas), josadb))
            replace_word_history.append(original_text)

    inp = inp.split(' ')
    replaces_result = []
    alphaN = 0
    for n in range(len(inp)):
        try:
            if inp[n] != result[n]:
                replaces_result.append([inp[n], result[n], replace_word_history[n - alphaN]])
            else:
                alphaN += 1
        except:
            pass
    if get_replaces:
        return replaces_result

    result = ' '.join(result)
    return result, replaces_result

def del_in_list(List, delete_thing):
    result = []
    for l in List:
        if l != delete_thing: result.append(l)
    return result


def is_els_in_inp(els, inp):
    # els = [기준 문자, 기준 문자로 split했을 때 남는 문자들의 수] (ex: ['각', 2] -> '인정각' -> ['인정'] -> 1 -> False       ['각', 2] -> '인정각인데' -> ['인정', '인데'] -> 2 -> True)
    for s in inp.split(' '):
        for el in els:
            if el[0] in s:
                if el[1] == 0:
                    return True
                elif el[1] == 2 and len(del_in_list(s.split(el[0]), '')) == el[1]:
                    return True
                elif len(s.split(el[0])) == 2:
                    if s.split(el[0])[0] == '' and s.split(el[0])[1] != '' and el[1] == '1':
                        return True
                    elif s.split(el[0])[1] == '' and s.split(el[0])[0] != '' and el[1] == '0':
                        return True

    return False


def realtime_api(com_file_path="etc/realtime_api_com.txt"):
    # 실시간으로 com_file_path의 텍스트 파일을 읽어서 translate를 해주는 함수. 신조어 번역 사이트에서 쓰인다.
    import json, time
    db, josadb, josas, els, explain_db, autoexplain_db = get_db()
    print('start')
    while True:
        try:
            with open(com_file_path, 'r') as f:
                a = f.read().replace("'", '"')
                js = json.loads(a)
            if js['type'] == 'Request':
                # 신조어 번역
                inp = js['sentence']
                if is_els_in_inp(els, inp):
                    print('st')
                    tokens, poses = get_tokens(inp)
                    print(poses)
                    result = replace(db, josadb, josas, poses, inp, get_replaces=False)
                    result = result[0]
                else:
                    result = inp
                    print('token SKIP')
                try:
                    with open(com_file_path, 'r') as f:
                        a = f.read().replace("'", '"')
                        js = json.loads(a)
                    if js['type'] == 'Request' and js['sentence'] != inp:
                        continue
                except:
                    pass
                print('result:', result)
                while True:
                    try:
                        with open(com_file_path, 'w') as f:
                            f.write(str({'type': 'Result', 'sentence': result}))
                        break
                    except:
                        time.sleep(0.1)
        except:
            time.sleep(0.1)

db, josadb, josas, els, explain_db, autoexplain_db = get_db()
print()
realtime_api()