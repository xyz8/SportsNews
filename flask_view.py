from flask import Flask, render_template, request
import handle_news
import indexer
import jieba
import searcher
import pickle
import correlation

app = Flask(__name__)

jieba.initialize()


@app.route('/query/<query>')
def search(query):
    # 排序方式 0相关性 1热度 2时间
    order = request.args.get('order', '0')

    if query != "":
        terms = searcher.tokenlize(query)

        if order == '0':
            docs, sTime = searcher.search(terms)
        elif order == '1':
            docs, sTime = searcher.searchByHot(terms)
        elif order == '2':
            docs, sTime = searcher.searchByTime(terms)
        results = []
        related = correlation.getSimilarWords(terms)
        for id in docs:
            results.append(searcher.documents[id])
        resultCount = len(results)
        if resultCount > 100:
            results = results[:100]
        return render_template("index.html", results=results, related=related, resultCount=resultCount, sTime=sTime,
                               query=query)
    return render_template("index.html")


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


if __name__ == '__main__':
    app.run()
