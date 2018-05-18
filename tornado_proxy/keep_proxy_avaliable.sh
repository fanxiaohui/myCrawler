#!/bin/sh
echo "start crawl proxy list"
python proxy_finder/finder.py proxylist_daily > /dev/null
rm -f addproxy.sh
echo "start generate addproxy.sh script"
cat proxylist_daily | awk '{print "redis-cli zadd proxy \"0\" \""$1"\""}' > addproxy.sh
echo "start add proxy to the pool"
sh addproxy.sh > /dev/null
echo "start remove bad proxy from the pool"
python validateip/validate_proxy_pool.py > /dev/null
echo "Done"

