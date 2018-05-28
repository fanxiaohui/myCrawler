#!/usr/bin/env python
#
# Simple asynchronous HTTP proxy with tunnelling (CONNECT).
#
# GET/POST proxying based on
# http://groups.google.com/group/python-tornado/msg/7bea08e7a049cf26
#
# Copyright (C) 2012 Senko Rasic <senko.rasic@dobarkod.hr>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import sys
import socket

import tornado.httpserver
import tornado.ioloop
import tornado.iostream
import tornado.web
import tornado.httpclient

import redis, random, time, md5, os

__all__ = ['ProxyHandler', 'run_proxy']


def init_redis():
    '''
    init redis
    '''
    global redis_client
    redis_client = redis.Redis(host='210.22.106.178', port=2003, db=0)


redis_client = None
init_redis()
SKIP_PROXY = 0
REQUEST_TIMEOUT = 1000
CONNECT_TIMEOUT = 1000
MAX_CD_TRYCOUNT = 6
COOLDOWN_TIME = 100 # cooldown time 3s
headers = {
    SKIP_PROXY:'Skip-Proxy',
    REQUEST_TIMEOUT:'Request-Timeout',
    CONNECT_TIMEOUT:'Connect-Timeout'
}

CACHE_PATH = '/tmp/proxy_cache'


class ProxyHandler(tornado.web.RequestHandler):
    SUPPORTED_METHODS = ['GET', 'POST', 'CONNECT']

    def initialize(self, redis):
        self.redis_client = redis_client

    def check_cooldown(self, proxy, host):
        last_visit = self.redis_client.exists( 'proxy::cooldown::%s_%s' % (proxy, host))
        print "last_visit time:%s" %last_visit
        return not last_visit
        '''if not last_visit:
            print 'no visit'
            return True
        print 'last_visit:%s' % last_visit 
        return int(last_visit) + cooldown < int(time.time())'''

    def choose_proxy(self, host='', last=''):
        # proxylist = self.redis_client.zrangebyscore('proxy','-inf', '+inf', num=5, start=0)
        proxylist = self.redis_client.zrangebyscore('prank', '90', '+inf', withscores=True)
        proxy = None
        cd_trycount = 1
        num = random.randint(0, len(proxylist) - 1)
        tmpproxy = proxylist[num][0]
        print proxylist[num]
        proxy = tmpproxy
        # while not proxy or proxy == last:
        #     tmpproxy = proxylist[random.randint(0, len(proxylist) - 1)]
        #     #check CD
        #     '''print 'check cd'''
        #     if host != '' and cd_trycount <= MAX_CD_TRYCOUNT and not self.check_cooldown(tmpproxy, host):
        #         cd_trycount += 1
        #         continue
        #     proxy = tmpproxy
        #
        # self.redis_client.incr(proxy)
        # if host != '':
        #     cd = int(time.time())
        #     #print 'cd:%i' %  cd
        #     self.redis_client.setex( 'proxy::cooldown::%s_%s' % (proxy, host), 3, COOLDOWN_TIME)
        # self.proxy = proxy
        return proxy
         
    @tornado.web.asynchronous
    def get(self):
        def handle_response(response):
            # print response.code, self.proxy, response.effective_url
            print response.code, response.effective_url
            if response.code == 599:
                self.set_status(504)
                #mark proxy timeout
                # self.redis_client.zincrby('proxy', self.proxy, -1)
                self.finish()
                return

            if response.error and not isinstance(response.error,
                    tornado.httpclient.HTTPError):
                self.set_status(500)
                self.write('Internal server error1:\n' + str(response.error))
                self.finish()
            else:
                self.set_status(response.code)
                for header in ('Date', 'Cache-Control', 'Server',
                        'Content-Type', 'Location'):
                    v = response.headers.get(header)
                    if v:
                        self.set_header(header, v)
                # self.set_header('SNDA-Proxy', self.proxy)
                if response.body:
                    m = md5.new()
                    m.update(response.body)
                    cachefile = file('%s/%s' % (CACHE_PATH, m.hexdigest()), 'w')
                    cachefile.write(response.body)
                    cachefile.close()
                    self.write(response.body)
                self.finish()

        lastproxy = ''
        connect_timeout = 3
        request_timeout = 3
        if headers[SKIP_PROXY] in self.request.headers:
            lastproxy = self.request.headers[headers[SKIP_PROXY]]
            print 'skip:', lastproxy
        if headers[CONNECT_TIMEOUT] in self.request.headers:
            connect_timeout = int(self.request.headers[headers[CONNECT_TIMEOUT]])
        if headers[REQUEST_TIMEOUT] in self.request.headers:
            request_timeout = int(self.request.headers[headers[REQUEST_TIMEOUT]])

        # tmpproxy = self.choose_proxy(self.request.host, lastproxy).split(':')
        tmpproxy = ['pp', '//106.14.135.47', '3389']
        body = self.request.body
        body = None
        if self.request.method.lower() == "post":
            body = self.request.body
        # print body
        ua = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36"
        tornado.httpclient.AsyncHTTPClient.configure('tornado.curl_httpclient.CurlAsyncHTTPClient')
        req = tornado.httpclient.HTTPRequest(url=self.request.uri, user_agent=ua,
                                            method=self.request.method,
                                            body=body,
                                            # headers=self.request.headers,
                                            follow_redirects=False,
                                            connect_timeout=connect_timeout, request_timeout=request_timeout,
                                            allow_nonstandard_methods=True,
                                            proxy_host=tmpproxy[1][2:], proxy_port=int(tmpproxy[2]))

        client = tornado.httpclient.AsyncHTTPClient()
        try:
            client.fetch(req, handle_response)
        except tornado.httpclient.HTTPError as e:
            if hasattr(e, 'response') and e.response:
                handle_response(e.response)
            else:
                self.set_status(500)
                self.write('Internal server error2:\n' + str(e))
                self.finish()
        except Exception,e:
            print 'Common Exception', e

    @tornado.web.asynchronous
    def post(self):
        return self.get()

    @tornado.web.asynchronous
    def connect(self):
        host, port = self.request.uri.split(':')
        client = self.request.connection.stream

        def read_from_client(data):
            upstream.write(data)

        def read_from_upstream(data):
            client.write(data)

        def client_close(data=None):
            if upstream.closed():
                return
            if data:
                upstream.write(data)
            upstream.close()

        def upstream_close(data=None):
            if client.closed():
                return
            if data:
                client.write(data)
            client.close()

        def start_tunnel():
            client.read_until_close(client_close, read_from_client)
            upstream.read_until_close(upstream_close, read_from_upstream)
            client.write(b'HTTP/1.0 200 Connection established\r\n\r\n')

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        upstream = tornado.iostream.IOStream(s)
        upstream.connect((host, int(port)), start_tunnel)

    

def run_proxy(port, start_ioloop=True):
    """
    Run proxy on the specified port. If start_ioloop is True (default),
    the tornado IOLoop will be started immediately.
    """

    #init tornado
    app = tornado.web.Application([
        (r'.*', ProxyHandler, dict(redis=redis_client)),
    ])
    server = tornado.httpserver.HTTPServer(app, xheaders=True)
    #sockets = tornado.netutil.bind_sockets(port, '127.0.0.1')
    #server.add_sockets(sockets)
    server.bind(port)
    server.start(4)

    ioloop = tornado.ioloop.IOLoop.instance()
    if start_ioloop:
        ioloop.start()
    
if __name__ == '__main__':
    port = 8888
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    
    if not os.path.exists(CACHE_PATH):
        os.mkdir(CACHE_PATH) 
    print ("Starting HTTP proxy on port %d" % port)
    run_proxy(port)
