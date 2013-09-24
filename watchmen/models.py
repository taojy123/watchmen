# -*- coding: utf-8 -*-
from django.db import models


class Remind(models.Model):
    mid = models.CharField(max_length=64, blank=True , null=True)
    mtype = models.CharField(max_length=64, blank=True , null=True)
    btime = models.CharField(max_length=64, blank=True , null=True)
    team1 = models.CharField(max_length=64, blank=True , null=True)
    team2 = models.CharField(max_length=64, blank=True , null=True)
    org = models.CharField(max_length=64, blank=True , null=True)
    url = models.CharField(max_length=64, blank=True , null=True)
    is_read = models.BooleanField()

    @property
    def out_str(self):
        if self.org == "WD":
            org = u"韦德"
        else:
            org = u"易胜"
        s = "%s, %s, %s, %s, %s." % (self.mtype, self.btime, self.team1, self.team2, org)
        return s

    @property
    def out_org(self):
        if self.org == "WD":
            org = u"韦德"
        else:
            org = u"易胜"
        return org




