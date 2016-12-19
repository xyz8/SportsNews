# coding=utf-8
import json
import jieba
import pickle
import time

# 把新闻分词后 保存
def segWords():
    count = 0
    newLines = []
    with open("all.txt") as file:
        for line in file:
            count += 1
            print(count)
            jsonObj = json.loads(line)
            id = jsonObj['id']
            content = jsonObj['content']
            title = jsonObj['title']

            contentSeg = []
            for word in jieba.cut_for_search(content):
                if word.strip() == "":
                    continue
                contentSeg.append(word)
            jsonObj['contentSeg'] = " ".join(contentSeg)
            jsonObj['contentLen'] = len(contentSeg)
            titleSeg = []
            for word in jieba.cut_for_search(title):
                if word.strip() == "":
                    continue
                titleSeg.append(word)
            jsonObj['titleSeg'] = " ".join(titleSeg)
            jsonObj['titleLen'] = len(titleSeg)
            newLines.append(json.dumps(jsonObj) + "\n")

    with open("all_seg.txt", "w") as file:
        file.writelines(newLines)


# 读新闻数据，用pickle序列化保存
def saveNewsDict():
    newsDic = {}
    count = 0
    with open("all_seg.txt") as file:
        for line in file:
            count += 1
            print(count)
            jsonObj = json.loads(line)
            id = jsonObj['id']
            content = jsonObj['content']
            contentLen = jsonObj['contentLen']
            title = jsonObj['title']
            titleLen = jsonObj['titleLen']
            source = jsonObj['origin']
            report_time = jsonObj['report_date']
            url = jsonObj['url']
            hot = jsonObj['hot']
            crawl_time = jsonObj['crawl_date']
            keyword = jsonObj['keyword']
            category = jsonObj['category']
            newsDic[id] = {}
            newsDic[id]['id'] = id
            newsDic[id]['content'] = content
            newsDic[id]['contentLen'] = contentLen
            newsDic[id]['title'] = title
            newsDic[id]['titleLen'] = titleLen
            newsDic[id]['reportTime'] = report_time
            newsDic[id]['source'] = source
            newsDic[id]['url'] = url
            newsDic[id]['hot'] = hot
            newsDic[id]['crawl_time'] = crawl_time
            newsDic[id]['keyword'] = keyword
            newsDic[id]['category'] = category
    pickle.dump(newsDic, open("newsDic", 'wb'), True)


# 读词典
def loadNewsDict():
    return pickle.load(open("newsDic", "rb"))


if __name__ == '__main__':
    # print(time.time())
    # loadNewsDict()
    # print(time.time())
    saveNewsDict()
