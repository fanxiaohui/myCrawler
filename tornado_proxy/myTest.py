#-*- coding:UTF-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import mail
import json
import re
import urllib
import  testHttp


def checkDest(dstr):
    myPattern = u".*上海|杭州.*"
    p = re.compile(myPattern)
    ret = p.search(dstr)
    return ret


if __name__ == '__main__':
    print 'my test'
    data = '{ "_id" : "cab5b6e1-660d-11e8-99d4-00163e002e59_2018-06-02 11:15:36", "JoinList" : null, "Yid" : 224937, "RecommendCity" : "", "FromMark" : "", "From" : "深圳市", "Guest" : "false", "LikeList" : null, "Destination" : "南京～上海～苏州", "ReplyList" : null, "MoneyType" : "线下AA", "Platform" : "ios", "Gid" : "50867403292673", "Recommend" : false, "Latitude" : 22.722473, "AssemblingPlace" : { "Locate" : "", "Province" : "", "City" : "", "Country" : "", "Section" : "", "YueyouCount" : 0, "PicUrl" : "", "Address" : "", "ComId" : 0 }, "WantGo" : "最远的希腊", "EndTime" : "0001-01-01 00:00:00", "Status" : 0, "StartDate" : "2018-06-04", "Updated" : "2018-06-02 11:18:14", "MaritalStatus" : "保密", "EndDate" : "2018-06-11", "YueyouLikeCount" : 1, "Tags" : "", "IsGroup" : false, "IsTop" : false, "YueyouReplyCount" : 1, "Gender" : "女", "UserTags" : "小资,小清新", "Nickname" : "娃娃国的小精灵", "Age" : 32, "RecommendResCount" : 0, "Distance" : 1187.32, "Remark" : "#6月4日号出发，求约伴#我是6.4从深圳出发南京，然后上海再去苏州，求志同道合的小伙伴，不事多，不挑剔，不挑食！我的性格比较理智但是很暖暖暖暖……", "YueyouJoinCount" : 1, "Created" : "2018-06-02 11:15:36", "RecommendRes" : null, "IsCohabit" : false, "Require" : "我是个开朗而且特别朴实的菇凉想把这几个地方游览求不事多不挑剔", "Work" : "", "Longitude" : 114.219422, "GroupName" : "2018-06-04深圳市至南京～上海～苏州", "Position" : "深圳市", "ComId" : 0, "Uid" : "cab5b6e1-660d-11e8-99d4-00163e002e59", "Number" : 1, "IsJoin" : false, "PicList" : [ 	{ 	"Status" : 0, 	"Yid" : 224937, 	"Uid" : "cab5b6e1-660d-11e8-99d4-00163e002e59", 	"Created" : "2018-06-02 11:18:15", 	"Ypid" : 2219904, 	"Url" : "http://img2.miaotu.net/2018-06-02/920117c54db12901d9653f2267ec6da7.jpg" } ], "HeadUrl" : "http://img2.miaotu.net/2018-06-02/352a30589d835950255cd679b845058d.jpg", "IsLike" : false }'
    '''
    _id
    Destination
    StartDate
    Nickname
    Age 
    Distance
    Position
    Remark
    PicList Url
    HeadUrl
    <tr><img src='http://img2.miaotu.net/2018-06-02/920117c54db12901d9653f2267ec6da7.jpg'></tr>
    '''
    # jObj = json.loads(data)
    # # rule = '杭州sskshkj上海'
    # # myPattern = r".*上海|杭州.*"
    # # p = re.compile(myPattern)
    # # print p.search(rule)
    # print urllib.quote('上海')
    #
    # if jObj['Gender'] == "女" and checkDest(jObj['Destination']):
    #     print jObj['Destination']
    # mail.sendMail(jObj)
    zaiurl = 'http://zaiwai.qunawan.com/feedService/findProvinceOrNationInviteFeedListByTerminiId'
    mongo = testHttp.pagedbLogic('zaiwai')
    testHttp.zaiwaiRequest(zaiurl, mongo, '370668282294176')