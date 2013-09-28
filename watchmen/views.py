
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
    no_sound =  request.REQUEST.get('no_sound', 'false')
    remind_WD_A, remind_WD_B, remind_YS_A, remind_YS_B = scan(email, gap, no_sound)
    return HttpResponse( remind_WD_A + "/////" + remind_WD_B + "/////" + remind_YS_A + "/////" + remind_YS_B )

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


def add_remind(mid, mtype, btime, team1, team2, org, url, email="", no_sound="false"):
    print no_sound
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
        if no_sound == "false":
            winsound.PlaySound("static/beep.wav", 131072)
        if email:
            smtp = smtplib.SMTP()
            smtp.connect("smtp.163.com", "25")
            smtp.login('watchmen123456', 'wm123456')
            msg = 'From: watchmen123456@163.com\r\nTo: %s\r\nSubject: WatchMen Remind %s\r\n\r\n%s\n%s' % (email, rm.mtype, rm.out_str, rm.url)
            msg = msg.encode("gbk")
            smtp.sendmail('watchmen123456@163.com', email, msg)
            smtp.quit()



def scan(email="", gap=0.2, no_sound="false"):
    remind_WD_A = []
    remind_WD_B = []
    remind_YS_A = []
    remind_YS_B = []
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
                if not odds:
                    print "not data"
                    continue
                trs = odds.findAll("tr")
                SB = trs[2]
                WD = trs[3]
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
                        if SB_PK != WD_PK:
                            x = min(abs(WD_ZD-SB_ZD), abs(WD_KD-SB_KD))
                            print mid, mtype, btime, team1, team2, x, "BET_A"
                            remind_WD_A.append([x, u"<p><a href='%s' target='_blank' >%s, %s, %s, %s, %s, BET.</a></p>" % (url, mtype, btime, team1, team2, x)])
                            add_remind(mid, mtype, btime, team1, team2, "BET", url, email, no_sound)
                        elif WD_ZD-SB_ZD>gap or WD_KD-SB_KD>gap:
                            x = max(WD_ZD-SB_ZD, WD_KD-SB_KD)
                            print mid, mtype, btime, team1, team2, x, "BET_B"
                            remind_WD_B.append([x, u"<p><a href='%s' target='_blank' >%s, %s, %s, %s, %s, BET.</a></p>" % (url, mtype, btime, team1, team2, x)])
                            add_remind(mid, mtype, btime, team1, team2, "BET", url, email, no_sound)
                    if YS_PK:
                        YS_ZD = float(YS[4].getText())
                        YS_KD = float(YS[6].getText())
                        if SB_PK != YS_PK:
                            x = min(abs(YS_ZD-SB_ZD), abs(YS_KD-SB_KD))
                            print mid, mtype, btime, team1, team2, x, "YS_A"
                            remind_YS_A.append([x, u"<p><a href='%s' target='_blank' >%s, %s, %s, %s, %s, 易胜.</a></p>" % (url, mtype, btime, team1, team2, x)])
                            add_remind(mid, mtype, btime, team1, team2, "YS", url, email, no_sound)
                        elif YS_ZD-SB_ZD>gap or YS_KD-SB_KD>gap:
                            x = max(YS_ZD-SB_ZD, YS_KD-SB_KD)
                            print mid, mtype, btime, team1, team2, x, "YS_B"
                            remind_YS_B.append([x, u"<p><a href='%s' target='_blank' >%s, %s, %s, %s, %s, 易胜.</a></p>" % (url, mtype, btime, team1, team2, x)])
                            add_remind(mid, mtype, btime, team1, team2, "YS", url, email, no_sound)

        except:
            print "=========warning========", m[0]
            traceback.print_exc()

    print "scan finish"

    remind_WD_A.sort()
    remind_WD_B.sort()
    remind_YS_A.sort()
    remind_YS_B.sort()
    remind_WD_B = remind_WD_B[::-1]
    remind_YS_B = remind_YS_B[::-1]

    remind_WD_A = [r[1] for r in remind_WD_A]
    remind_WD_B = [r[1] for r in remind_WD_B]
    remind_YS_A = [r[1] for r in remind_YS_A]
    remind_YS_B = [r[1] for r in remind_YS_B]

    remind_WD_A = "".join(remind_WD_A)
    remind_WD_B = "".join(remind_WD_B)
    remind_YS_A = "".join(remind_YS_A)
    remind_YS_B = "".join(remind_YS_B)

    print "-----------------"
    print remind_WD_A
    print remind_WD_B
    print remind_YS_A
    print remind_YS_B
    print "-----------------"

    return remind_WD_A, remind_WD_B, remind_YS_A, remind_YS_B


#======================================================================








