#import grants from RSS file into DMP app 
# 
# needs a RSS file from datamad system.
# this is retrived by going to the CEDA export view. 
# use the edit view page. THis page has an RSS button that when clicked returns the 
# CEDA list of grants.


from django.core.management import setup_environ
import settings
setup_environ(settings)

from dmp.models import *

import sys
import xml.etree.ElementTree as ET
import re

tree = ET.parse(settings.DATAMAD_RSS_FILE)
root = tree.getroot()
channel = root.findall('channel')[0]

def getText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)

def find_field(desc, text):
    m = re.search('<div><b>%s:</b>(.*?)</div>' % text ,desc)
    if m: return m.group(1).strip()
    else: return ''
    
def find_long_field(desc, text):
    m = re.search('<div><b>%s:</b> <div class=".*?">(.*?)</div>' % text ,desc, re.S)
    if m: return m.group(1).strip()
    else: return ''


for item in channel.findall('item'):
    desc = item.find('description').text
    title = item.find('title').text
    print desc
    grant_ref =  find_field(desc, 'Grant Reference')
    PI =  find_field(desc, 'Grant Holder')
    PIemail = find_field(desc, 'E-Mail')
    abstract =  find_long_field(desc, 'Abstract')
    objectives =  find_long_field(desc, 'Objectives')
    
    print title
    print grant_ref
    print PI
    print abstract
    print objectives
    print '----------------------'
    
    # find grant if  does not exist make a new one
    grant = Grant.objects.filter(number=grant_ref)
    if len(grant) == 0:
        #need to make a new grant
        grant = Grant(number=grant_ref, pi= PI, title=title, 
                      desc="Abstract: %s\n\nObjectives: %s" % (abstract, objectives)) 
        grant.save()
    else:
        grant = grant[0]
        grant.pi = PI
        grant.title = title
        grant.desc = "Abstract: %s\n\nObjectives: %s" % (abstract, objectives)        
        grant.save()

