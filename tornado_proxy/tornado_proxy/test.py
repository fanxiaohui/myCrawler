#!/usr/bin/env python
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
    redis_client = redis.Redis(host='localhost', port=6379, db=0)

redis_client = None
init_redis()
SKIP_PROXY = 0
REQUEST_TIMEOUT = 1
CONNECT_TIMEOUT = 2
MAX_CD_TRYCOUNT = 6
COOLDOWN_TIME = 3 # cooldown time 3s
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

    @tornado.web.asynchronous
    def get(self):
        def handle_response(response):
            if not hasattr(self, 'step'):
                self.step = 0
            print response.code,  response.effective_url, self.step
            self.step += 1
            if not hasattr(self, 'reqlist'):
                self.reqlist = []
            self.reqlist.append(response.body)

            if self.step == 2:
                self.set_status(200)
                self.write('___________'.join(self.reqlist))
                self.finish()

            

        lastproxy = ''
        connect_timeout = 30
        request_timeout = 180
        tornado.httpclient.AsyncHTTPClient.configure('tornado.curl_httpclient.CurlAsyncHTTPClient')
        req0 = tornado.httpclient.HTTPRequest(url='http://www.the520.cn/proxy.php',
            method=self.request.method, body=None,
            headers=self.request.headers, follow_redirects=False,
            connect_timeout=connect_timeout, request_timeout=request_timeout,
            allow_nonstandard_methods=True)
        req1 = tornado.httpclient.HTTPRequest(url='http://www.google.com',
            method=self.request.method, body=None,
            headers=self.request.headers, follow_redirects=False,
            connect_timeout=connect_timeout, request_timeout=request_timeout,
            allow_nonstandard_methods=True)

        client = tornado.httpclient.AsyncHTTPClient()
        try:
            client.fetch(req0, handle_response)
            client.fetch(req1, handle_response)
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
