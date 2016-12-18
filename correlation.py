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
    result = word2vecModel.most_similar(positive=words, topn=5)
    print(result)
    return [x[0] for x in result]


def getSimilarDocs(docId):
    return docSimilarDict[docId]


if __name__ == '__main__':
    a = time.time()
    list = ['李', '詹姆斯', '进攻', '李博伟', '詹姆斯', '李博伟', '薛菲']
    s = getSimilarWords(list)
    print(s)
    print(time.time() - a)
