from screener.financials import *

# only keep most recent filings
prune()

# run nightly, although ticker only needs to be updated once
insertFinancials()

# only needs to run on new filings
insertXBRL()

#print net-nets, will add more filters later
print 'netnets:'
filings = Index.objects.all()
for filing in filings:
    if (filing.netnet()):
        print filing.ticker, filing.exchange
