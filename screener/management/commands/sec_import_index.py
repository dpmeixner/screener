import sys
from pysec.models import *
from django.core.management.base import NoArgsCommand
from django.conf import settings
import urllib,os,re,os.path
from zipfile import ZipFile
import time
from django.db.transaction import commit_on_success
from screener.models import Index as screener_index

DATA_DIR = settings.DATA_DIR
def removeNonAscii(s): return "".join(i for i in s if ord(i)<128)

# Gets the list of filings and download locations for the given year and quarter
def get_filing_list(year,qtr):
    url='ftp://ftp.sec.gov/edgar/full-index/%d/QTR%d/company.zip' % (year,qtr)
    quarter = "%s%s" % (year,qtr)

    print url

    # Download the data and save to a file
    fn='%s/company_%d_%d.zip' % (DATA_DIR, year,qtr)

    compressed_data=urllib.urlopen(url).read()
    fileout=file(fn,'w')
    fileout.write(compressed_data)
    fileout.close()
    
    # Extract the compressed file
    zip=ZipFile(fn)
    zdata=zip.read('company.idx')
    zdata = removeNonAscii(zdata)
    # Parse the fixed-length fields
    result=[]
    # DM: edited this, remove '3010' to change back to [10:]:
    for r in zdata.split('\n')[10:]:
        form = r[62:74].strip()
        if (form != '10-K' and form != '10-Q'): continue
        date = r[86:98].strip()
        if date=='': date = None
        if r.strip()=='': continue
        cik = r[74:86].strip()
        filing={'name':r[0:62].strip(),
                'form':form,
                'cik':cik,
                'date':date,
                'quarter': quarter,
                'filename':r[98:].strip()}

        #TODO: new company could use cik from old company, but date should fix this...make sure
        dbFiling = Index.objects.filter(cik=cik)

        if dbFiling.count(): # This cik alread exists
            newDate = int(re.sub('-','',str(date)))
            oldDate = int(re.sub('-','',str(dbFiling[0].date)))
            if newDate > oldDate:
                print cik, ': This is a new filing, oldDate:', oldDate, ' newDate:', newDate
                Index.objects.filter(cik=cik).delete()
                result.append(Index(**filing))
                screener_index.objects.filter(cik=cik).delete()
        else: # cik does not exist so add it
            print cik, ': This filing does noe exist...adding it'
            result.append(Index(**filing))

    return result

#Commit all objects at once to speed up the process
@commit_on_success
def commitObjs(objs):
    for obj in objs:
        try:
            obj.save()
        except:
            print 'error: %s' % obj
            pass

class Command(NoArgsCommand):
    help = "Download new files representing one month of 990s, ignoring months we already have. Each quarter contains hundreds of thousands of filings; will take a while to run. "
    
    '''
    Grab the current quarter and previous 2 quarters of filings to make sure
    nothing gets missed. CIKs with multiple filings will be taken care of by 
    the prune() function later
    '''
    #TODO: Update this to only add new filings. For now, this creates a new
    #      database every time
    #      Also need to delete quarters less than current quarter-3
    def handle_noargs(self, **options):

        year  = int(time.strftime("%Y"))
        month = int(time.strftime("%m"))
        if   month in range(1,4):  qtr = 1
        elif month in range(4,7):  qtr = 2
        elif month in range(7,10): qtr = 3
        else:                      qtr = 4
        for i in range(0,3):
            quarter = "%s%s" % (year,qtr)
            objs = get_filing_list(year,qtr)
            commitObjs(objs)
            qtr -= 1
            if qtr==0:
               qtr = 4
               year -= 1

