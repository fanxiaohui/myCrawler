
#-*- coding:UTF-8 -*-
import sys
# reload(sys)
# sys.setdefaultencoding('utf8')
import BeautifulSoup
import urllib, urllib2
import zipfile,gzip,io,StringIO,zlib
import json

reload(sys)
sys.setdefaultencoding('utf-8')

baseline = ''
testurl = 'http://106.14.135.47:2233/'
# testurl = 'http://www.example.com/'


def http_get(url):
    request = urllib2.Request(url)
    request.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8')
    request.add_header('Accept-Encoding', 'deflate')
    request.add_header('Accept-Language', 'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4')
    request.add_header('Cache-Control', 'max-age=0')
    request.add_header('Connection', 'keep-alive')
    request.add_header('User-Agent', 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0)')

    try:
        response = urllib2.urlopen(request)
        print response.getcode()
    except:
        print '--------------------403--------------------'
        return url
    html = response.read()
    return html
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
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        ret = opener.open(url, timeout=timeout)
        print ret.code
        if ret.code == 200:
            return True
        else:
            ret.code
            print data
        # html = opener.open(url, timeout=timeout).read()
    except Exception, e:
        print e
    return False


def main():
    # for i in range(30):
    #     test_proxy(testurl, '119.28.194.66', '8888')
    # exit()

    # html = http_get(testurl)
    # print html
    # global baseline
    # baseline = json.loads(html)['HTTP_X_FORWARDED_FOR']
    # print 'public ip:', baseline
    url = 'http://www.xici.net.co/nn'
    html = http_get(url)
    # print html
    s = BeautifulSoup.BeautifulSoup(html)
    # print s
    # print type(s)
    artiBlock = s.find('table', {'id': 'ip_list'})
    # print artiBlock.findAll('tr')
    # print artiBlock
    # print s.select('#ip_list')

    # ips = []
    output = []
    ofile = file(sys.argv[1], 'w')
    # for tr in s.select('table #ip_list tr')[1:]:
    count = 0
    for tr in artiBlock.findAll('tr')[1:]:
        # print tr
        ip = {}
        ip['ip'] = tr.findAll('td')[1].text
        ip['port'] = tr.findAll('td')[2].text
        ip['type'] = tr.findAll('td')[5].text
        print '%s:%s %s' %(ip['ip'], ip['port'], ip['type'])
        # ips.append(ip)
        # output.append(ip)
        # print 'avaliable:', '%s:%s' % (ip['ip'], ip['port'])
        # print >> ofile, '%s:%s' % (ip['ip'], ip['port'])
        if ip['type'].lower() == 'http' and test_proxy(testurl, ip['ip'], ip['port']):
            if count == 2:
                continue
            output.append(ip)
            print 'avaliable:', '%s:%s'% (ip['ip'], ip['port'])
            print >>ofile, '%s:%s' % (ip['ip'], ip['port'])
            count = count + 1
        else:
            print 'not:%s:%s' %(ip['ip'], ip['port'])
    print output
    ofile.close()


if __name__ == '__main__':
    main()
