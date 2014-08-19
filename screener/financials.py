#!/usr/bin/python

import sys
import urllib
import socket
import re
from pysec.models import Index as pysec_index
from screener.models import *

# Define a context manager to suppress stdout and stderr.
class suppress_stdout_stderr(object):
    '''
    A context manager for doing a "deep suppression" of stdout and stderr in 
    Python, i.e. will suppress all print, even if the print originates in a 
    compiled C/Fortran sub-function.
       This will not suppress raised exceptions, since exceptions are printed
    to stderr just before a script exits, and after the context manager has
    exited (at least, I think that is why it lets exceptions through).      

    '''
    def __init__(self):
        # Open a pair of null files
        self.null_fds =  [os.open(os.devnull,os.O_RDWR) for x in range(2)]
        # Save the actual stdout (1) and stderr (2) file descriptors.
        self.save_fds = (os.dup(1), os.dup(2))

    def __enter__(self):
        # Assign the null pointers to stdout and stderr.
        os.dup2(self.null_fds[0],1)
        os.dup2(self.null_fds[1],2)

    def __exit__(self, *_):
        # Re-assign the real stdout/stderr back to (1) and (2)
        os.dup2(self.save_fds[0],1)
        os.dup2(self.save_fds[1],2)
        # Close the null files
        os.close(self.null_fds[0])
        os.close(self.null_fds[1])

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
            # output will still go to a file if redirected there (instead of stdout)
            with suppress_stdout_stderr():
                x = filing.xbrl()
            if count > 35*24: # keep first 840 on harddisk for debug purposes
                filing.rmlocalcik()
        except:
            #filing.error = 'XBRL filing exception'
            #filing.save()
            continue

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

