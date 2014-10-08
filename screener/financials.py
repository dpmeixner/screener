#!/usr/bin/python

import sys
import urllib
import socket
import re
from pysec.models import Index as pysec_index
from screener.models import *

def outputCounter(count):

    ''' Prints 'count: %s' and resets the cursor to the beginning of the line
        so that the count value gets updated in place. If output is redirected
        to a file, this will show a lot of '\b' characters
    '''

    sys.stdout.write("count: %s" % count)
    sys.stdout.flush()
    sys.stdout.write("\b" * 11)


def prune():

    # get unique list of ciks
    ciks = set(pysec_index.objects.values_list('cik'))
    print '# of filings before pruning: ', pysec_index.objects.count()
    for cik in ciks:
        filings = pysec_index.objects.filter(cik = cik[0])
        dates = filings.values_list('date')
        # only keep the most recent
        pysec_index.objects.filter(cik = cik[0]).exclude(date = max(dates)[0]).delete()
    print '# of filings after pruning: ', pysec_index.objects.count()

def insertFinancials():

   count = 1
   socket.setdefaulttimeout(30)
   ciks = pysec_index.objects.values_list('cik')

   for cik in ciks:
       
       outputCounter(count)

       # The cik should be unique in the table
       filing = Index.objects.filter(cik=cik[0])
       if filing.count() == 0:
           # This cik does not exist, so create it
           filing = Index(cik=cik[0])
       elif filing.count > 1:
           #TODO: would be more appropriate to remove duplicate cik records in prune()
           filing = filing[0]
       count += 1

       # Get the ticker, only if it doesn't exist
       if filing.ticker == '':
           url = "http://google.brand.edgar-online.com/?cik=%d" % cik[0]
           try:
               fileprops = urllib.urlretrieve(url)
           except IOError:
               continue
           else:
               f = file(fileprops[0])
               line = f.read()	
               ticker = re.match('.*\?ticker=(.*?)\"', line, re.DOTALL)
               try:
                   ticker = ticker.group(1)
               except:
                   filing.ticker = 'N/A'
                   filing.save()
       else:
           ticker = filing.ticker

       #print ticker
       if filing.ticker == 'N/A':
          continue

       if len(ticker) > 0:
           try:
               #TODO: should be possible to grab 200 records in one urlretrieve() call
               fn = urllib.urlretrieve("http://finance.yahoo.com/d/quotes.csv?s=" + ticker + "&f=xj1")
           except IOError:
               Exchange = ''
               MarketCap = ''
           else:
               f = file(fn[0])
               result = f.read().split(',')
               Exchange = result[0].strip()
               MarketCap = result[1].strip()
       else: # no ticker found
           Exchange = ''
           MarketCap = ''

       filing.ticker = ticker
       filing.exchange = Exchange
       filing.marketcap = MarketCap
       filing.save()

#TODO: Do a second pass on any IOError rows?

def insertXBRL():

    ciks = pysec_index.objects.values_list('cik')
    socket.setdefaulttimeout(30)

    count = 1
    for cik in ciks:
        print count, cik[0]
        count += 1
        #print 'cik is ', cik[0]
        #TODO: figure out how to handle multiple records with same cik, this is not optimal
        try:
            filing = pysec_index.objects.get(cik=cik[0])
        except:
            filing = pysec_index.objects.filter(cik=cik[0])[0]

        # initialize XBRL parser and populate assets and liability information
        #TODO: investigate what is causing the exception when xbrl data exists
        try:
            x = filing.xbrl()
        except:
            if count > 100: # keep first 100 on harddisk for debug purposes
                try:
                    Index.objects.get(cik=cik[0]).rmlocalcik()
                except:
                    Index.objects.filter(cik=cik[0])[0].rmlocalcik()
            #filing.error = 'XBRL filing exception'
            #filing.save()
            continue
        else:
            if count > 100:
                try:
                    Index.objects.get(cik=cik[0]).rmlocalcik()
                except:
                    Index.objects.filter(cik=cik[0])[0].rmlocalcik()

        if x is None:
            #filing.error = 'XBRL file DNE'
            # TODO: when run on BBB, database is locked and this errors out
            #filing.save()
            continue;

        #filing.save()

        # Sometimes this field is null, which throws an exception. This is a 
        # quick fix, but worth investigating further
        if x.fields['ContextForInstants'] == None:
            x.fields['ContextForInstants'] = "ERROR"

        Index.objects.filter(cik=cik[0]).update(**x.fields)

