#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
@author: juzipi
@file: bm25.py
@time:2022/04/16
@description:
"""
import math
import os
import jieba
import pickle
import logging
import pandas as pd
from config import pdf_extract_file
import sys


jieba.setLogLevel(log_level=logging.INFO)


class BM25Param(object):
    def __init__(self, f, df, idf, length, avg_length, docs_list, line_length_list,k1=1.5, k2=1.0,b=0.75,pdf_info = []):
        """

        :param f:
        :param df:
        :param idf:
        :param length:
        :param avg_length:
        :param docs_list:
        :param line_length_list:
        :param k1: 可调整参数，[1.2, 2.0]
        :param k2: 可调整参数，[1.2, 2.0]
        :param b:
        """
        self.f = f
        self.df = df
        self.k1 = k1
        self.k2 = k2
        self.b = b
        self.idf = idf
        self.length = length
        self.avg_length = avg_length
        self.docs_list = docs_list
        self.line_length_list = line_length_list
        self.pdf_info = pdf_info


    def __str__(self):
        return f"k1:{self.k1}, k2:{self.k2}, b:{self.b}"


class BM25(object):
    _param_pkl = "data/param.pkl"
    _docs_path = "data/data.txt"
    _stop_words_path = "data/stop_words.txt"
    _stop_words = []

    def __init__(self, docs=""):
        self.docs = docs
        self.param: BM25Param = self._load_param()

    def _load_stop_words(self):
        if not os.path.exists(self._stop_words_path):
            raise Exception(f"system stop words: {self._stop_words_path} not found")
        stop_words = []
        with open(self._stop_words_path, 'r', encoding='utf8') as reader:
            for line in reader:
                line = line.strip()
                stop_words.append(line)
        return stop_words

    def _build_param(self):

        def _cal_param(pd_docs):
            f = []  # 列表的每一个元素是一个dict，dict存储着一个文档中每个词的出现次数
            df = {}  # 存储每个词及出现了该词的文档数量
            idf = {}  # 存储每个词的idf值
            lines = pd_docs['pdf_content'].tolist()
            pdf_info = []
            length = len(lines)
            words_count = 0
            docs_list = []
            line_length_list =[]
            for ind,row in pd_docs.iterrows():
                pdf_info.append([row['pdf_name'],row['pdf_path']])
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                words = [word for word in jieba.lcut(line) if word and word not in self._stop_words]
                line_length_list.append(len(words))
                docs_list.append(line)
                words_count += len(words)
                tmp_dict = {}
                for word in words:
                    tmp_dict[word] = tmp_dict.get(word, 0) + 1
                f.append(tmp_dict)
                for word in tmp_dict.keys():
                    df[word] = df.get(word, 0) + 1
            for word, num in df.items():
                idf[word] = math.log(length - num + 0.5) - math.log(num + 0.5)
            param = BM25Param(f, df, idf, length, words_count / length, docs_list, line_length_list,pdf_info = pdf_info)
            print(len(docs_list),' ',len(lines), ' ',len(pdf_info))
            return param

        # cal
        if self.docs:
            if not os.path.exists(self.docs):
                raise Exception(f"input docs {self.docs} not found")
            pd_docs = pd.read_csv(self.docs,sep = ',')
            param = _cal_param(pd_docs)

        else:
            raise ('please spicify the doc files')
            #if not os.path.exists(self._docs_path):
            #    raise Exception(f"system docs {self._docs_path} not found")
            #with open(self._docs_path, 'r', encoding='utf8') as reader:
            #    param = _cal_param(reader)

        with open(self._param_pkl, 'wb') as writer:
            pickle.dump(param, writer)
        return param

    def _load_param(self):
        self._stop_words = self._load_stop_words()
        if is_flush_data in ['0',0] and os.path.isfile(self._param_pkl):
            with open(self._param_pkl, 'rb') as reader:
                param = pickle.load(reader)
        else:
            param = self._build_param()

        return param

    def _cal_similarity(self, words, index):
        score = 0
        for word in words:
            if word not in self.param.f[index]:
                continue
            molecular = self.param.idf[word] * self.param.f[index][word] * (self.param.k1 + 1)
            denominator = self.param.f[index][word] + self.param.k1 * (1 - self.param.b +
                                                                       self.param.b * self.param.line_length_list[index] /
                                                                       self.param.avg_length)
            score += molecular / denominator
        return score

    def cal_similarity(self, query: str):
        """
        相似度计算，无排序结果
        :param query: 待查询结果
        :return: [(doc, score), ..]
        """
        words = [word for word in jieba.lcut(query) if word and word not in self._stop_words]
        score_list = []
        for index in range(self.param.length):
            score = self._cal_similarity(words, index)
            score_list.append((self.param.pdf_info[index][0],self.param.pdf_info[index][1], score))
        return score_list

    def cal_similarity_rank(self, query: str):
        """
        相似度计算，排序
        :param query: 待查询结果
        :return: [(doc, score), ..]
        """
        result = self.cal_similarity(query)
        result.sort(key=lambda x: -x[-1])
        return result



if __name__ == '__main__':
    if len(sys.argv) > 1:
        is_flush_data = sys.argv[1]
    else:
        is_flush_data = '0'

    bm25 = BM25(docs = pdf_extract_file)
    query_content = "有丰富的论文经验"
    #result = bm25.cal_similarity(query_content)
    #for line, score in result:
    #    print(line, score)
    print("**"*100)
    result = bm25.cal_similarity_rank(query_content)
    for pdf_name,pdf_path, score in result:
        if score > 0.05:
            print(score,' ',pdf_name,' ',pdf_path)
            print()
