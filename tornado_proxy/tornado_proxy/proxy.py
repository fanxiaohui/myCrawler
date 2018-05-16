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

import redis
import random

__all__ = ['ProxyHandler', 'run_proxy']


def init_redis():
    '''
    init redis
    '''
    global redis_client
    redis_client = redis.Redis(host='localhost', port=6379, db=0)


redis_client = None
init_redis()
SKIP_PROXY = 0
REQUEST_TIMEOUT = 1
CONNECT_TIMEOUT = 2
headers = {
    SKIP_PROXY:'Skip-Proxy',
    REQUEST_TIMEOUT:'Request-Timeout',
    CONNECT_TIMEOUT:'Connect-Timeout'
}


class ProxyHandler(tornado.web.RequestHandler):
    SUPPORTED_METHODS = ['GET', 'POST', 'CONNECT']

    def initialize(self, redis):
        self.redis_client = redis_client
    
    def choose_proxy(self, last=''):
        proxylist = self.redis_client.zrangebyscore('proxy', '-inf', '+inf', num=5, start=0)
        proxy = None
        while not proxy or proxy == last:
            proxy = proxylist[random.randint(0, len(proxylist) - 1)]

        self.redis_client.incr(proxy)
        self.proxy = proxy
        return proxy
         
    @tornado.web.asynchronous
    def get(self):

        def handle_response(response):
            print response.code, self.proxy, response.effective_url
            if response.code == 599:
                self.set_status(504)
                #mark proxy timeout
                self.redis_client.zincrby('proxy', self.proxy, 1)
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
                self.set_header('SNDA-Proxy', self.proxy)
                if response.body:
                    self.write(response.body)
                self.finish()

        lastproxy = ''
        connect_timeout = 30
        request_timeout = 180
        if headers[SKIP_PROXY] in self.request.headers:
            lastproxy = self.request.headers[headers[SKIP_PROXY]]
            print 'skip:', lastproxy
        if headers[CONNECT_TIMEOUT] in self.request.headers:
            connect_timeout = int(self.request.headers[headers[CONNECT_TIMEOUT]])
        if headers[REQUEST_TIMEOUT] in self.request.headers:
            request_timeout = int(self.request.headers[headers[REQUEST_TIMEOUT]])

        tmpproxy = self.choose_proxy(lastproxy).split(':')

        tornado.httpclient.AsyncHTTPClient.configure('tornado.curl_httpclient.CurlAsyncHTTPClient')
        req = tornado.httpclient.HTTPRequest(url=self.request.uri,
            method=self.request.method, body=self.request.body,
            headers=self.request.headers, follow_redirects=False,
            connect_timeout=connect_timeout, request_timeout=request_timeout,
            allow_nonstandard_methods=True, 
            proxy_host=tmpproxy[0], proxy_port=int(tmpproxy[1]))

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
            print e

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

    app = tornado.web.Application([
        (r'.*', ProxyHandler, dict(redis=redis_client)),
    ])
    server = tornado.httpserver.HTTPServer(app, xheaders=True)
    sockets = tornado.netutil.bind_sockets(port, '127.0.0.1')
    server.add_sockets(sockets)
    ioloop = tornado.ioloop.IOLoop.instance()
    if start_ioloop:
        ioloop.start()


if __name__ == '__main__':
    port = 8888
    if len(sys.argv) > 1:
        port = int(sys.argv[1])

    print ("Starting HTTP proxy on port %d" % port)
    run_proxy(port)
