
#-*- coding:UTF-8 -*-
import sys
# reload(sys)
# sys.setdefaultencoding('utf8')
import BeautifulSoup
import urllib, urllib2
import zipfile,gzip,io,StringIO,zlib
import json
import redis
import time
import tornado.httpserver
import tornado.ioloop
import tornado.iostream
import tornado.web
import tornado.httpclient
import requests
import pymongo
import hashlib


reload(sys)
sys.setdefaultencoding('utf-8')

baseline = ''
cList = ['%E4%B8%8A%E6%B5%B7','%e6%9d%ad%e5%b7%9e','%e5%8c%97%e4%ba%ac']
testurl = 'http://api.miaotu.net/v2/yueyou/search?count=20&keywords=%s'

# +%s
end = '&latitude=30.898888&longitude=121.905973&page=%s&token=5e81b50f-ee12-11e6-b983-00163e002e59'
# testurl = 'http://api.miaotu.net/v2/yueyou/search?count=20&keywords=%E4%B8%8A%E6%B5%B7&latitude=30.898888&longitude=121.905973&page=1&token=5e81b50f-ee12-11e6-b983-00163e002e59'
# testurl = 'http://www.example.com/'
db = redis.StrictRedis(host='210.22.106.178', port=2003)
miaotuURl = '/v2/yueyou/search?count=20&keywords=%E4%B8%8A%E6%B5%B7&latitude=30.898927&longitude=121.905984&page=1&token=5e81b50f-ee12-11e6-b983-00163e002e59 HTTP/1.1'
'''
GET /v2/yueyou/search?count=20&keywords=%E4%B8%8A%E6%B5%B7&latitude=30.898927&longitude=121.905984&page=1&token=5e81b50f-ee12-11e6-b983-00163e002e59 HTTP/1.1
Host: api.miaotu.net
Connection: keep-alive
Accept: */*
User-Agent: miaotu/1.0.2 (iPhone; iOS 9.3.5; Scale/2.00)
Accept-Language: zh-Hans-CN;q=1
Accept-Encoding: gzip, deflate
Connection: keep-alive
'''
headers = {
            'user-agent': 'miaotu/1.0.2 (iPhone; iOS 9.3.5; Scale/2.00)',
            'Host': 'api.miaotu.net',
            'Accept': '*/*',
            'Accept-Language': 'zh-Hans-CN;q=1',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
           }


def requestClient(url, monconn):
    print 'start request---'
    proxies = {"http": "http://127.0.0.1:8888"}
    # requests.get("http://example.org", proxies=proxies)
    r = requests.get(url, headers=headers, proxies=proxies)
    data = r.text
    # oData = r.json
    # print type(data)
    # print type(oData)
    jData = json.loads(data)
    listData = jData['Items']
    num = 0
    for item in jData['Items']:
        ret = monconn.insert(item)
        num = num + ret
    if num == 0:
        return False, 0
    if len(listData) < 5:
        return False, 1
    else:
        return True, 1
    # print jData['Items'][0]['Uid']
    # print jData['Items'][0]['Created']
    # monconn.insert(jData)

'''
"mongo_config":
    {
        "host"       : "106.14.135.47",
        "port"       : 27017,
        "database"   : "wenda"
    }
'''

class pagedbLogic(object):

    def __init__(self):
        self.connection = pymongo.MongoClient('106.14.135.47', 27017)
        self.database = self.connection['wenda']
        # self.collection = None
        self.collection = self.database["shtest"]

    def update(self, doc_item):
        _id = self.get_primary_key(doc_item)
        if self.collection.find_one({'_id': _id}):
            # 存在则更新
            self.collection.update({'_id': _id}, {'$set':doc_item}, upsert=True)
        else:
            return False, 'primary_key [' + _id + '] NOT exists.'
        return True, 'OK'

    def delete(self, doc_item):
        # 找出主键
        _id = self.get_primary_key(doc_item,)
        # 判断主键是否存在
        if self.collection.find_one({'_id': _id}):
            # 存在则删除
            self.collection.remove({'_id': _id})
        else:
            return False, 'primary_key [' + _id + '] NOT exists.'
        return True, 'OK'

    def insert(self, doc_item, upsert = False):
        # 找出主键
        # print jData['Items'][0]['Uid']
        # print jData['Items'][0]['Created']
        # _id = self.get_primary_key(doc_item)
        _id = doc_item['Uid'] + '_' + doc_item['Created']
        print '_id:%s' %_id
        # 判断主键是否存在
        if self.collection.find_one({'_id': _id}):
            # 存在则更新
            # if upsert:
            #     self.collection.update({'_id': _id}, {'$set':doc_item}, upsert=True)
            #     return True, 'primary_key [' + _id + '] upsert OK.'
            # else:
            #     return False, 'primary_key [' + _id + '] already exists.'
            return 0
        else:
            doc_item['_id'] = _id
            self.collection.insert(doc_item)
            return 1

    def select(self, doc_id):
        return self.collection.find_one({'_id': str(doc_id)})

    def get_primary_key(self, doc_item,):
        assert doc_item.has_key('url')
        #print '[%s]' % doc_item['url']
        _id = hashlib.md5(doc_item['url']).hexdigest()
        table_name = doc_item['host'].replace('.', '_').replace('-', '_')
        self.collection = self.database[table_name]
        return str(_id)


def main():
    ip = '127.0.0.1'
    port = 8888
    # test_proxy(testurl, ip, port, timeout=5)
    # tornadoReq()
    # html = http_get(testurl)
    mon = pagedbLogic()
    for cItem in cList:
        cURL = testurl%cItem
        for count in range(1, 2000):
            cDate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime(time.time()))
            addr = end%count
            url = cURL + addr
            print "%s, url:%s" % (cDate, url)
            ret,check = requestClient(url, mon)
            if check == 0:
                print 'no new msg---------------------'
                # break
            if not ret:
                print "--------end---,pages:%s"%count
                break
            time.sleep(5)


    # requestClient(testurl)
    # rr = db.zadd('proxy', 4, '%s:%s' % ('106.114.135.47', '3122'))
    # print rr
    # exit()
    # test_proxy(testurl, '119.28.194.66', '8888')
    # exit()
    # start = time.time()
    # cDate = time.strftime("%Y/%m/%d %H:%M", time.localtime(time.time()))
    # url1 = 'http://www.xici.net.co/nn/%s'
    # url2 = 'http://www.xici.net.co/nt/%s'
    # url3 = 'http://www.xici.net.co/wt/%s'
    # url4 = 'http://www.xici.net.co/wn/%s'
    #
    # # kuaiUrl = 'https://www.kuaidaili.com/free/inha/%s'
    # url = []
    # # url.append(kuaiUrl)
    # url.append(url1)
    # url.append(url2)
    # url.append(url3)
    # url.append(url4)
    # for count in range(1, 720):
    #     for item in url:
    #         addr = item%count
    #         print "%s, days:%s, url:%s" % (cDate, days, addr)
    #         html = http_get(addr)
    #         parseToRedis(html)
            # parseKuaiToRedis(html)

        #         # print >>ofile, '%s:%s' % (ip['ip'], ip['port'])
    # ofile.close()


if __name__ == '__main__':
    # sysTime = time.strftime("%Y/%m/%d %H:%M", time.localtime(time.time()))
    # num = 1
    # while True:
        #sysTime = time.strftime("%Y/%m/%d %H:%M", time.localtime(time.time()))
        #print '---------%s,days:%s' % (sysTime, num)
    # main()
    while True:
        main()
        time.sleep(300)
        # num = num + 1

