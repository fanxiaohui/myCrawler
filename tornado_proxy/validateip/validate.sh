#!/bin/sh
#****************************************************************#
# ScriptName: sh.sh
# Create Date: 2014-04-23 14:27
# Modify Date: 2014-04-23 14:27
#***************************************************************#

for ip in `cat $1`
do
	echo $ip
	curl -x$ip -m 3  -XGET http://www.the520.cn/proxy.php
	echo 
done
