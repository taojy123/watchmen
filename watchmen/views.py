
# -*- coding: utf-8 -*-
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.views.decorators.csrf import csrf_exempt
from django.contrib import auth
from models import *
import os
import uuid
import cookielib
import urllib2, urllib
import time
import re
import traceback
import UglySoup
import smtplib
import json
import winsound





def index(request):
    return render_to_response('index.html', locals())


def manual_scan(request):
    email =  request.REQUEST.get('email', '')
    gap =  float(request.REQUEST.get('gap', 0.2))
    remind_WD, remind_YS = scan(email, gap)
    return HttpResponse( remind_WD + "<br/>" + remind_YS )

def unread(request):
    rs = Remind.objects.filter(is_read=False)
    for r in rs:
        r.is_read = True
        r.save()
    return render_to_response('unread.html', locals())

def remind(request):
    rs = Remind.objects.all()
    org =  request.REQUEST.get('org', '')
    if org:
        rs = Remind.objects.filter(org=org)
    return render_to_response('remind.html', locals())

def read(request):
    id = request.REQUEST.get('id', '')
    if id == "all":
        for rm in Remind.objects.all():
            rm.is_read = True
            rm.save()
    else:
        rm = Remind.objects.get(id=id)
        rm.is_read = True
        rm.save()
    return HttpResponseRedirect("/unread/")

def delete(request):
    id = request.REQUEST.get('id', '')
    if id == "all":
        Remind.objects.all().delete()
    else:
        Remind.objects.filter(id=id).delete()
    return HttpResponseRedirect("/remind/")

def clear(request):
    Remind.objects.all().delete()
    return HttpResponseRedirect("/index/")

#====================login=============================================
def login(request):
    username = request.REQUEST.get('username', '')
    password = request.REQUEST.get('password', '')
    user = auth.authenticate(username=username, password=password)
    if user is not None and user.is_active:
        auth.login(request, user)
    return HttpResponseRedirect("/admin/")

def logout(request):
    if request.user.is_authenticated():
        auth.logout(request)
    return HttpResponseRedirect("/admin/")
#======================================================================






#=======================FB_Spider=====================================
cj = cookielib.CookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.72 Safari/537.36'),
                     #('User-agent', 'Mozilla/5.0 (Windows NT 5.2) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.89 Safari/537.1'),
                     ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
                     ('Accept-Language', 'zh-CN,zh;q=0.8'),
                     ('Connection', 'keep-alive'),
                     ('Host', 'vip.bet007.com')
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
            print "Will try after 1 seconds ..."
            time.sleep(1)
    return "Null"


def add_remind(mid, mtype, btime, team1, team2, org, url, email=""):
    if not Remind.objects.filter(mid=mid, org=org):
        rm = Remind()
        rm.mid = mid
        rm.mtype = mtype
        rm.btime = btime
        rm.team1 = team1
        rm.team2 = team2
        rm.org = org
        rm.url = url
        rm.is_read = False
        rm.save()
        winsound.MessageBeep(61)
        if email:
            smtp = smtplib.SMTP()
            smtp.connect("smtp.163.com", "25")
            smtp.login('watchmen123456', 'wm123456')
            msg = 'From: watchmen123456@163.com\r\nTo: %s\r\nSubject: WatchMen Remind %s\r\n\r\n%s\n%s' % (email, rm.mtype, rm.out_str, rm.url)
            msg = msg.encode("gbk")
            smtp.sendmail('watchmen123456@163.com', email, msg)
            smtp.quit()



def scan(email="", gap=0.2):
    remind_WD = ""
    remind_YS = ""
    microtime = int(time.time() * 1000)
    url = 'http://live2.titan007.com/vbsxml/bfdata.js?%d' % microtime
    p = get_page(url)

    p = p.decode("gbk")
    p = p.replace(r"^", r"///")
    p = p.encode("gbk")
    p = p.replace("\r\n", "<bR>")
    p = re.findall(r"(A\[1\]=.*)B\[1\]=" , p)[0]
    p = p.replace("<bR>", "\n").replace(";", "")


    num = len(p.split("\n"))
    A = [None for i in range(num + 30)]
    exec(p)

    n = 0
    for m in A:
        if not m :
            continue
        else:
            n += 1
        try:
            mid = m[0]
            print n, mid
            mtype = m[2]
            team1 = m[5]
            team2 = m[8]
            btime = m[11]
            bdate = m[36]
            mtype = mtype.decode("gbk")
            team1 = team1.decode("gbk")
            team2 = team2.decode("gbk")
            begintime = time.strptime(bdate + "_" + btime, '%m-%d_%H:%M')
            nowtime = time.strftime("%m-%d_%H:%M", time.localtime())
            nowtime = time.strptime(nowtime, '%m-%d_%H:%M')
            if begintime > nowtime:
                url = "http://vip.bet007.com/AsianOdds_n.aspx?id=%s" % mid
                time.sleep(0.1)
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
                        if (SB_PK!=WD_PK) or (WD_ZD-SB_ZD>gap) or (WD_KD-SB_KD>gap):
                            print mid, mtype, btime, team1, team2, "WD"
                            remind_WD += u"<p><a href='%s' target='_blank' >%s, %s, %s, %s, 韦德.</a></p>" % (url, mtype, btime, team1, team2)
                            add_remind(mid, mtype, btime, team1, team2, "WD", url, email)
                    if YS_PK:
                        YS_ZD = float(YS[4].getText())
                        YS_KD = float(YS[6].getText())
                        if (SB_PK!=YS_PK) or (YS_ZD-SB_ZD>gap) or (YS_KD-SB_KD>gap):
                            print mid, mtype, btime, team1, team2, "YS"
                            remind_YS += u"<p><a href='%s' target='_blank' >%s, %s, %s, %s, 易胜.</a></p>" % (url, mtype, btime, team1, team2)
                            add_remind(mid, mtype, btime, team1, team2, "YS", url, email)

        except:
            print "=========warning========", m[0]
            traceback.print_exc()

    print "scan finish"
    return remind_WD, remind_YS


#======================================================================








