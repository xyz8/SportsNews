# coding=utf-8

import json
import pickle
import time
import math

# 构建倒排记录表
def set_ivs_index(debug=False):
    if debug:
        count = 0

    documents = {}
    with open("all_seg.txt") as file:
        for line in file:
            jsonObj = json.loads(line)
            id = jsonObj['id']
            documents[id] = {}
            documents[id]['content'] = jsonObj['contentSeg']
            documents[id]['title'] = jsonObj['titleSeg']

    print("读取文档完毕")
    TF_Set = {}
    TF_Set_Title = {}
    for docId in documents.keys():

        if debug:
            count += 1
            print("读取第%d个文档" % count)

        terms = documents[docId]['content'].split()
        for term in terms:
            TF_Set[term] = TF_Set.get(term, {})
            TF_Set[term][docId] = TF_Set[term].get(docId, 0) + 1

        termsTitle = documents[docId]['title'].split()
        for term in termsTitle:
            TF_Set_Title[term] = TF_Set_Title.get(term, {})
            TF_Set_Title[term][docId] = TF_Set_Title[term].get(docId, 0) + 1

    # 获取词典部分
    termsContent = list(TF_Set.keys())
    print(termsContent)
    termsTitle = list(TF_Set_Title.keys())
    print(termsTitle)

    # 合并标题中和正文中的词项
    termsContent.extend(termsTitle)
    terms = set(termsContent)
    terms = sorted(terms)

    if debug:
        count = 0

    # 倒排记录表
    index = {}
    for term in terms:

        if debug:
            count += 1
            print("构建第%d个索引：%s" % (count, term))

        docsContent = list(TF_Set.get(term, {}).keys())  # 当前词项对应的文档
        df_content = len(docsContent)  # 当前此项的文档频率

        docsTitle = list(TF_Set_Title.get(term, {}).keys())
        df_title = len(docsTitle)

        docsContent.extend(docsTitle)
        docs = set(docsContent)
        docs = sorted(docs)

        index[term] = {}
        index[term]['df'] = (df_content, df_title)
        index[term]['docs'] = []
        for doc in docs:
            index[term]['docs'].append(
                (doc, (TF_Set.get(term, {}).get(doc, 0), TF_Set_Title.get(term, {}).get(doc, 0))))
    return index


# pickle序列化保存倒排记录表
def savePostingList(posting):
    pickle.dump(posting, open("postingList", "wb"), True)


def loadPostingList():
    return pickle.load(open("postingList", "rb"))

if __name__ == '__main__':
    postingList = set_ivs_index(debug=True)
    savePostingList(postingList)

    print(time.time())
    loadPostingList()
    print(time.time())
