
import cookielib
import urllib2, urllib
import time
import re
import traceback
import UglySoup
from models import *

cj = cookielib.CookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 5.2) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.89 Safari/537.1'),
                     ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
                     ('Accept-Language', 'zh-cn,zh;q=0.8,en-us;q=0.5,en;q=0.3'),
                     ('Connection', 'keep-alive')
]
opener.addheaders.append( ('Accept-encoding', 'identity') )
opener.addheaders.append( ('Referer', 'http://live2.titan007.com/') )

def get_page(url, data=None):
    n = 0
    while n < 5:
        n += 1
        try:
            resp = opener.open(url, data)
            page = resp.read()
            return page
        except:
            traceback.print_exc()
            print "Will try after 2 seconds ..."
            time.sleep(2.0)
            continue
        break
    return "Null"


def add_remind(mid, mtype, btime, team1, team2, org):
    if not Remind.objects.filter(mid=mid, org=org):
        rm = Remind()
        rm.mid = mid
        rm.mtype = mtype
        rm.btime = btime
        rm.team1 = team1
        rm.team2 = team2
        rm.org = org
        rm.is_read = False
        rm.save()


def scan():
    microtime = int(time.time() * 1000)
    url = 'http://live2.titan007.com/vbsxml/bfdata.js?%d' % microtime
    p = get_page(url)

    p = p.replace("\r\n", "<bR>")
    p = re.findall(r"(A\[1\]=.*)B\[1\]=" , p)[0]
    p = p.replace("<bR>", "\n").replace(";", "")

    num = len(p.split("\n"))
    A = [None for i in range(num + 30)]
    exec(p)

    for m in A:
        if not m :
            continue
        try:
            mid = m[0]
            mtype = m[2]
            team1 = m[5]
            team2 = m[8]
            btime = m[11]
            bdate = m[36]
            begintime = time.strptime(bdate + "_" + btime, '%m-%d_%H:%M')
            nowtime = time.strftime("%m-%d_%H:%M", time.localtime())
            nowtime = time.strptime(nowtime, '%m-%d_%H:%M')
            if begintime > nowtime:
                url = "http://vip.bet007.com/AsianOdds_n.aspx?id=%s" % mid
                p = get_page(url)
                sp = UglySoup.BeautifulSoup(p)
                odds = sp.find("span", attrs={"id":"odds"})
                trs = odds.findAll("tr")
                SB = trs[2]
                WD = trs[5]
                YS = trs[6]
                SB = SB.findAll("td")
                WD = WD.findAll("td")
                YS = YS.findAll("td")
                SB_PK = SB[5].getText()
                WD_PK = WD[5].getText()
                YS_PK = YS[5].getText()
                if SB_PK:
                    SB_ZD = float(SB[4].getText())
                    SB_KD = float(SB[6].getText())
                    if WD_PK:
                        WD_ZD = float(WD[4].getText())
                        WD_KD = float(WD[6].getText())
                        if (SB_PK!=WD_PK) or (WD_ZD-SB_ZD>0.2) or (WD_KD-SB_KD>0.2):
                            print mid, mtype, btime, team1, team2, "WD"
                            add_remind(mid, mtype, btime, team1, team2, "WD")
                    if YS_PK:
                        YS_ZD = float(YS[4].getText())
                        YS_KD = float(YS[6].getText())
                        if (SB_PK!=YS_PK) or (YS_ZD-SB_ZD>0.2) or (YS_KD-SB_KD>0.2):
                            print mid, mtype, btime, team1, team2, "YS"
                            add_remind(mid, mtype, btime, team1, team2, "YS")

        except:
            print "=========warning========", m[0]







