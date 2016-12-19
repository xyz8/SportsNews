from flask import Flask, render_template, request
import handle_news
import indexer
import jieba
import searcher
import pickle
import correlation
import json
import math

app = Flask(__name__)

jieba.initialize()
pageSize = 10


@app.route('/')
@app.route('/query/')
@app.route('/query/<query>')
def search(query=None):
    # 排序方式 0相关性 1热度 2时间
    order = request.args.get('order', '0')
    page = int(request.args.get('page', 1))

    if query != "" and query != None:
        terms = searcher.tokenlize(query)

        print(terms)

        if order == '0':
            docs, sTime = searcher.search(terms)
        elif order == '1':
            docs, sTime = searcher.searchByHot(terms)
        elif order == '2':
            docs, sTime = searcher.searchByTime(terms)
        results = []
        related = correlation.getSimilarWords(terms)
        if docs != None:
            for id in docs:
                results.append(searcher.documents[id])
            resultCount = len(results)
            # 分页
            start = (page - 1) * pageSize
            end = (page) * pageSize
            results = results[start:end]
            pageDict = setPage(resultCount, page)

        sortClass = ['default', 'default', 'default']
        sortClass[int(order)] = 'primary'
        return render_template("results.html", results=results, related=related, resultCount=resultCount, sTime=sTime,
                               query=query, sortClass=sortClass, pageDict=pageDict, order=order)
    return render_template("index.html")


def setPage(total, current):
    pageSize = 10
    pageDict = {'hasPre': True, 'hasNext': True}
    pageCount = math.ceil(total / pageSize)
    if current == 1:
        pageDict['hasPre'] = False
    if current == pageCount:
        pageDict['hasNext'] = False

    # 显示的链接数
    window = 7
    if current - 5 <= 0:
        start = 1
        end = min([pageCount, start + window])
    elif current + 5 >= pageCount:
        end = pageCount
        start = max([1, end - window])
    else:
        start = max([1, current - 4])
        end = min([pageCount, current + 3])
    pageDict['current'] = current
    pageDict['pages'] = list(range(start, end + 1))
    return pageDict


@app.route('/news/<id>')
def news(id):
    news = searcher.documents.get(id, 0)
    if news != 0:
        related = []
        similarDocs = correlation.getSimilarDocs(id)
        for docId in similarDocs:
            related.append(searcher.documents[docId])
        print(similarDocs)
        return render_template("news.html", news=news, related=related)
    return render_template("index.html")


@app.route('/complete/<query>')
def start_complete(query):
    if query != "":
        candidates = searcher.getCompleteCandidate(query, 5)
    else:
        candidates = []
    return json.dumps(candidates)


if __name__ == '__main__':
    app.run()
