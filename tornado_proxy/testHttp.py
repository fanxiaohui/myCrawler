
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

reload(sys)
sys.setdefaultencoding('utf-8')

baseline = ''
testurl = 'http://api.miaotu.net/v2/yueyou/search?count=20&keywords=%E4%B8%8A%E6%B5%B7&latitude=30.898888&longitude=121.905973&page=1&token=5e81b50f-ee12-11e6-b983-00163e002e59 HTTP/1.1\r\n'
# testurl = 'http://www.example.com/'
db = redis.StrictRedis(host='210.22.106.178', port=2003)


def http_get(url):
    url = urllib2.quote(url, ': /= & ?')
    request = urllib2.Request(url)
    # request.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8')
    request.add_header('Accept', '*/*')
    request.add_header('Accept-Encoding', 'gzip, deflate')
    request.add_header('Accept-Language', 'zh-Hans-CN;q=1')
    # request.add_header('host', 'api.miaotu.net')
    # request.add_header('Cache-Control', 'max-age=0')
    request.add_header('Connection', 'keep-alive')
    request.add_header('User-Agent', 'miaotu/1.0.2 (iPhone; iOS 9.3.5; Scale/2.00)')

    try:
        httpHandler = urllib2.HTTPHandler(debuglevel=1)
        httpsHandler = urllib2.HTTPSHandler(debuglevel=1)
        opener = urllib2.build_opener(httpHandler, httpsHandler)

        urllib2.install_opener(opener)
        response = urllib2.urlopen(request)
        html = response.read()
        # print response
        # print html
        # print response.getcode()
    except urllib2.URLError, e:
        print e.reason
    # html = response.read()
    # print html
    # return html
    # html = unicode(html, 'gb18030').encode('utf-8')
    # respHtml = zlib.decompress(html, 16 + zlib.MAX_WBITS)
    # return respHtml
    # respStream = StringIO.StringIO(html)
    # gf = gzip.GzipFile(fileobj=respStream)
    # gdata = gf.read()
    # print gdata
    # return gdata
    # return urllib2.urlopen(url).read()


def test_proxy(url, ip, port, timeout=5):
    try:
        proxy_handler = urllib2.ProxyHandler({'http': 'http://%s:%s/' % (ip, port)})
        opener = urllib2.build_opener(proxy_handler)
        opener.addheaders = [('User-Agent', 'miaotu/1.0.2 (iPhone; iOS 9.3.5; Scale/2.00)'),
                             ('Connection', 'keep - alive'),
                             ('Accept-Language', 'zh-Hans-CN;q=1'),
                             ('Accept-Encoding', 'gzip, deflate'),
                             ('Accept', '*/*')]

        print 'test porxy==='
        ret = opener.open(url, timeout=timeout)
        print ret.code
        resp = opener.open(url, timeout=timeout).read()
        # if ret.code == 200 and resp == 'Hello, world':
        print resp
            # print ret.url
            # return True
        # else:
        #     print ret.code
        #     return False
        # html = opener.open(url, timeout=timeout).read()
    except Exception, e:
        print e
        pass
    # return False


def parseToRedis(html):
    s = BeautifulSoup.BeautifulSoup(html)
    artiBlock = s.find('table', {'id': 'ip_list'})

    # for tr in s.select('table #ip_list tr')[1:]:
    for tr in artiBlock.findAll('tr')[1:]:
        # print tr
        ip = {}
        ip['ip'] = tr.findAll('td')[1].text
        ip['port'] = tr.findAll('td')[2].text
        ip['type'] = tr.findAll('td')[5].text
        # print '%s:%s %s' %(ip['ip'], ip['port'], ip['type'])
        if ip['type'].lower() == 'http' and test_proxy(testurl, ip['ip'], ip['port']):
            # print >>ofile, '%s:%s' % (ip['ip'], ip['port'])
            db.zadd('proxy', 0, '%s:%s' % (ip['ip'], ip['port']))


def parseKuaiToRedis(html):
    s = BeautifulSoup.BeautifulSoup(html)
    # print html
    artiBlock = s.find('table', {'class': 'table table-bordered table-striped'})

    # for tr in s.select('table #ip_list tr')[1:]:
    for tr in artiBlock.findAll('tr')[1:]:
        # print tr
        ip = {}
        ip['ip'] = tr.findAll('td')[0].text
        ip['port'] = tr.findAll('td')[1].text
        ip['type'] = tr.findAll('td')[3].text
        # print '%s:%s %s' %(ip['ip'], ip['port'], ip['type'])
        if test_proxy(testurl, ip['ip'], ip['port']):
            # print >>ofile, '%s:%s' % (ip['ip'], ip['port'])
            db.zadd('proxy', 0, '%s:%s' % (ip['ip'], ip['port']))


def tornadoReq():
    def handle_response(response):
        # print response.code, self.proxy, response.effective_url
        print '======================='
        print response.code, response.effective_url
        if response.code == 599:
            # self.set_status(504)
            # #mark proxy timeout
            # # self.redis_client.zincrby('proxy', self.proxy, -1)
            # self.finish()
            return

        if response.error and not isinstance(response.error,
                tornado.httpclient.HTTPError):
            print 'ser error'
        else:
            self.set_status(response.code)
            for header in ('Date', 'Cache-Control', 'Server',
                    'Content-Type', 'Location'):
                v = response.headers.get(header)
                if v:
                    self.set_header(header, v)
            # self.set_header('SNDA-Proxy', self.proxy)
            if response.body:
                print response.body
            #     m = md5.new()
            #     m.update(response.body)
            #     cachefile = file('%s/%s' % (CACHE_PATH, m.hexdigest()), 'w')
            #     cachefile.write(response.body)
            #     cachefile.close()
            #     self.write(response.body)
            # self.finish()

        lastproxy = ''
        connect_timeout = 3
        request_timeout = 3
        # if headers[SKIP_PROXY] in self.request.headers:
        #     lastproxy = self.request.headers[headers[SKIP_PROXY]]
        #     print 'skip:', lastproxy
        # if headers[CONNECT_TIMEOUT] in self.request.headers:
        #     connect_timeout = int(self.request.headers[headers[CONNECT_TIMEOUT]])
        # if headers[REQUEST_TIMEOUT] in self.request.headers:
        #     request_timeout = int(self.request.headers[headers[REQUEST_TIMEOUT]])

        # tmpproxy = self.choose_proxy(self.request.host, lastproxy).split(':')
        tmpproxy = ['pp', '//106.14.135.47', '3389']
        # body = self.request.body
        body = None
        # if self.request.method.lower() == "post":
        #     body = self.request.body
        # print body
        ua = "miaotu/1.0.2 (iPhone; iOS 9.3.5; Scale/2.00)"
        tornado.httpclient.AsyncHTTPClient.configure('tornado.curl_httpclient.CurlAsyncHTTPClient')
        req = tornado.httpclient.HTTPRequest(url=testurl, user_agent=ua,
                                            method='GET',
                                            body=body,
                                            # headers=self.request.headers,
                                            follow_redirects=False,
                                            connect_timeout=3, request_timeout=3,
                                            allow_nonstandard_methods=True,
                                            proxy_host=tmpproxy[1][2:], proxy_port=int(tmpproxy[2]))

        client = tornado.httpclient.AsyncHTTPClient()
        try:
            client.fetch(req, handle_response)
        except tornado.httpclient.HTTPError as e:
            if hasattr(e, 'response') and e.response:
                handle_response(e.response)
            else:
                print 'Internal server error2:%s\n' + str(e)
                # self.finish()
        except Exception,e:
            print 'Common Exception', e


def main():
    ip = '192.168.1.11'
    port = 8888
    # test_proxy(testurl, ip, port, timeout=5)
    tornadoReq()
    # html = http_get(testurl)
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
    main()
        # time.sleep(120)
        # num = num + 1

