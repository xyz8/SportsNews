# coding=utf-8
import requests
from bs4 import BeautifulSoup
import urllib
import re
import time

urls = set()
visited = set()
s = requests.Session()


class News():
    id = ''
    title = ''
    content = ''
    time = ''
    source = ''
    type = ''
    url = ''
    hot = ''
    keyword = ''
    collect = ''

    def save(self):
        line = "%s|%s|%s|%s|%s|%s|%s|%s|%s|%s\n" \
               % (self.id, self.title, self.source, self.time, self.type, \
                  self.url, self.hot, self.keyword, self.content, self.collect)
        with open("hupu_news.txt", 'a', encoding='utf-8') as file:
            file.write(line)

    def __str__(self):
        lines = []
        lines.append("标题：%s" % self.title)
        lines.append("id：%s" % self.id)
        lines.append("时间：%s" % self.time)
        lines.append("来源：%s" % self.source)
        lines.append("类型：%s" % self.type)
        lines.append("网址：%s" % self.url)
        lines.append("正文：%s" % self.content)
        lines.append("热度：%s" % self.hot)
        lines.append("关键字：%s" % self.keyword)
        lines.append("收集时间：%s" % self.collect)
        return "\n".join(lines)


def findLinks(startUrls):
    for url in startUrls:
        r = urllib.request.urlopen(url).read()
        getLink(r)


def getLink(html):
    reg = r'(http://voice.hupu.com/\w+/\d+.html)'
    pattern = re.compile(reg)
    bsObj = BeautifulSoup(html, "html.parser").find_all("a")
    for a in bsObj:
        href = a.get("href")
        if href == None:
            continue
        match = pattern.match(href)
        if match:
            print(href)
            urls.add(match.group(1))


def visit():
    url = urls.pop()

    if url in visited:
        return

    r = urllib.request.urlopen(url).read()
    html = r
    getLink(html)
    getNews(html, url)
    visited.add(url)


def getNews(html, url):
    print(url)

    news = News()

    # 网址
    news.url = url
    # 来源
    news.source = "虎扑体育"
    # id
    reg = r'http://voice.hupu.com/.*/(\d+).html'
    match = re.compile(reg).match(url)
    if match:
        news.id = "hupu_%s" % match.group(1)

    bsObj = BeautifulSoup(html, "html.parser")

    # 新闻标题
    news.title = bsObj.find("div", {"class": "artical-title"}).h1.get_text().strip()

    # 新闻时间
    news.time = bsObj.find("a", {"class", "time"}).get_text().strip()

    # 关键字
    news.keyword = bsObj.find("meta", {"http-equiv": "Keywords"}).get("content")

    # 正文
    paras = []
    for p in bsObj.find("div", {"class": "artical-main-content"}).find_all("p"):
        paras.append("".join(p.get_text().strip().split()))
    news.content = "".join(paras)

    # 热度
    hotSpan = bsObj.find("span", {"class", "J_voice_comment_total_num"})
    if not hotSpan == None:
        news.hot = hotSpan.get_text()
    else:
        news.hot = '0'

    # 类型
    news.type = bsObj.find("div", {"class", "navPath-crumb"}).a.get_text()

    # 采集时间
    news.collect = time.strftime("%Y-%m-%d %H:%M", time.localtime())
    print(news)
    news.save()


if __name__ == '__main__':

    startUrls = ['http://voice.hupu.com/sports', \
                 'http://voice.hupu.com/cba', \
                 'http://voice.hupu.com/china', \
                 'http://voice.hupu.com/nba', \
                 'http://voice.hupu.com/soccer',\
                 'http://www.hupu.com/']
    findLinks(startUrls)

    with open("hupu_news.txt", encoding="utf-8") as file:
        lines = file.readlines()

    visited = set(map(lambda x: x.split("|")[5], lines))

    while len(urls) > 0:
        try:
            print(len(urls))
            visit()
        except Exception:
            time.sleep(20)
