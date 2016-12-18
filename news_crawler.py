# coding=utf-8

import requests
from bs4 import BeautifulSoup
import urllib
import json
import re
import time
import getopt
import sys

# 待访问的URL
urls = set()

# 已访问的URL
visited = set()

s = requests.Session()


class News(object):
    id = ''
    title = ''
    content = ''
    time = ''
    source = ''
    type = ''
    url = ''
    hot = 0
    keyword = ''
    collect = ''

    def toJson(self):
        data = {}
        data['id'] = self.id
        data['title'] = self.title
        data['origin'] = self.source
        data['report_date'] = self.time
        data['category'] = self.type
        data['url'] = self.url
        data['hot'] = self.hot
        data['keyword'] = self.keyword
        data['content'] = self.content
        data['crawl_date'] = self.collect
        data = dict(sorted(data.items(), key=lambda x: x[0]))
        return json.dumps(data)

    def save(self, fileName=None):
        if fileName == None:
            if self.source == "虎扑体育":
                fileName = "hupu_news.txt"
            elif self.source == "新浪体育":
                fileName = "sina_news.txt"
            elif self.source == "搜狐体育":
                fileName = "sohu_news.txt"
            elif self.source == "腾讯体育":
                fileName = "qq_news.txt"
            else:
                print("需要指定保存的文件")
                return
        with open(fileName, 'a', encoding='utf-8') as file:
            file.write(self.toJson() + "\n")

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


# 寻找当前页面中符合条件的链接
def findUrlsInHtml(html, source):
    if source == "qq" or source == "腾讯":
        reg = r'http://sports.qq.com/a/\d+/\d+.htm'
    elif source == "hupu" or source == "虎扑":
        reg = r'http://voice.hupu.com/.+?/\d+.html'
    elif source == "sina" or source == "新浪":
        reg = r'http://sports.sina.com.cn/.+?/doc-i\w+.shtml'
    elif source == "sohu" or source == "搜狐":
        reg = r'http://sports.sohu.com/\d+/n\d+.shtml'
    else:
        return
    match = re.compile(reg).findall(html)
    for m in match:
        urls.add(m)


def openUrl(url, source):
    if source == "hupu" or source == "虎扑":
        r = urllib.request.urlopen(url).read()
        html = r.decode()
    else:
        r = s.get(url)
        if source == "sina" or source == "新浪":
            r.encoding = 'utf-8'
        if source == "sohu" or source == "搜狐":
            r.encoding = 'gbk'
        if source == "sohu" or source == "搜狐":
            r.encoding = 'gbk'
        html = r.text
    return html


# 访问页面
def visit(source, show=True, fileName=None):
    # 从待访问集合中取出一条
    url = urls.pop()
    if url in visited:
        return

    html = openUrl(url, source)

    findUrlsInHtml(html, source)
    news = getNews(html, url, source)
    if news != None:
        news.save(fileName)
        if show:
            print(news)
    # 加入已访问url列表
    visited.add(url)


def getNews(html, url, source):
    news = News()
    # 网址
    news.url = url
    # 采集时间
    news.collect = time.strftime("%Y-%m-%d %H:%M", time.localtime())
    bsObj = BeautifulSoup(html, "html.parser")

    if source == "hupu" or source == "虎扑体育":
        # 来源
        news.source = "虎扑体育"
        # id
        reg = r'http://voice.hupu.com/.*/(\d+).html'
        match = re.compile(reg).match(url)
        if match:
            news.id = "hupu_%s" % match.group(1)
        # 新闻标题
        titleSoup = bsObj.find("div", {"class": "artical-title"})
        if titleSoup == None:
            return None
        news.title = titleSoup.h1.get_text().strip()
        # 新闻时间
        news.time = bsObj.find("a", {"class", "time"}).get_text().strip()[:16]
        # 关键字
        keyword = []
        keySoup = bsObj.find("div", {"class": "relatedTag"})
        if keySoup != None:
            for a in keySoup.find_all("a"):
                str = a.get_text()
                if str.find("-") >= 0:
                    keyword.append(str.split("-")[-1:][0])
                else:
                    keyword.append(str)
        news.keyword = " ".join(keyword)
        # 正文
        paras = []
        for p in bsObj.find("div", {"class": "artical-main-content"}).find_all("p"):
            paras.append("".join(p.get_text().strip().split()))
        content = "".join(paras)
        if content.find("\n") > 0:
            return None
        if len(content) < 100:
            return None
        news.content = content
        # 热度
        hotSpan = bsObj.find("span", {"class", "J_voice_comment_total_num"})
        if not hotSpan == None:
            hot = int(hotSpan.get_text())
        else:
            hot = 0
        news.hot = hot * 16
        # 类型
        news.type = bsObj.find("div", {"class", "navPath-crumb"}).a.get_text()
        return news

    if source == "sina" or source == "新浪":
        # 来源
        news.source = "新浪体育"
        # id
        reg = r'http://sports.sina.com.cn/.*/doc-i(\w+).shtml'
        match = re.compile(reg).match(url)
        if match:
            newsId = match.group(1)  # fxyiayr9297208
            news.id = "sina_%s" % newsId
        # 新闻标题
        titleSoup = bsObj.find("h1", {"id": "artibodyTitle"})
        if titleSoup == None:
            return None
        news.title = titleSoup.get_text().strip()
        # 新闻时间
        timeStr = bsObj.find("div", {"class", "artInfo"}).span.get_text().strip()
        reg = r'(\d{4})年(\d{2})月(\d{2})日(\d{2}):(\d{2})'
        match = re.compile(reg).match(timeStr)
        if match:
            timeStr = "%s-%s-%s %s:%s" % (
                match.group(1), match.group(2), match.group(3), match.group(4), match.group(5))
            news.time = timeStr
        else:
            return None
        # 关键字
        keyword = bsObj.find("meta", {"name": "tags"}).get("content")
        if keyword.find("彩票") >= 0:
            return None
        news.keyword = " ".join(keyword.split(","))
        # 正文
        paras = []
        for p in bsObj.find("div", {"id": "artibody"}).find_all("p"):
            paras.append(p.get_text().strip())
        content = "".join(paras)
        if content.find("\n") >= 0:
            return None
        if len(content) < 100:
            return None
        news.content = content
        # 热度
        hotUrl = "http://comment5.news.sina.com.cn/page/info?format=json&channel=ty&newsid=comos-%s" % newsId
        hotJson = s.get(hotUrl).text
        reg = r'"show": (\d+)}'  # 评论数
        match = re.compile(reg).search(hotJson)
        if match:
            hot = int(match.group(1))
        else:
            hot = 0
        news.hot = hot * 2
        # 类型
        category = bsObj.find("div", {"class", "blkBreadcrumbLink"}).find_all("a")[1].get_text()
        if category.find("-") > 0:
            news.type = category.split("-")[0]
        else:
            news.type = category.replace("频道", "")
        if news.type.find("彩票") >= 0:
            return None
        return news

    if source == "sohu" or source == "搜狐":
        # 来源
        news.source = "搜狐体育"
        # id
        reg = r'http://sports.sohu.com/\d+/n(\d+).shtml'
        match = re.compile(reg).match(url)
        if match:
            news.id = "sohu_%s" % match.group(1)
        # 新闻标题
        soup = bsObj.find("div", {"class": "content-box clear"})
        if soup == None: return None
        news.title = soup.h1.get_text().strip()
        # 新闻时间
        news.time = bsObj.find("div", {"class", "time-source"}).div.get_text().strip()[:16]
        # 关键字
        news.keyword = bsObj.find("meta", {"name": "keywords"}).get("content")
        # 类型
        news.type = '体育'
        # 正文
        paras = []
        for p in bsObj.find("div", {"id": "contentText"}).find_all("p"):
            paras.append("".join(p.get_text().strip().split()))
        content = "".join(paras)
        if content.find("\n") > 0:
            return None
        if len(content) < 100:
            return None
        news.content = content
        # 热度
        hotJson = s.get("http://changyan.sohu.com/api/3/topic/liteload?client_id=cyqemw6s1&topic_url=%s" % url).text
        hot = int(json.loads(hotJson)['cmt_sum'])
        news.hot = hot * 15
        return news

    if source == "qq" or source == "腾讯":

        # 只抓取以下类别的新闻
        types = {"NBA": "NBA", "CBA职业联赛": "CBA", "中超": "中超", "中甲": "中超", "中国国家队": "国足",
                 "英超": "英超", "西甲": "西甲", "德甲": "德甲", "意甲": "意甲", "乒乓球": "乒乓球", "跑步": "跑步",
                 "田径": "田径", "欧冠联赛": "欧冠", "游泳&跳水": "综合体育", "赛车": "综合体育",
                 "功夫搏击": "综合体育", "体操": "综合体育", "冰雪": "综合体育", "国青": "国足",
                 "五洲足坛": "国际足球", "2018世界杯预选赛": "国际足球", "2016欧洲杯": "国际足球", "亚冠": "中超"}

        news.source = "腾讯体育"

        # 新闻标题
        soup = bsObj.find("div", {"class": "hd"})
        if soup == None: return None
        if soup.h1 == None: return None
        news.title = soup.h1.get_text().strip()

        # 新闻时间
        timeSoup = bsObj.find("span", {"class", "a_time"})
        if timeSoup == None:
            return None
        news.time = timeSoup.get_text().strip()
        # 关键字
        soup = bsObj.find("div", {"bosszone": "keyword"})
        if soup != None:
            news.keyword = " ".join([a.get_text() for a in soup.find_all("a")])
        # 类型
        soup = bsObj.find("span", {"bosszone": "ztTopic"})
        if soup == None:
            return None
        type = soup.get_text()
        if type in types.keys():
            news.type = types[type]
        else:
            return None
        # 正文
        paras = []
        for p in bsObj.find("div", {"class": "Cnt-Main-Article-QQ"}).find_all("p"):
            if p.find_all("script") != None:
                for aa in p.find_all("script"):
                    aa.clear()
            if p.find_all("style") != None:
                for aa in p.find_all("style"):
                    aa.clear()
            if p.find("div", {"class": "rv-top"}) != None:
                p.find("div", {"class": "rv-top"}).clear()
            if p.find("div", {"class": "rv-player-wrap"}) != None:
                p.find("div", {"class": "rv-player-wrap"}).clear()
            if p.find("div", {"class": "rv-playlist"}) != None:
                p.find("div", {"class": "rv-playlist"}).clear()
            paras.append("".join(p.get_text().strip().replace("\n", " ").split()))
        content = "".join(paras)
        if content.find("\n") > 0:
            return None
        if len(content) < 100:
            return None
        news.content = content
        # 热度 新闻id
        reg = r"cmt_id='(\d+)';"
        match = re.compile(reg).search(html)
        if match:
            cmtId = match.group(1)
        reg = r"cmt_id = (\d+);"
        match = re.compile(reg).search(html)
        if match:
            cmtId = match.group(1)
            news.id = "qq_%s" % match.group(1)
        else:
            return None
        if cmtId != None:
            r = urllib.request.urlopen("http://coral.qq.com/article/%s/commentnum" % cmtId).read().decode()
            reg = r'"commentnum":"(\d+)"'
            match = re.compile(reg).search(r)
            if match:
                news.hot = int(match.group(1))
        return news


# 从已抓取的文件中获得url集合
def getCrawedList(source):
    # 待添加
    pass



def start(source):
    hupuSeed = ['http://www.hupu.com/', 'http://voice.hupu.com/sports', 'http://voice.hupu.com/cba',
                'http://voice.hupu.com/china', 'http://voice.hupu.com/nba', 'http://voice.hupu.com/soccer']
    sinaSeed = ['http://sports.sina.com.cn/', 'http://sports.sina.com.cn/nba/', 'http://sports.sina.com.cn/others/', \
                'http://sports.sina.com.cn/china/', 'http://sports.sina.com.cn/global/',
                'http://sports.sina.com.cn/cba/']
    qqSeed = ['http://sports.qq.com/', 'http://sports.qq.com/nba/', 'http://sports.qq.com/cba/',
              'http://sports.qq.com/isocce/', 'http://sports.qq.com/csocce/csl/''http://sports.qq.com/others/',
              'http://sports.qq.com/premierleague/']
    sohuSeed = ['http://sports.sohu.com/', 'http://sports.sohu.com/scroll/', 'http://sports.sohu.com/guoneizuqiu.shtml',
                'http://sports.sohu.com/lanqiu.shtml', 'http://sports.sohu.com/guojizuqiu.shtml',
                'http://sports.sohu.com/zonghe.shtml']

    dict = {"sohu": sohuSeed, "搜狐": sohuSeed, "hupu": hupuSeed, "虎扑": hupuSeed, "qq": qqSeed, "腾讯": qqSeed,
            "新浪": sinaSeed, "sina": sinaSeed}
    for url in dict[source]:
        html = openUrl(url, source)
        findUrlsInHtml(html, source)

    while len(urls) > 0:
        print("\n%d 条新闻待抓取...\n" % len(urls))
        try:
            visit(source)
        except Exception:
            print("跳过错误...")
            time.sleep(1)


if __name__ == '__main__':
    start("sohu")
