# coding=utf-8
import re
import jieba
from numpy import argsort
from searcher import tokenlize

# 返回一个列表，表中的元素有三元组（句子，句子开始位置，句子结束位置）构成
def get_sentences(doc):
    delimiter = '\r\n，。？！；'
    white_space = '\t '
    sentences = []
    sentence = ''
    newline_index = 0
    endline_index = newline_index
    for index in range(len(doc)):
        if doc[index] in delimiter:
            if index > 0 and doc[index - 1] not in delimiter:
                endline_index = index
            # 遇到最后一个分隔符或者文档下一个字符不是分隔符，开始组装新行
            if index == len(doc) - 1 or doc[index + 1] not in delimiter:
                sentences.append((sentence, newline_index, endline_index))
                sentence = ''
            index += 1
        elif doc[index] not in white_space:
            sentence += doc[index]
            # 遇到第一个字符或者上一个字符是分隔符，标记新行开始
            if index == 0 or doc[index - 1] in delimiter:
                newline_index = index
            if index == len(doc) - 1:
                endline_index = index + 1
                sentences.append((sentence, newline_index, endline_index))
            index += 1
        else:
            index += 1
    return sentences


# 从wnd_size大小的窗口（最小单元为句子）中寻找包含查询词最多的一部分
def get_summery(doc, wnd_size, query):
    terms = jieba.cut(query)
    terms = list(set(terms))
    sentences = get_sentences(doc)
    len_sentences = len(sentences)
    if wnd_size > len_sentences:
        wnd_size = len_sentences

    term_posionts = []
    for sent_id in range(len_sentences):
        term_posiont = []
        for term in terms:
            term_start = sentences[sent_id][0].find(term)
            while term_start != -1:
                term_end = term_start + len(term)
                flag = True
                for p in term_posiont:
                    if (p[0] <= term_start and p[1] > term_start) or (p[0] < term_end and p[1] >= term_end) or (
                                    p[0] >= term_start and p[1] <= term_end):
                        flag = False
                if flag:
                    term_posiont.append((term_start, term_end))

                term_start = sentences[sent_id][0].find(term, term_end)

        term_posionts.append(term_posiont)
    # 窗口数目
    len_wnd = len_sentences - wnd_size + 1
    wnd_values = []
    for wnd_index in range(len_wnd):
        value = 0
        for sent in range(wnd_size):
            value += len(term_posionts[wnd_index + sent])
        wnd_values.append(value)

    # 获取具有最多term的窗口号
    wnd_max_val = list(argsort(wnd_values))[-1]

    sum_start = sentences[wnd_max_val][1]
    sum_end = sentences[wnd_max_val + wnd_size - 1][2]
    sum_end = sum_end + 1 if len(doc) > sum_end else sum_end

    summery = doc[sum_start:sum_end]
    # if len(summery)>100:
    #     summery = summery[:100]

    if wnd_max_val > 0:
        summery = "...，" + summery
    if wnd_max_val + wnd_size < len(sentences):
        summery += "..."

    return summery


def mark(doc, query):
    positions = []
    terms = tokenlize(query)
    mark = ""
    for term in terms:
        start = doc.find(term)
        while start != -1:
            end = start + len(term)
            flag = True
            for p in positions:
                if (p[0] <= start and p[1] > start) or (p[0] < end and p[1] >= end) or (p[0] >= start and p[1] <= end):
                    flag = False
            if flag:
                positions.append((start, end))
            start = doc.find(term, end)

    if positions != []:
        positions = sorted(positions, key=lambda x: x[0])
        pre_end = 0
        for p in positions:
            mark += doc[pre_end:p[0]]
            mark += "<span class='marked'>" + doc[p[0]:p[1]] + "</span>"
            pre_end = p[1]
        mark += doc[pre_end:]
    else:
        mark = doc
    return mark


if __name__ == "__main__":
    summery_wnd = 10
    doc = "詹姆斯-哈登发布个人专属标志"
    query = "詹姆斯 哈登"
    summery = get_summery(doc, summery_wnd, query)

    print(summery)
    print(mark(doc, list(set(jieba.cut(query)))))
