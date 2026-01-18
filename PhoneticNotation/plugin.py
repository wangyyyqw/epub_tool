#!/usr/bin/env python
# -*- coding: utf-8 -*-

from copy import deepcopy
import sys,os,re,time
from typing import Sized
import Dict.ShengPiZi
import configparser

e = os.environ.get('SIGIL_QT_RUNTIME_VERSION', '6.5.2')
SIGIL_QT_MAJOR_VERSION = tuple(map(int, (e.split("."))))[0]
if SIGIL_QT_MAJOR_VERSION == 6:
    from PySide6 import QtWidgets,QtGui,QtCore
elif SIGIL_QT_MAJOR_VERSION == 5:
    from PyQt5 import QtWidgets,QtGui,QtCore


BOOK_NOREPEAT_SWITCH = False # 不重复开关（整本）
PAGE_NOREPEAT_SWITCH = False # 不重复开关（页内）

READ_PHRASES = True # 读词典开关


UEMPTY = ''
# states
(START, END, FAIL, WAIT_TAIL) = list(range(4))
# conditions
(TAIL, ERROR, MATCHED_SWITCH, UNMATCHED_SWITCH, CONNECTOR) = list(range(5))

MAPS = {}
LOG = {}
LOG_PER_PAGE = {}

class Timer():
    def __init__(self):
        self.t = time.perf_counter()
    def timer(self):
        t_ = self.t
        self.t = time.perf_counter()
        return self.t - t_

def initMaps():

    from Dict.ShengPiZi import shengpizi_dict
    from Dict.Phrases import phrases_dict

    mapping = {}
    for code in shengpizi_dict:
        mapping[code] = shengpizi_dict[code]
    
    for key in phrases_dict:
        mapping[key] = phrases_dict[key]

    global MAPS
    MAPS = ConvertMap(mapping)

    del shengpizi_dict, phrases_dict


class Node(object):
    def __init__(self, from_word, to_phonetic=None, is_tail=True,
            have_child=False):
        self.from_word = from_word
        if to_phonetic is None: #字典中没有该键
            self.to_phonetic = from_word
            self.is_original = True #需返回原值
        else: #字典中存在该键
            if BOOK_NOREPEAT_SWITCH and from_word in LOG:
                self.to_phonetic = from_word
                self.is_original = True
            elif PAGE_NOREPEAT_SWITCH and from_word in LOG_PER_PAGE:
                self.to_phonetic = from_word
                self.is_original = True
            else:
                self.to_phonetic = to_phonetic or from_word #如果字典中存在该键但对应值为空，则返回原值（短语前缀类的过渡关键字）
                self.is_original = False

        self.is_tail = is_tail # is_tail 标志该节点不属于短语前缀，可能是在字典中有键值，对应值非空，或在字典中无键值两种。
        self.have_child = have_child

    def is_original_long_word(self): # 在字典中找不到键的短语
        return self.is_original and len(self.from_word)>1

    def is_follow(self, chars): #查询传入字符串是否该节点键值前缀部分
        return chars != self.from_word[:-1]

    def add_phonetic(self):
        if type(self.to_phonetic) == str:
            return self.to_phonetic
        elif type(self.to_phonetic) == list:
            if len(self.from_word) == 1:
                return '<ruby>' + self.from_word+'<rt>'+self.to_phonetic[0] +'</rt></ruby>'
            elif len(self.from_word) > 1 and len(self.from_word) == len(self.to_phonetic):
                index,result = 0,''
                for char in self.from_word:
                    result = result + char if not self.to_phonetic[index]\
                           else result + '<ruby>' + char + '<rt>' + self.to_phonetic[index] +'</rt></ruby>'
                    index += 1
                return result

    def __str__(self):
        return '<Node, %s, %s, %s, %s>' % (repr(self.from_word),
                repr(self.to_phonetic), self.is_tail, self.have_child)

    __repr__ = __str__

class ConvertMap(object):
    def __init__(self, mapping=None):
        self._map = {}
        if mapping:
            self.set_convert_map(mapping)

    def set_convert_map(self, mapping):
        convert_map = {}
        have_child = {}
        max_key_length = 0
        for key in sorted(mapping.keys()):
            if len(key)>1:
                for i in range(1, len(key)):
                    parent_key = key[:i]
                    have_child[parent_key] = True
            have_child[key] = False
            max_key_length = max(max_key_length, len(key))
        for key in sorted(have_child.keys()):
            convert_map[key] = (key in mapping, have_child[key],
                    mapping.get(key, UEMPTY))
        self._map = convert_map
        self.max_key_length = max_key_length

    def __getitem__(self, k):
        try:
            is_tail, have_child, to_phonetic  = self._map[k]
            return Node(k, to_phonetic, is_tail, have_child)
        except:
            return Node(k)

    def __contains__(self, k):
        return k in self._map

    def __len__(self):
        return len(self._map)

class StatesMachineException(Exception): pass

class StatesMachine(object):
    def __init__(self):
        self.state = START
        self.final = UEMPTY
        self.len = 0
        self.pool = UEMPTY
        self.last_matched = None #用于记录，不参与转化过程

    def clone(self, pool):
        new = deepcopy(self)
        new.state = WAIT_TAIL
        new.pool = pool
        new.last_matched = self.last_matched
        return new

    def feed(self, char, map):
        self.node = node = map[self.pool+char]
        if node.have_child:
            if node.is_tail:
                if node.is_original: 
                    #该字符串属于字典中的键值，也属于某键前缀，但该键值对应值为None。、
                    #属于字典编写不合理的状态，一般不会出现这个状态。
                    cond = UNMATCHED_SWITCH
                else: # 该字符串属于字典中的键，又属于某键前缀
                    cond = MATCHED_SWITCH
            else: # 该字符串不属于字典中的键，但属于某键前缀
                cond = CONNECTOR
        else: # 该字符串不属于某键前缀
            if node.is_tail: # 该字符串属于字典中的键或者非键
                cond = TAIL
            else: # 未知错误状态
                cond = ERROR

        new = None
        if cond == ERROR:
            self.state = FAIL
        elif cond == TAIL:
            if self.state == WAIT_TAIL and node.is_original_long_word():
                self.state = FAIL
                #录入LOG
                if self.last_matched is not None:
                    key,value = self.last_matched
                    LOG[key] = value
                    LOG_PER_PAGE[key] = value
            else:
                self.final += node.add_phonetic()
                self.len += 1
                self.pool = UEMPTY
                self.state = END
                #录入LOG
                if not node.is_original:
                    LOG[node.from_word] = node.to_phonetic
                    LOG_PER_PAGE[node.from_word] = node.to_phonetic
        elif self.state == START or self.state == WAIT_TAIL:
            if cond == MATCHED_SWITCH:
                self.last_matched = [node.from_word,node.to_phonetic]
                new = self.clone(node.from_word)
                self.final += node.add_phonetic()
                self.len += 1
                self.state = END
                self.pool = UEMPTY
            elif cond == UNMATCHED_SWITCH or cond == CONNECTOR:
                if self.state == START:
                    new = self.clone(node.from_word)
                    self.final += node.add_phonetic()
                    self.len += 1
                    self.state = END
                else:
                    if node.is_follow(self.pool):
                        self.state = FAIL
                    else:
                        self.pool = node.from_word
        elif self.state == END:
            # END is a new START
            self.state = START
            new = self.feed(char, map)
        elif self.state == FAIL:
            raise StatesMachineException('Translate States Machine '
                    'have error with input data %s' % node)
        return new

    def __len__(self):
        return self.len + 1

    def __str__(self):
        return '<StatesMachine %s, pool: "%s", state: %s, final: %s>' % (
                id(self), self.pool, self.state, self.final)
    __repr__ = __str__

class Converter(object):
    def __init__(self):
        self.map = MAPS
        self.start()

    def feed(self, char):
        branches = []
        for fsm in self.machines:
            new = fsm.feed(char, self.map)
            if new:
                branches.append(new)
        if branches:
            self.machines.extend(branches)
        self.machines = [fsm for fsm in self.machines if fsm.state != FAIL]
        all_ok = True
        for fsm in self.machines:
            if fsm.state != END:
                all_ok = False
        if all_ok:
            self._clean()
        return self.get_result()

    def _clean(self):
        if len(self.machines):
            self.machines.sort(key=lambda x: len(x))
            # self.machines.sort(cmp=lambda x,y: cmp(len(x), len(y)))
            self.final += self.machines[0].final
            
        self.machines = [StatesMachine()]

    def start(self):
        self.machines = [StatesMachine()]
        self.final = UEMPTY

    def end(self):
        self.machines = [fsm for fsm in self.machines
                if fsm.state == FAIL or fsm.state == END]
        self._clean()

    def convert(self, string):
        self.start()
        for char in string:
            self.feed(char)
        self.end()
        return self.get_result()

    def get_result(self):
        return self.final

def convert_chars(match):
    text = ''
    for char in match.group():
        try:
            MAPS[char]
            if BOOK_NOREPEAT_SWITCH and char in LOG.keys():
                text += char
            elif PAGE_NOREPEAT_SWITCH and char in LOG_PER_PAGE.keys():
                text += char
            else:
                #print(Dict.ShengPiZi.shengpizi_dict[char][0])
                text += '<ruby>' + char + '<rt>' +Dict.ShengPiZi.shengpizi_dict[char][0] + '</rt></ruby>'
                LOG[char] = Dict.ShengPiZi.shengpizi_dict[char]
                LOG_PER_PAGE[char] = Dict.ShengPiZi.shengpizi_dict[char]
        except:
            text += char
    return text

def log():
    text = ''
    text += '-'*13+'\n执行结果统计：\n'+'-'*13 +'\n'
    text += '【共注音生僻字%d个】'%len(LOG) + '\n'
    text += ''.join(LOG.keys())+ '\n\n'
    monophonic_chars = list(filter(lambda key:len(LOG[key]) == 1,LOG.keys()))
    text += '【包含单音生僻字%d个】'%len(monophonic_chars) +'\n'
    text += ''.join(monophonic_chars) +'\n\n'
    polyphonic_chars = list(filter(lambda key:len(LOG[key])>1,LOG.keys()))
    text += '【含多音生僻字%d个】'%len(polyphonic_chars) + '\n'
    text += ''.join(polyphonic_chars)+ '\n\n'
    text += '-'*13+'\n已注音的生僻字：\n'+'-'*13 +'\n'
    multitone = ''
    for key in LOG:
        phonetic = ','.join(LOG[key])
        text += '%s : %s\n'%(key,phonetic)
        if len(LOG[key]) > 1:
            multitone += '%s : %s\n'%(key,phonetic)
    text += '\n'+'-'*13+'\n多音生僻字：\n'+'-'*13 +'\n'
    text += multitone
    return text

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.isRun = False
        self.initUI()
        self.initFunc()
        self.load_ini()
        self.show()
    def initUI(self):
        self.resize(250, 115)
        font = QtGui.QFont()
        font.setPixelSize(15)
        self.setFont(font)
        icon_path = os.path.join(os.path.dirname(__file__),'plugin.png')
        self.setWindowIcon(QtGui.QIcon(icon_path))
        self.setWindowTitle('生僻字注音')
        self.centralwidget = QtWidgets.QWidget(self)
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.noRepeatLayout = QtWidgets.QHBoxLayout()
        self.no_repeated_cbox = QtWidgets.QCheckBox(text="相同字符仅注音一次")
        self.no_repeated_in_book_rbt = QtWidgets.QRadioButton(text="整本")
        self.no_repeated_in_page_rbt = QtWidgets.QRadioButton(text="章内")
        self.noRepeatLayout.addWidget(self.no_repeated_cbox)
        self.noRepeatLayout.addWidget(self.no_repeated_in_book_rbt)
        self.noRepeatLayout.addWidget(self.no_repeated_in_page_rbt)
        self.read_phrases_cbox = QtWidgets.QCheckBox(text="通过词典校读多音字")
        self.verticalLayout.addLayout(self.noRepeatLayout)
        self.verticalLayout.addWidget(self.read_phrases_cbox)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.comfirm_btn = QtWidgets.QPushButton(text="执行")
        self.cancel_btn = QtWidgets.QPushButton(text="退出")
        self.horizontalLayout.addWidget(self.comfirm_btn)
        self.horizontalLayout.addWidget(self.cancel_btn)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.setCentralWidget(self.centralwidget)
    def initFunc(self):
        self.no_repeated_cbox.stateChanged.connect(lambda state:self.Switch(1,state))
        self.comfirm_btn.clicked.connect(self.run)
        self.cancel_btn.clicked.connect(self.close)
    def Switch(self,sender,state):
        if sender == 1:
            if state == QtCore.Qt.Checked:
                for w in (
                    self.no_repeated_in_book_rbt, 
                    self.no_repeated_in_page_rbt
                ):
                    w.setEnabled(True)
            else:
                for w in (
                    self.no_repeated_in_book_rbt,
                    self.no_repeated_in_page_rbt
                ):
                    w.setEnabled(False)
    def run(self):
        global BOOK_NOREPEAT_SWITCH,PAGE_NOREPEAT_SWITCH,READ_PHRASES
        if self.no_repeated_cbox.isChecked():
            BOOK_NOREPEAT_SWITCH = True  if self.no_repeated_in_book_rbt.isChecked() else False
            PAGE_NOREPEAT_SWITCH = True if self.no_repeated_in_page_rbt.isChecked() else False
        READ_PHRASES = True if self.read_phrases_cbox.isChecked() else False
        self.isRun = True
        self.close()
    def load_ini(self):
        no_repeat_sw = 0
        no_repeat_in_book = 1
        no_repeat_in_page = 0
        read_phrases = 0
        conf = configparser.ConfigParser()
        curdir = os.path.dirname(os.path.realpath(__file__))
        cfgpath = os.path.join(curdir,'config.ini')
        if os.path.exists(cfgpath):
            conf.read(cfgpath, encoding="utf-8")
            try:
                no_repeat_sw = int(conf.get('settings','no_repeat_sw'))
                no_repeat_in_book = int(conf.get('settings','no_repeat_in_book'))
                no_repeat_in_page = int(conf.get('settings','no_repeat_in_page'))
                read_phrases = int(conf.get('settings','read_phrases'))
            except:
                pass
        else:
            pass
        sw = True if no_repeat_sw == 1 else False
        self.no_repeated_cbox.setChecked(sw)
        self.no_repeated_in_book_rbt.setEnabled(sw)
        self.no_repeated_in_page_rbt.setEnabled(sw)

        sw = True if no_repeat_in_book == 1 else False
        self.no_repeated_in_book_rbt.setChecked(sw)

        sw = True if no_repeat_in_page == 1 else False
        self.no_repeated_in_page_rbt.setChecked(sw)

        sw = True if read_phrases == 1 else False
        self.read_phrases_cbox.setChecked(sw)


    def save_ini(self):
        no_repeat_sw = 1 if self.no_repeated_cbox.isChecked() else 0
        no_repeat_in_book = 1 if self.no_repeated_in_book_rbt.isChecked() else 0
        no_repeat_in_page = 1 if self.no_repeated_in_page_rbt.isChecked() else 0
        read_phrases = 1 if self.read_phrases_cbox.isChecked() else 0
        curdir = os.path.dirname(os.path.realpath(__file__))
        conf = configparser.ConfigParser()
        conf.add_section("settings")
        conf.set("settings", "no_repeat_sw", str(no_repeat_sw))
        conf.set("settings", "no_repeat_in_book", str(no_repeat_in_book))
        conf.set("settings", "no_repeat_in_page", str(no_repeat_in_page))
        conf.set("settings", "read_phrases", str(read_phrases))
        with open(os.path.join(curdir,'config.ini'),'w',encoding='utf-8') as cf:
            conf.write(cf)
    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.save_ini()
        return super().closeEvent(a0)

initMaps()

def run(bk):

    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    app.exec()

    if win.isRun == False:
        return 0

    print('生僻字注音：\n'+
          '生僻字字典路径：/Dict/ShengPiZi.py\n'+
          '词汇字典路径：/Dict/Phrases.py\n\n')

    clock = Timer().timer
    clock()
    print('正在处理中，请等待：',end='')
    for fid,href in bk.text_iter():
        LOG_PER_PAGE.clear()
        html = bk.readfile(fid)
        body = re.search(r'<body[^>]*>.*</body>',html,re.S)
        if body is not None:
            if READ_PHRASES:
                conv_text = re.sub(r'(?<!<ruby>)[^\x20-\x7E\r\n]+',lambda x:Converter().convert(x.group()),body.group())
            else:
                conv_text = re.sub(r'(?<!<ruby>)[^\x20-\x7E\r\n]+',convert_chars,body.group())
            new_html = html[:body.start()] + conv_text + html[body.end():]
            bk.writefile(fid,new_html)
        print(' *',end='')
    log_text = log()

    try:
        bk.writefile('log_text.txt',log_text)
    except:
        bk.addfile('log_text.txt','log_text.txt',log_text,"text/plain")

    print('\n\n生僻字注音完毕，处理记录已生成到OEBPS/Misc/log_text.txt中\n')
    print(log_text)
    
    print('耗费时间 %.3f'%clock())

    return 0

def main():
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    app.exec()
    #text = '大水冲了龙王庙𠀅𠀉'
    #Converter().convert(text)
    pass

if __name__ == '__main__':
    main()
