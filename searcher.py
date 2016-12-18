# coding=utf-8

import indexer
import handle_news

import time
import jieba
import re
import math

'''
'''
# 所有新闻
documents = handle_news.loadNewsDict()

# 倒排索引
postingList = indexer.loadPostingList()

# 所有词条
terms = postingList.keys()

# 新闻计数
docCount = len(documents)

length = 0
lengthTitle = 0
for doc in documents.keys():
    length += documents[doc]['contentLen']
    lengthTitle += documents[doc]['titleLen']
# 正文平均长度
docAveLen = length / docCount
# 标题平均长度
titleAveLen = lengthTitle / docCount


def tokenlize(document):
    cut_sult = jieba.cut_for_search(document)
    term_list = []
    for term in cut_sult:
        re.sub("[\s+\.\!\/_,$%^*(+\"\']+|[+——！，。？、~@#￥%……&*（）]+", "", term)
        if term != "":
            term_list.append(term)
    return term_list


def search(query, postingList=postingList, terms=terms, documents=documents, docCount=docCount, docAveLength=docAveLen,
           titleAveLength=titleAveLen, debug=False):
    search_start = time.time()  # 查询开始计时
    query_terms = query
    query_results = []  # 搜索结果
    record_match_merge = []  # 匹配的record合并结果
    query_match_terms = []  # 匹配的词项

    # 查询词汇
    for query_term in query_terms:
        if query_term in terms:
            query_match_terms.append(query_term)

    if debug:
        print("terms: )", terms)
        print("query_terms: ", query_terms)
        print("query_match_terms: ", query_match_terms)

    if query_match_terms == []:
        query_results.append('No related news.')
        return

    # BM25参数
    k1 = 2
    b = 0.75
    # 标题和正文权重
    weightTitle = 0.7
    weightContent = 0.3

    resultList = {}
    for term in query_match_terms:
        posting = postingList.get(term, 0)
        if posting != 0:

            # 倒排表文档包含正文
            if posting['df'][0] != 0:
                for docId, tf in posting['docs']:
                    tf = tf[0]
                    if tf == 0: continue
                    score = resultList.get(docId, 0.0)
                    # BM25模型
                    score += weightContent * math.log10(docCount / posting['df'][0]) * ((k1 + 1) * tf) / (
                        k1 * ((1 - b) + b * (documents[docId]['contentLen'] / docAveLength)) + tf)
                    resultList[docId] = score
            # 倒排表包含标题
            if posting['df'][0] != 0:
                for docId, tf in posting['docs']:
                    tf = tf[1]
                    if tf == 0: continue
                    score = resultList.get(docId, 0.0)
                    # BM25模型
                    score += weightTitle * math.log10(docCount / posting['df'][1]) * ((k1 + 1) * tf) / (
                        k1 * ((1 - b) + b * (documents[docId]['titleLen'] / titleAveLength)) + tf)
                    resultList[docId] = score

    resultList = sorted(resultList.items(), key=lambda x: x[1], reverse=True)
    resultList = list(map(lambda x: x[0], resultList))

    search_end = time.time()
    search_time = (search_end - search_start)
    return resultList, search_time


# 按热度排序
def searchByHot(query, postingList=postingList, terms=terms, documents=documents):
    search_start = time.time()  # 查询开始计时
    query_terms = query
    query_results = []  # 搜索结果
    record_match_merge = []  # 匹配的record合并结果
    query_match_terms = []  # 匹配的词项

    # 查询词汇
    for query_term in query_terms:
        if query_term in terms:
            query_match_terms.append(query_term)

    resultDocs = []
    for term in query_match_terms:
        posting = postingList.get(term, 0)
        if posting != 0:
            for docId, tf in posting['docs']:
                resultDocs.append(docId)

    resultDict = {}
    for docId in set(resultDocs):
        try:
            doc = documents[docId]
            postTime = doc['reportTime']
            hot = int(doc['hot'])  # 这里有一些doc的hot 类型为str，很奇怪。 应该为Int
            postTimestamp = time.mktime(time.strptime(postTime, "%Y-%m-%d %H:%M"))
            # HackerNews 热度计算
            hotScore = hot / (((time.time() - postTimestamp) / 60) ** 1.8)
            resultDict[docId] = hotScore
        except ValueError:
            # 有些doc的时间格式不太对啊 ValueError: time data '-0001-11-30 00:0' does not match format '%Y-%m-%d %H:%M'
            pass

    resultList = sorted(resultDict.items(), key=lambda x: x[1], reverse=True)
    resultList = list(map(lambda x: x[0], resultList))

    search_end = time.time()
    search_time = (search_end - search_start)
    return resultList, search_time


# 按时间排序
def searchByTime(query, postingList=postingList, terms=terms, documents=documents):
    search_start = time.time()  # 查询开始计时
    query_terms = query
    query_results = []  # 搜索结果
    record_match_merge = []  # 匹配的record合并结果
    query_match_terms = []  # 匹配的词项

    # 查询词汇
    for query_term in query_terms:
        if query_term in terms:
            query_match_terms.append(query_term)

    resultDocs = []
    for term in query_match_terms:
        posting = postingList.get(term, 0)
        if posting != 0:
            for docId, tf in posting['docs']:
                resultDocs.append(docId)

    resultDict = {}
    for docId in set(resultDocs):
        doc = documents[docId]
        postTime = doc['reportTime']
        resultDict[docId] = postTime

    resultList = sorted(resultDict.items(), key=lambda x: x[1], reverse=True)
    resultList = list(map(lambda x: x[0], resultList))

    search_end = time.time()
    search_time = (search_end - search_start)
    return resultList, search_time


if __name__ == '__main__':
    # documents = handle_news.loadNewsDict()
    # postingList = indexer.loadPostingList()
    #
    # length = 0
    # for doc in documents.keys():
    #     length += documents[doc]['contentLen']
    # docAveLen = length / len(documents)

    query = "詹姆斯"

    result = search(query, postingList, postingList.keys(), documents, len(documents), docAveLen, False)
    print(result)
