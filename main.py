# coding='utf-8'

import jieba as jieba
import json
import re
import cProfile
import time
import math


def doc2json(doc_file,json_file,num_of_doc=-1, debug = False):
    data = {}
    linenum = 0
    with open(doc_file, 'r', encoding='utf-8') as fp:
        jf = open(json_file, 'w')
        line = fp.readline()
        while line != '':

            if num_of_doc!= -1 and linenum >= num_of_doc:
                break
            if (debug):
                print(linenum, end=': ')
                print(line)

            elements = line.split("|")
            # docId
            data[str(linenum)]={
                            # url后缀
                            "postfix":elements[0],
                            # 标题
                            "title":elements[1],
                            # 来源 ect. 虎扑体育
                            "origin":elements[2],
                            # 报道时间
                            "reportdate":elements[3],
                            # 类别 etc. 足球新闻
                            "category":elements[4],
                            # url
                            "url":elements[5],
                            # 热度
                            "hot_dgree":elements[6],
                            # 关键字
                            "keyword":elements[7],
                            # 内容
                            "content":elements[8],
                            # 爬取时间
                            "craw_date":elements[9]
                            }
            line = fp.readline()
            linenum += 1
        # 文档集大小
        data['doc_len'] = linenum
        json.dump(data,jf,ensure_ascii=True)
        jf.close()



def getJson(json_file):
    jf = open(json_file,'r')
    data = json.load(jf)
    jf.close()
    return data



def tokenlize(document):
        cut_sult = jieba.cut_for_search(document)
        term_list = []
        for term in cut_sult:
            re.sub("[\s+\.\!\/_,$%^*(+\"\']+|[+——！，。？、~@#￥%……&*（）]+", "", term)
            if term !="":
                term_list.append(term)
        return term_list

# 构建倒排记录表
def set_ivs_index(documents ,threshold = 0,debug = False):
    term_id_frequeny_set = {}
    doc_len = documents['doc_len']
    for doc_id in range(doc_len):
        if debug:
            print("Reading doc No.%d: ",doc_id)
        doc = documents[str(doc_id)]["content"]

        # 词条化
        term_list = tokenlize(doc)

        # 填写词项、文档id、文档频率表
        for term in term_list:
            term_id_frequeny_set[term] = term_id_frequeny_set.get(term,{})
            term_id_frequeny_set[term][str(doc_id)] = term_id_frequeny_set[term].get(str(doc_id),0) + 1         # term frequency (TF)
    if debug:
        print("frequency_set: ",term_id_frequeny_set)

    # 获取词典部分
    terms = term_id_frequeny_set.keys()
    terms=sorted(terms)
    if debug:
        print("%d terms: "%len(terms),terms)
    dict = {}
    dict['terms'] = terms
    dict['doc_frequency'] = []
    rvs_record_table = []
    for term in terms:
        docs4term = term_id_frequeny_set[term].keys()                       # 当前词项对应的文档
        docs4term = sorted(docs4term)
        doc_frequency = len(docs4term)                                      # 当前此项的文档频率

        # 去停用词
        if threshold!=0 and doc_frequency > threshold:
            dict['terms'].remove(term)
            continue

        dict['doc_frequency'].append(doc_frequency)                                          # 填写词典部分
        rvs_record = []
        if debug:
            print("docs for '%s contains %d docs': "%(term,doc_frequency), docs4term)
        for doc in docs4term:
            rvs_record.append([doc,term_id_frequeny_set[term][doc]])        # 填写倒排记录,每一项是文档号和TF
        if debug:
            print("rvs_record: ",rvs_record)
        rvs_record_table.append(rvs_record)                                 # 填写倒排记录表
    return dict, rvs_record_table


# 持久化倒排记录表
def persist_rvs_index(dict,rvs_record_table, rvs_index_path ,threshold = 0, separator = '\t', debug = False):

    with open(rvs_index_path,'w',encoding="utf-8") as fp:
        terms = dict['terms']
        index = 0
        fp.write("词项id"+separator+"词项"+separator+"DF"+separator+"倒排记录表\n")
        for term in terms:
            line = ''
            if debug:
                print("正在构建第%d个索引"%index)
            line = str(index) + separator + term  + separator + str(dict['doc_frequency'][index]) + separator
            rvs_record = rvs_record_table[index]
            for record in rvs_record:
                    line +=  record[0] + separator + str(record[1]) + separator
            line.strip(separator)                                                   # 删除最后的分割符
            line += '\n'
            if debug:
                print(line)
            fp.write(line)
            index += 1


def analysize_data(origin_data, reformed_data, type = "json"):
    if type =='json':
        doc2json(origin_data, reformed_data)


def read_rvs_index(rvs_index_path):
    with open(rvs_index_path,'r',encoding='utf-8') as fp:
        fp.readline()                           # 过滤表头
        lines = fp.readlines()
        rvs_index_table = []
        terms = []
        terms_index = {}
        for line in lines:
            line = line.strip()
            table_row = line.split('\t')
            terms.append(table_row[1])
            terms_index[table_row[1]]=table_row[0]
            rvs_index_table.append(table_row)
        return rvs_index_table, terms, terms_index


def scroing(df,tf,doc_num,*,type="tf-idf"):
    type_set=['df','tf-idf','wf-idf']                         #可能的计分方式
    idf = math.log10(doc_num / df)
    if type not in type_set:
        print("Wrong type. Type must be in %s",type_set)
        exit()
    elif type.lower() == 'df':
        return df
    elif type.lower() == 'tf-idf':
        return tf*idf
    elif type.lower() == 'wf-idf':
        if tf > 0 :
            wf = 1 + math.log10(tf)
        else:
            wf = 0
        return wf * idf

# 按给定的评分标准给词做排序，低分可能是停用词
def find_stop_wd(rvs_index_table, terms, terms_index,doc_num,debug = False,*,type='df'):
    # 获取倒排记录
    type_set=['df','tf-idf','wf-idf']

    term_score_set = []
    # 按tf计算
    # for i in range(len(rvs_index_table)):
    #     term_score_set.append(int(rvs_index_table[i][0]))
    #     term_score_set.append(int(rvs_index_table[i][2]))

    for i in range(len(rvs_index_table)):
        term_score_set.append(int(rvs_index_table[i][0]))
        df = int(rvs_index_table[i][2])
        max_tf_idf = 0
        for j in range(3,len(rvs_index_table[i]),2):
            tf = int(rvs_index_table[i][j+1])
            score = scroing(df,tf,doc_num,type="tf-idf")
            if max_tf_idf < score:
                max_tf_idf = score
        term_score_set.append(max_tf_idf)
    for i in range(0,len(term_score_set),2):
        print("%.3f%%"%(i/len(term_score_set)*100))
        for j in range(i,len(term_score_set),2):
            if term_score_set[i+1] < term_score_set[j+1]:
                tmp_term, tmp_score  = term_score_set[j],term_score_set[j+1]
                term_score_set[j], term_score_set[j + 1] = term_score_set[i],term_score_set[i+1]
                term_score_set[i], term_score_set[i + 1] = tmp_term, tmp_score



    with open("terms_sorted_by_tf-idf.txt",'w',encoding='utf-8') as fp:
        for i in range(0,len(term_score_set),2):
            line = "%s\t%s\t%s\n"%(term_score_set[i],terms[term_score_set[i]],term_score_set[i+1])
            if debug:
                print(line,end='')
            fp.write(line)


def search(query, rvs_index_table, terms, terms_index,debug = False):
    search_start = time.time()               #查询开始计时
    query_terms = tokenlize(query)
    query_results = []                       # 搜索结果
    record_match_merge = []                  # 匹配的record合并结果
    query_match_terms = []                   # 匹配的词项

    # 查询词汇
    for query_term in query_terms:
        if query_term in terms:
            query_match_terms.append(query_term)

    # query_match_terms = list(set(query_terms)&set(terms))   # 匹配的词项，太慢，弃用

    if debug:
        print("terms: )",terms)
        print("query_terms: ",query_terms)
        print("query_match_terms: ",query_match_terms)
    if query_match_terms == []:
        query_results.append('No related news.')
    elif len(query_match_terms) == 1:
        query_match_term = query_match_terms[0]
        rvs_record = rvs_index_table[int(terms_index[query_match_term])]
        record_match = rvs_record[3:]     # 只有一个不需要合并
        record_match_merge = record_match

        if debug:
            print("For match Doc_id %s: "%terms_index[query_match_term],end='')
            print("the match records are :",record_match)
    # 多个匹配记录的合并
    else:
        query_match_terms_len = len(query_match_terms)
        term_count = 1
        # 第一个记录
        rvs_record = rvs_index_table[int(terms_index[query_match_terms[0]])]
        record_match1= rvs_record[3:]
        # 依次与后边合并
        for term_count in range(query_match_terms_len):
            record_match_merge = []
            rvs_record = rvs_index_table[int(terms_index[query_match_terms[term_count]])]
            record_match2 = rvs_record[3:]
            index1 = 0
            index2 =0

            # 合并record_match1与record_match2的结果到record_match1
            while index1 < len(record_match1) and index2 < len(record_match2):
                if record_match1[index1]<record_match2[index2]:
                    index1 += 2
                    continue
                elif record_match1[index1]>record_match2[index2]:
                    index2 += 2
                    continue
                else:
                    record_match_merge.append(record_match1[index1])
                    record_match_merge.append(record_match1[index1+1])
                    index1 += 2
                    index2 += 2
            record_match1 = record_match_merge

            term_count += 1
    if debug:
        print("record_match_merge: ", record_match_merge)
    record_match_merge_len = len(record_match_merge)//2
    match_count = 0
    for match_count in range(record_match_merge_len):
        match_doc_id = record_match_merge[match_count*2]
        query_results.append(match_doc_id)
        match_count += 1

    search_end = time.time()
    print("Search time: ",(search_end - search_start))
    return query_results

def present_search_results(query_results,documents,debug = False):
    # 把结果写成html
    html_results = "<ul>"
    for query_result in query_results:
        match_doc_title = documents[query_result]['title']
        match_doc_content = documents[query_result]['content']
        match_doc_url = documents[query_result]['url']
        html_results += "<tr><a href=" + match_doc_url + '>' + match_doc_title + "</a></tr>" \
                                                                                 "<tr><p>" + match_doc_content + "</p></tr>"
    html_results += "</ul>"
    if debug:
        print("Search results are as follows: \n", html_results)
    with open("search_results.html", 'w', encoding='utf-8') as fp:
        fp.write(html_results)
    return query_results

def main():
    jieba.initialize()
    doc2json("hupu_news.txt", "json_file.txt")
    doc = getJson("json_file.txt")

    query = " "
    rvs_index_path = 'rvs_index.txt'
    rvs_index_table, terms, terms_index = read_rvs_index(rvs_index_path)
    # find_stop_wd(rvs_index_table, terms, terms_index,doc_num=int(doc['doc_len']), debug=True)
    query_results = search(query, rvs_index_table, terms, terms_index,debug=False)
    present_search_results(query_results,doc,debug = False)

    # # cProfile.run("search(query, rvs_index_path, doc)")
    # dict, rvs_record_table = set_ivs_index(doc ,threshold = 0,debug = False)
    # persist_rvs_index(dict,rvs_record_table, "rvs_index.txt", debug=True)

if __name__ == "__main__":
    main()
