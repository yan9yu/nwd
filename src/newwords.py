#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import division
import re
import os
import math
import config
import pandas as pd
from collections import Counter
from collections import defaultdict

__author__ = 'yan9yu'


class NewWordsDetector:
    def __init__(self, content):
        self.content = content
        self.words_frequency = self.get_words_freq()
        self.words = self.get_words()
        self.words_cohesion = self.get_words_cohesion()
        self.words_entropy = self.get_words_entropy()
        self.new_words = self.new_words_filter()

    def get_words_freq(self):
        words_frequency = Counter()

        # 仅保留中文, 剔除英文及数字
        pattern = re.compile(u'[^\u4e00-\u9fa5]+')
        content = pattern.sub('', self.content)

        # 采用滑动窗口的方式切分文本. 目前最大窗口为5.
        ## 向右切割字符串
        words_frequency.update(content[ii:ii + nn] for nn in xrange(1, config.Threshold.MAX_NGRAM + 1) for ii in
                               xrange(len(content) - nn, -1, -1))

        # ## 向左切割字符串
        rev_content = content[::-1]
        words_frequency.update(
            rev_content[ii:ii + nn][::-1] for nn in xrange(1, config.Threshold.MAX_NGRAM + 1) for ii in
            xrange(len(rev_content) - nn, -1, -1))

        return words_frequency

    def get_words(self):
        # 剔除词频过低的词
        raw = [word for word, count in self.words_frequency.iteritems() if
               count >= config.Threshold.MIN_FREQUENCE and config.Threshold.MIN_LENGTH <= len(
                   word) <= config.Threshold.MAX_LENGTH]

        words = {}
        for word in raw:
            words[word] = {}
            words[word]["frequency"] = 0
            words[word]["cohesion"] = 0
            words[word]["entropy"] = 0

        return words

    def get_words_cohesion(self):
        # 计算词之间的凝固度
        words_cohesion = defaultdict(float)

        MINF = config.Threshold.MIN_FREQUENCE
        for word in self.words:
            length = len(word)
            frequency = self.words_frequency.get(word, config.Threshold.MIN_FREQUENCE)

            # 每个词切分成两个词. 首个词的长度依次递增.
            cohesions = map(lambda (x, y, z): x / (y * z),
                            [(frequency, self.words_frequency.get(word[0:ii], MINF),
                              self.words_frequency.get(word[ii:length], MINF)) for ii in xrange(1, length)])

            words_cohesion[word] = min(cohesions)

        return words_cohesion

    def get_words_entropy(self):
        # 计算词的最大熵
        def _get_entropy(lists):
            _entropy = 0.0
            if lists:
                _sum = sum(lists)
                _prob = map(lambda x: x / _sum, lists)
                _entropy = sum(map(lambda x: -x * math.log(x), _prob))
            return _entropy

        right_entropy = defaultdict(list)

        # TODO: 最右熵计算
        for word, count in self.words_frequency.iteritems():
            length = len(word)
            right_word = word[: - 1]
            if length >= config.Threshold.MIN_LENGTH and right_word in self.words:
                right_entropy[right_word].append(count)

        # 获取每个词的最大熵
        entropy = map(lambda x: _get_entropy(right_entropy.get(x, None)), self.words)
        words_entropy = dict(zip(self.words, entropy))

        return words_entropy

    def merge(self, data):
        # 合并正向和逆向结果
        for word in data:
            act_word = word[::-1]
            if act_word in self.words:
                self.words[act_word]["frequency"] += data[word]["frequency"]
                self.words[act_word]["cohesion"] += data[word]["cohesion"]
                self.words[act_word]["entropy"] += data[word]["entropy"]
            else:
                self.words[act_word] = data[word]

        return self.words

    def new_words_filter(self):
        # 根据设定的阈值进行筛选
        new_words = defaultdict(dict)
        for word in self.words:
            frequency = self.words_frequency[word]
            cohesion = self.words_cohesion[word]
            entropy = self.words_entropy[word]
            data = {}
            if frequency >= config.Threshold.MIN_FREQUENCE and cohesion >= config.Threshold.MIN_COHESION and entropy >= config.Threshold.MIN_ENTROPY:
                data["frequency"] = frequency
                data["cohesion"] = cohesion
                data["entropy"] = entropy
                new_words[word] = data


        # 剔除长度较短的词, 保留最大长度的新词
        words = new_words.keys()
        words.sort(key=len)
        sub_words = set()
        for ii in xrange(0, len(words) - 1):
            word_ii = words[ii]
            for jj in xrange(ii + 1, len(words)):
                word_jj = words[jj]
                if len(word_ii) < len(word_jj) and word_ii in word_jj:
                    sub_words.add(word_ii)

        for word in sub_words:
            if word in new_words:
                del new_words[word]

        return new_words


def get_content(path):
    content = ""
    files = [path + item for item in os.listdir(path)]
    for f in files:
        with open(f, "r") as fp:
            data = "".join(fp.readlines())
            if len(data) > 0:
                raw = data.strip().decode(encoding='utf-8', errors='ignore')
                content += raw
    return content


def main():
    msg = "WARNING: Program running using below configuation\nFrequency:\t%s\nCohesion:\t%s\nEntropy:\t%s\n" % (
        config.Threshold.MIN_FREQUENCE, config.Threshold.MIN_COHESION, config.Threshold.MIN_ENTROPY)
    print config.bcolors.WARNING + msg + config.bcolors.ENDC

    content = get_content(config.Path.CORPUS)
    nwd = NewWordsDetector(content)

    if config.Detection.IS_REVERSE:
        content_ext = content[::-1]
        new_words_ext = NewWordsDetector(content_ext)
        nwd.merge(new_words_ext.new_words)

    if len(nwd.new_words) == 0:
        exit(-1)

    msg = "COMPLETED! Get %s new words" % (len(nwd.new_words))
    print config.bcolors.OKGREEN + msg + config.bcolors.ENDC
    df = pd.DataFrame(nwd.new_words).T
    df = df.sort_index(by=["entropy"], ascending=False)
    result_path = config.Path.RESULT + "results.dat"
    df.to_csv(result_path, sep="\t", encoding="utf-8")


if __name__ == "__main__":
    main()
