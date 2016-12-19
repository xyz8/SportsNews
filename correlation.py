# coding=utf=8

import json
from gensim.models import Word2Vec
import jieba
import pickle
import time

word2vecModel = Word2Vec.load_word2vec_format("word2vec.model", binary=True)
docSimilarDict = pickle.load(open("doc_similar_dict.bin", "rb"))


# 最相似的五个词
def getSimilarWords(query):
    words = []
    for word in query:
        if word in word2vecModel:
            words.append(word)
    if words!=[]:
        result = word2vecModel.most_similar(positive=words, topn=5)
        return [x[0] for x in result]
    else:
        return []


def getSimilarDocs(docId):
    return docSimilarDict[docId]


