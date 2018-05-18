#coding:utf8
import redis,json
import urllib, urllib2

baseline = ''
testurl = 'http://www.the520.cn/proxy.php'

def http_get(url):
    return urllib2.urlopen(url).read()    

def test_proxy(url, ip, port, timeout = 5):
    global baseline
    try:
        proxy_handler = urllib2.ProxyHandler({'http':'http://%s:%s/' % (ip, port)})
        opener = urllib2.build_opener(proxy_handler)
        opener.addheaders = [('User-agent','Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36')]
        html = opener.open(url, timeout=timeout).read()
        return html.find('mato') == -1
        data = json.loads(html)
        if data.has_key('status') and data.has_key('HTTP_X_FORWARDED_FOR') and data['status'] == 'ok' and data['HTTP_X_FORWARDED_FOR'].find(baseline) == -1:
            return True
        else:
            print data
    except Exception,e:
        print e
    return False


def validate(proxy, testurl):
    return test_proxy(testurl, proxy.split(':')[0], proxy.split(':')[1], 5)
    
html = http_get(testurl)
baseline = json.loads(html)['HTTP_X_FORWARDED_FOR']

db = redis.StrictRedis(host='127.0.0.1', port=6379)
for proxy in db.zrange('proxy',0, -1):
    if not validate(proxy, 'http://www.babytree.com/ask/detail/16389192'):
        db.zrem('proxy', proxy)
        print 'remove proxy:%s' % proxy
print 'end'



