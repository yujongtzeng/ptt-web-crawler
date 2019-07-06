# -*- coding: utf-8 -*-

# to do: fix the page problem when keyword is present
from __future__ import absolute_import
from __future__ import print_function

import os
import re
import sys
import json
import requests
import argparse
import time
import codecs
from bs4 import BeautifulSoup
from six import u
import chardet

__version__ = '2.1'

# if python 2, disable verify flag in requests.get()
VERIFY = True
if sys.version_info[0] < 3:
    VERIFY = False
    requests.packages.urllib3.disable_warnings()


class PttWebCrawler(object):

    PTT_URL = 'https://www.ptt.cc'

    """docstring for PttWebCrawler"""
    def __init__(self, cmdline=None, as_lib=False):
        parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description='''
            A crawler for the web version of PTT, the largest online community in Taiwan.
            Input: board name and page indices (or articla ID)
            Output: BOARD_NAME-START_INDEX-END_INDEX.json (or BOARD_NAME-ID.json)
        ''')
        parser.add_argument('-b', metavar='BOARD_NAME', help='Board name', required=True)
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('-p', metavar=('START_PAGE', 'END_PAGE'), type=int, 
            nargs=2, help="Start(inclusive) and end(exclusive) PAGE")
        #group.add_argument('-d', metavar=('START_DAY', 'END_DAY'), type=int, 
        #    nargs=2, help="Start(inclusive) and end(exclusive) day as YYYYMMDD")
        # group.add_argument('-n', metavar=('START_NUMBER', 'END_NUMBER'), type=int, 
        #    nargs=2, help="Start(inclusive) and end(exclusive) article number on the board")
        group.add_argument('-a', metavar='ARTICLE_ID', help="Article ID")
        parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)
        parser.add_argument('-k', metavar=('KEYWORD'), help="Keyword required in the title")##
        
        if not as_lib:
            if cmdline:
                args = parser.parse_args(cmdline)
            else:
                args = parser.parse_args()
            board = args.b
            keyword = ''   ############## NEW
            if args.k:     
                keyword = args.k
                print(chardet.detect(keyword))
                print(keyword) 
                # it's okay with English 
                keyword = keyword.decode("utf-8")
                print(keyword)
                print(type(keyword))
                # print(keyword)
                # print(type(keyword))
                # print(chardet.detect(keyword))
            if args.p:
                start_page = args.p[0]
                if args.p[1] == -1:
                    end_page = self.getLastPage(board)
                else:
                    end_page = args.p[1]
                self.range_pages(start_page, end_page, board, keyword)    
            #if args.d:
            #    start_day = args.i[0]
            #    end_day = args.i[1]
            #    self.range_dates(args.i[0], args.i[1], board, keyword)    
            #if args.n:
            #    start_number = 
            else:  # args.a
                article_id = args.a
                self.parse_article(article_id, board)                         

    def range_pages(self, start_page, end_page, board, keyword = '', path='.', timeout=3):
        filename = board + '-p' + str(start_page) + '-' + str(end_page) + '-'+keyword+'.json'
        filename = os.path.join(path, filename) 
        self.store(filename, u'{"articles": [', 'w')
        parsed_res = self.parse_pages(start_page, end_page, board, keyword)
        self.store(filename, parsed_res[0], 'a')
        for i in range(1, len(parsed_res)):
            if parsed.res[i]:
                self.store(filename, ',\n' + parsed_res[i], 'a') 
        self.store(filename, u']}', 'a')            
        return filename
        
#    def range_numbers(self, start_num, end_num, board, keyword = '', path='.', timeout=3):
#        filename = board + '-n' + str(start_page) + '-' + str(end_page) + '-'+keyword+'.json'
#        filename = os.path.join(path, filename) 
#        start_page, start_index = (start_num-1)/20 +1, (start_num-1)%20
#        end_page = (end_num-1)/20 +1
#        self.store(filename, u'{"articles": [', 'w')
#        parsed_res = parse_pages(start_page, end_page, board, keyword)
#        self.store(filename, parsed_res[start_index], 'a')
#        for i in range(start_index+1, end_num-(start_page-1)*20):
#            self.store(filename, ',\n' + parsed_res[i], 'a') 
#        self.store(filename, u']}', 'a')                 
#        retur filename
        
#    def range_dates(self, start_day, end_day, board, keyword = '', path='.', timeout=3):
#        filename = board + '-d' + str(start_day) + '-' + str(end_day) + '-'+keyword+'.json'
#        filename = os.path.join(path, filename) 
#        # do a binary search for the start page and end page   
#        last_page = self.getLastPage(board)
#            board_url = self.PTT_URL + '/bbs/' + board + '/index' 
#            while first_page < last_page
#                middle_page = (first_page + last_page) /2
#                resp = get_request(board, middle_page, keyword, timeout)
#                if resp.status_code != 200:
#                    print('invalid url:', resp.url)
#                    continue
#                    soup = BeautifulSoup(resp.text, 'html.parser')
#                    divs = soup.find_all("div", "r-ent")
#                    href = div[0].find('a')['href']
#                    link = self.PTT_URL + href
#                    article_id = re.sub('\.html', '', href.split('/')[-1])
#                    date = self.get_date(board, article_id, keyword)  
#                    if date > end_day:
#                        end_page = middle_page
#                    href = div[19].find('a')['href']
#                    link = self.PTT_URL + href
#                    article_id = re.sub('\.html', '', href.split('/')[-1])
#                    date = self.get_date(board, article_id, keyword)   
#                    if date < start_day:
#                        start_page = middle_page +1
#            ..................######## unfinished here            
#            return filename

    def parse_article(self, article_id, board, path='.'):
        link = self.PTT_URL + '/bbs/' + board + '/' + article_id + '.html'
        filename = board + '-' + article_id + '.json'
        filename = os.path.join(path, filename)
        self.store(filename, self.parse(link, article_id, board), 'w')
        return filename

    # return a list of json, one element for each article     
    def parse_pages(self, start_page, end_page, board, keyword = '', path='.', timeout=3):            
        res = [] 
        for page_number in range(start_page, end_page):
            print('Processing index:', str(page_number))
            resp = get_request(board, page_number, keyword, timeout)
            if resp.status_code != 200:
                print('invalid url:', resp.url)
                continue
            soup = BeautifulSoup(resp.text, 'html.parser')
            divs = soup.find_all("div", "r-ent")
            for div in divs:
                try:
                    # ex. link would be <a href="/bbs/PublicServan/M.1127742013.A.240.html">Re: [問題] 職等</a>
                    href = div.find('a')['href']
                    link = self.PTT_URL + href
                    article_id = re.sub('\.html', '', href.split('/')[-1])
                    parsed_res = self.parse(link, article_id, board, keyword)                        
                    if parsed_res: 
                         res.append(parsed_res)
                except:   
                    res.append('')
                time.sleep(0.1)
        return res
            
    @staticmethod
    def parse(link, article_id, board, timeout=3):
        print('Processing article:', article_id)
        resp = requests.get(url=link, cookies={'over18': '1'}, verify=VERIFY, timeout=timeout)
        if resp.status_code != 200:
            print('invalid url:', resp.url)
            return json.dumps({"error": "invalid url"}, sort_keys=True, ensure_ascii=False)
        soup = BeautifulSoup(resp.text, 'html.parser')
        main_content = soup.find(id="main-content")
        metas = main_content.select('div.article-metaline')
        author = ''
        title = ''
        date = ''
        if metas:
            author = metas[0].select('span.article-meta-value')[0].string if metas[0].select('span.article-meta-value')[0] else author
            title = metas[1].select('span.article-meta-value')[0].string if metas[1].select('span.article-meta-value')[0] else title
            date = metas[2].select('span.article-meta-value')[0].string if metas[2].select('span.article-meta-value')[0] else date

            # remove meta nodes
            for meta in metas:
                meta.extract()
            for meta in main_content.select('div.article-metaline-right'):
                meta.extract()        
            
        # remove and keep push nodes
        pushes = main_content.find_all('div', class_='push')
        for push in pushes:
            push.extract()

        try:
            ip = main_content.find(text=re.compile(u'※ 發信站:'))
            ip = re.search('[0-9]*\.[0-9]*\.[0-9]*\.[0-9]*', ip).group()
        except:
            ip = "None"

        # 移除 '※ 發信站:' (starts with u'\u203b'), '◆ From:' (starts with u'\u25c6'), 空行及多餘空白
        # 保留英數字, 中文及中文標點, 網址, 部分特殊符號
        filtered = [ v for v in main_content.stripped_strings if v[0] not in [u'※', u'◆'] and v[:2] not in [u'--'] ]
        expr = re.compile(u(r'[^\u4e00-\u9fa5\u3002\uff1b\uff0c\uff1a\u201c\u201d\uff08\uff09\u3001\uff1f\u300a\u300b\s\w:/-_.?~%()]'))
        for i in range(len(filtered)):
            filtered[i] = re.sub(expr, '', filtered[i])

        filtered = [_f for _f in filtered if _f]  # remove empty strings
        filtered = [x for x in filtered if article_id not in x]  # remove last line containing the url of the article
        content = ' '.join(filtered)
        content = re.sub(r'(\s)+', ' ', content)
        # print 'content', content

        # push messages
        p, b, n = 0, 0, 0
        messages = []
        for push in pushes:
            if not push.find('span', 'push-tag'):
                continue
            push_tag = push.find('span', 'push-tag').string.strip(' \t\n\r')
            push_userid = push.find('span', 'push-userid').string.strip(' \t\n\r')
            # if find is None: find().strings -> list -> ' '.join; else the current way
            push_content = push.find('span', 'push-content').strings
            push_content = ' '.join(push_content)[1:].strip(' \t\n\r')  # remove ':'
            push_ipdatetime = push.find('span', 'push-ipdatetime').string.strip(' \t\n\r')
            messages.append( {'push_tag': push_tag, 'push_userid': push_userid, 'push_content': push_content, 'push_ipdatetime': push_ipdatetime} )
            if push_tag == u'推':
                p += 1
            elif push_tag == u'噓':
                b += 1
            else:
                n += 1

        # count: 推噓文相抵後的數量; all: 推文總數
        message_count = {'all': p+b+n, 'count': p-b, 'push': p, 'boo': b, "neutral": n}

        # print 'msgs', messages
        # print 'mscounts', message_count

        # json data
        data = {
            'url': link,
            'board': board,
            'article_id': article_id,
            'article_title': title,
            'author': author,
            'date': date,
            'content': content,
            'ip': ip,
            'message_count': message_count,
            'messages': messages
        }
        # print 'original:', d
        return json.dumps(data, sort_keys=True, ensure_ascii=False)
    
    ### NEW
    # page is the page number (after keyword search)
#    @staticmethod
#    def get_request(board, page, keyword = '', timeout = 3):
#        if keyword:
#            resp = requests.get(
#                url = self.PTT_URL + '/bbs/' + board + '/search', 
#                    params = {'q':keyword, 'page':page}, cookies={'over18': '1'}, 
#                    verify=VERIFY, timeout=timeout
#            )
#         else:
#             resp = requests.get(
#                 url = self.PTT_URL + '/bbs/' + board + '/index'+str(page)+'.html', 
#                    cookies={'over18': '1'}, verify=VERIFY, timeout=timeout
#            )
#         return resp
#    @staticmethod
#    def get_date(board, article_id, timeout=3)
#        link = self.PTT_URL + '/bbs/' + board + '/' + article_id + '.html'        
#        resp = requests.get(url=link, cookies={'over18': '1'}, verify=VERIFY, timeout=timeout)
#        if resp.status_code != 200:
#            print('invalid url:', resp.url)
#            return json.dumps({"error": "invalid url"}, sort_keys=True, ensure_ascii=False)
#        soup = BeautifulSoup(resp.text, 'html.parser')
#        main_content = soup.find(id="main-content")
#        metas = main_content.select('div.article-metaline')
#        date = ''
#        if metas:
#            date = metas[2].select('span.article-meta-value')[0].string 
#        if metas[2].select('span.article-meta-value')[0] else date
#        return date    

    @staticmethod
    def getLastPage(board, timeout=3, keyword = ''):
        content = requests.get(
            url= 'https://www.ptt.cc/bbs/' + board + '/index.html',
            cookies={'over18': '1'}, timeout=timeout
        ).content.decode('utf-8')
        content = get_request(board, page_number, keyword, timeout).content.decode('utf-8')
        ## firstpage.group[0] will be the oldest page
        ## firstpage.group[1] will be the page before the last page
        if keyword:
            first_page = re.search(r'href="/bbs/' + board + '/search?page=(\d+)">', content)
            return int(first_page.group(0))
        # no keyword        
        else:
            first_page = re.search(r'href="/bbs/' + board + '/index(\d+).html">&lsaquo;', content)
            if first_page is None:
                return 1
            return int(first_page.group(1)) + 1

    @staticmethod
    def store(filename, data, mode):
        with codecs.open(filename, mode, encoding='utf-8') as f:
            f.write(data)

    @staticmethod
    def get(filename, mode='r'):
        with codecs.open(filename, mode, encoding='utf-8') as f:
            return json.load(f)

if __name__ == '__main__':
    c = PttWebCrawler()
