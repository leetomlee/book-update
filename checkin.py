# -*- coding: utf-8 -*-
import datetime
import random
import time
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED
import pymongo
# client = pymongo.MongoClient(host='192.168.3.9')
import requests
from bson import ObjectId
from lxml import etree
mongo_url = ""
user_agent_list = [
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1" \
    "Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11", \
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1092.0 Safari/536.6", \
    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1090.0 Safari/536.6", \
    "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/19.77.34.5 Safari/537.1", \
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.9 Safari/536.5", \
    "Mozilla/5.0 (Windows NT 6.0) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.36 Safari/536.5", \
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3", \
    "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3", \
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_0) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3", \
    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3", \
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3", \
    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3", \
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3", \
    "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3", \
    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.0 Safari/536.3", \
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24", \
    "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24"
]

import logging  # 引入logging模块

logging.basicConfig(level=logging.INFO)  # 设置日志级别




if(mongo_url == ""):
    mongo_url = input("链接地址：")
def getHTML(url):
    retry_count = 5
    while retry_count > 0:
        try:
            get = requests.get(url,
                               headers={"User-Agent": random.choice(user_agent_list)}, timeout=12)
            get.encoding = "utf-8"
            status = get.status_code
            if status != 200:
                raise Exception("request resource failed")
            html = etree.HTML(get.text)
            return html
        except Exception as e:
            logging.info("retry " + str(retry_count))
            retry_count -= 1
    return None


def get_books_from_db():
    find = bookDB.find({"hot": {"$gt": 0}, "status": {"$ne": "完结"}}, {"_id": 1, "link": 1,"book_name":1}).sort("hot",-1)
    cnt = 1
    jobs=[]
    ids=[]
    links=[]
    books=[]
    for f in find:
        try:
            link = str(f["link"])

            if link.__contains__("paoshuzw"):
                link=link.replace("paoshuzw.com","xbiquge.la",1)
            if link.__contains__("dwxdwx"):
                link=link.replace("dwxdwx.net","dwxdwx.com",1)
            ids.append(str(f["_id"]))
            links.append(link)
            books.append(str(f["book_name"]))
            #updateBook(str(f["_id"]),link)
            cnt += 1
            
        except Exception as e:
            logging.error(e)
            continue
            
    #wait(jobs, return_when=ALL_COMPLETED)
    for i in range(len(ids)):
        updateBook(ids[i],links[i])
        # time.sleep(2)
        logging.info("update "+str(books[i]))
        
    logging.info("update %s books" % str(cnt))


def updateBook(id, url):
    html = getHTML(url)
    if html is None:
        return "empty html"

    ids = []
    chps = chapterDB.find({"book_id": id}, {"chapter_name": 1})
    for chp in chps:
        ids.append(chp["chapter_name"])
    chapters = []
    if str(url).__contains__("dwxdwx"):
        for dd in html.xpath('//*[@id="list"]/dl/dt[2]/following-sibling::*'):
            if len(dd.xpath('a/@href')) > 0:
                s = dd.xpath('a/@href')[0]
                name = dd.xpath('a/text()')[0]
                if ids.__contains__(name):
                    continue
                chapter = {
                    'book_id': id,
                    'link': 'https://www.dwxdwx.net' + s,
                    'chapter_name': name}
                chapters.append(chapter)

    else:
        for dd in html.xpath("//*[@id='list']/dl/dd"):
            if len(dd.xpath('a/@href')) > 0:
                s = dd.xpath('a/@href')[0]
                name = dd.xpath('a/text()')[0]
                if ids.__contains__(name):
                    continue
                chapter = {
                    'book_id': id,
                    'link': 'http://www.xbiquge.la/' + s,
                    'chapter_name': name}
                chapters.append(chapter)
    try:
        if len(chapters) != 0:
            many = chapterDB.insert_many(chapters)
            logging.info("new add  " + str(len(many.inserted_ids)))
            logging.info("insert ok")

            update_time = html.xpath('//*[@id="info"]/p[3]/text()')[0]
            latest_chapter_name = html.xpath('//*[@id="info"]/p[4]/a/text()')[0]

            myquery = {"_id": ObjectId(id)}
            newvalues = {
                "$set": {"u_time": update_time, "last_chapter": latest_chapter_name}}

            bookDB.update_one(myquery, newvalues)
            logging.info("book info update " + str(id))
    except Exception as e:
        pass






if __name__ == '__main__':
    myclient1 = pymongo.MongoClient(mongo_url, connect=False)
    mydbDB = myclient1["book"]
    bookDB = mydbDB["books"]
    chapterDB = mydbDB["chapters"]  
    stime = datetime.datetime.now()
    logging.info("all update  " + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    get_books_from_db()
    logging.info("end update  " + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    etime = datetime.datetime.now()
    logging.info("used_time  " + str((etime - stime).seconds))
    myclient1.close()
