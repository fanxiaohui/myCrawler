# coding: utf-8
import sys
reload(sys)
sys.setdefaultencoding('utf8')

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.header import Header
import json

# 设置smtplib所需的参数
# 下面的发件人，收件人是用于邮件传输的。
smtpserver = 'smtp.163.com'
username = 'information_use@163.com'
password = 'zoucheng521'
sender = 'information_use@163.com'
# receiver='XXX@126.com'
# 收件人为多个收件人
# receiver = ['1369358420@qq.com', '153952862@qq.com']
receiver = ['153952862@qq.com']


def sendMail(jObj):

    # subject = jObj['Destination']
    # 通过Header对象编码的文本，包含utf-8编码信息和Base64编码信息。以下中文名测试ok
    # subject = '中文标题'
    # subject=Header(subject, 'utf-8').encode()

    # 构造邮件对象MIMEMultipart对象
    # 下面的主题，发件人，收件人，日期是显示在邮件页面上的。
    msg = MIMEMultipart('mixed')
    constructContent(msg, jObj)

    # 发送邮件
    smtp = smtplib.SMTP()
    smtp.connect('smtp.163.com')
    # 我们用set_debuglevel(1)就可以打印出和SMTP服务器交互的所有信息。
    # smtp.set_debuglevel(1)
    smtp.login(username, password)
    smtp.sendmail(sender, receiver, msg.as_string())
    smtp.quit()


def constructContent(msg, jObj):
    msg['Subject'] = jObj['Destination']
    msg['From'] = 'information_use@163.com'
    # msg['To'] = 'XXX@126.com'
    # 收件人为多个收件人,通过join将列表转换为以;为间隔的字符串
    msg['To'] = ";".join(receiver)
    # msg['Date']='2012-3-16'

    template = "<h4>_id:%s</h4>\
                Destination：%s<br/>\
                StartDate：%s<br/>\
                Nickname：%s<br/>\
                num：%s<br/>\
                Distance：%s<br/>\
                Position：%s<br/>\
                Remark：%s<br/>\
                <br/><br/>\
                <table> \
                       <tr><td>head</td><td><img src=\'%s\'></td></tr>\
                       %s\
                </table>"
    lineStri = ''
    for item in jObj['PicList']:
        str = "<tr><td><img src=\'%s\'></td></tr>" % (item['Url'])
        lineStri = lineStri + str

    html1 = template % (jObj['_id'], jObj['Destination'], jObj['StartDate'], jObj['Nickname'],
                        jObj['Age'], jObj['Distance'], jObj['Position'], jObj['Remark'], jObj['HeadUrl'], lineStri)
    msghtml = MIMEText(html1, 'html', "utf-8")
    msg.attach(msghtml)