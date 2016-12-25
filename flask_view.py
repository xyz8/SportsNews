from flask import Flask, render_template, request
import handle_news
import indexer
import jieba
import searcher
import pickle
import correlation
import json
import math
import summery as sm

app = Flask(__name__)

jieba.initialize()
pageSize = 10
summery_wnd = 10


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
                results.append(searcher.documents[id].copy())
            resultCount = len(results)
            # 分页
            start = (page - 1) * pageSize
            end = (page) * pageSize
            results = results[start:end]
            pageDict = setPage(resultCount, page)

        sortClass = ['default', 'default', 'default']
        sortClass[int(order)] = 'primary'
        index = 0
        for result in results:
            summery = sm.get_summery(result['content'], summery_wnd, query)
            result['summery'] = sm.mark(summery, query)

            result['title'] = sm.mark(result['title'], query)
            result['content'] = sm.mark(result['content'], query)

        return render_template("results.html", results=results, related=related, resultCount=resultCount, sTime=sTime,
                               query=query, sortClass=sortClass, pageDict=pageDict, order=order, terms=terms)
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
    news = searcher.documents.get(id, 0).copy()

    if news != 0:
        related = []
        similarDocs = correlation.getSimilarDocs(id)
        for docId in similarDocs:
            related.append(searcher.documents[docId].copy())

        # print(similarDocs)
        return render_template("news.html", news=news, related=related)
    return render_template("index.html")

@app.route('/news/<id>/<query>')
def news_from_query(id,query):
    news = searcher.documents.get(id, 0).copy()
    news['title'] = sm.mark(news['title'], query)
    news['content'] = sm.mark(news['content'], query)

    if news != 0:
        related = []
        similarDocs = correlation.getSimilarDocs(id)
        for docId in similarDocs:
            related.append(searcher.documents[docId].copy())

        # mark
        for r in related:
            r['title'] = sm.mark(r['title'], query)
            r['content'] = sm.mark(r['content'], query)
        # print(similarDocs)
        return render_template("news.html", news=news, related=related, query=query)
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
