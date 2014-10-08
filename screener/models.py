from django.db import models
import sys
import os
import shutil
from pysec.models import Index
from django.db import models

'''Part of quick fix mentioned below for localcik'''
from django.conf import settings
DATA_DIR = settings.DATA_DIR

class Index(models.Model):

    ticker = models.CharField(max_length=6,blank=True)
    cik = models.IntegerField()

    '''
    This data is gathered using the Yahoo finance API
    '''

    exchange = models.TextField(blank=True)
    marketcap = models.TextField(blank=True)

    '''This is all the fields returned by the xbrl data
       For simplicity, these will all be TextField
    '''
    
    DocumentPeriodEndDate = models.TextField(blank=True)
    LinkToXBRLInstance = models.TextField(blank=True)
    NetCashFlowsContinuing = models.TextField(blank=True)
    NetCashFlowsFinancingDiscontinued = models.TextField(blank=True)
    NetIncomeAvailableToCommonStockholdersBasic = models.TextField(blank=True)
    NonoperatingIncomeLossPlusInterestAndDebtExpense = models.TextField(blank=True)
    NoncurrentLiabilities = models.TextField(blank=True)
    IncomeFromContinuingOperationsBeforeTax = models.TextField(blank=True)
    ContextForInstants = models.TextField(blank=True)
    Equity = models.TextField(blank=True)
    EntityFilerCategory = models.TextField(blank=True)
    DocumentType = models.TextField(blank=True)
    ContextForDurations = models.TextField(blank=True)
    NetCashFlowsOperatingContinuing = models.TextField(blank=True)
    OtherComprehensiveIncome = models.TextField(blank=True)
    ComprehensiveIncomeAttributableToNoncontrollingInterest = models.TextField(blank=True)
    NetCashFlowsInvestingContinuing = models.TextField(blank=True)
    ROS = models.TextField(blank=True)
    NetIncomeAttributableToParent = models.TextField(blank=True)
    SGR = models.TextField(blank=True)
    NetCashFlowsInvestingDiscontinued = models.TextField(blank=True)
    ROE = models.TextField(blank=True)
    PreferredStockDividendsAndOtherAdjustments = models.TextField(blank=True)
    NonoperatingIncomePlusInterestAndDebtExpensePlusIncomeFromEquityMethodInvestments = models.TextField(blank=True)
    NetCashFlowsOperating = models.TextField(blank=True)
    CostsAndExpenses = models.TextField(blank=True)
    CurrentAssets = models.TextField(blank=True)
    IncomeFromEquityMethodInvestments = models.TextField(blank=True)
    NoncurrentAssets = models.TextField(blank=True)
    EntityRegistrantName = models.TextField(blank=True)
    IncomeTaxExpenseBenefit = models.TextField(blank=True)
    CostOfRevenue = models.TextField(blank=True)
    ExchangeGainsLosses = models.TextField(blank=True)
    CurrentLiabilities = models.TextField(blank=True)
    Assets = models.TextField(blank=True)
    NetCashFlowsDiscontinued = models.TextField(blank=True)
    SECFilingPage = models.TextField(blank=True)
    LiabilitiesAndEquity = models.TextField(blank=True)
    OperatingIncomeLoss = models.TextField(blank=True)
    TemporaryEquity = models.TextField(blank=True)
    NonoperatingIncomeLoss = models.TextField(blank=True)
    OtherOperatingIncome = models.TextField(blank=True)
    EquityAttributableToParent = models.TextField(blank=True)
    GrossProfit = models.TextField(blank=True)
    TradingSymbol = models.TextField(blank=True)
    NetCashFlow = models.TextField(blank=True)
    DocumentFiscalYearFocus = models.TextField(blank=True)
    IncomeFromDiscontinuedOperations = models.TextField(blank=True)
    NetCashFlowsInvesting = models.TextField(blank=True)
    ComprehensiveIncome = models.TextField(blank=True)
    Revenues = models.TextField(blank=True)
    CommitmentsAndContingencies = models.TextField(blank=True)
    OperatingExpenses = models.TextField(blank=True)
    IncomeStatementPeriodYTD = models.TextField(blank=True)
    Liabilities = models.TextField(blank=True)
    NetCashFlowsFinancingContinuing = models.TextField(blank=True)
    EntityCentralIndexKey = models.TextField(blank=True)
    EquityAttributableToNoncontrollingInterest = models.TextField(blank=True)
    ComprehensiveIncomeAttributableToParent = models.TextField(blank=True)
    DocumentFiscalPeriodFocus = models.TextField(blank=True)
    NetIncomeLoss = models.TextField(blank=True)
    IncomeBeforeEquityMethodInvestments = models.TextField(blank=True)
    NetCashFlowsOperatingDiscontinued = models.TextField(blank=True)
    FiscalPeriod = models.TextField(blank=True)
    BalanceSheetDate = models.TextField(blank=True)
    PeriodStartDate = models.TextField(blank=True)
    NetCashFlowsFinancing = models.TextField(blank=True)
    ROA = models.TextField(blank=True)
    ExtraordaryItemsGainLoss = models.TextField(blank=True)
    IncomeFromContinuingOperationsAfterTax = models.TextField(blank=True)
    NetIncomeAttributableToNoncontrollingInterest = models.TextField(blank=True)
    InterestAndDebtExpense = models.TextField(blank=True)
    FiscalYear = models.TextField(blank=True)
    
    class Meta:
        pass

    '''
    Remove the directory holding all xbrl data for this cik. This is necessary
    to free up disk space. All xbrl data would take up several GB of storage
    '''
    def rmlocalcik(self):
        try:
            shutil.rmtree(self.localcik())
        except:
            print "Unexpected error removing cik dir:", sys.exc_info()
            pass

    #TODO: Modify this to specify percent of netnet (mktcap/NCAV, not just True/False)
    #      Will probably migrate to a more robust screener with configurable options
    def netnet(self):

       if self.marketcap == '' or self.CurrentAssets == None or self.Liabilities == None:
           return False
       if self.marketcap == 'N/A':
           return False
       suffix = self.marketcap[-1]
       mktcap = float(self.marketcap[0:-1])
       if suffix == 'K':
           mktcap *= 1000
       elif suffix == 'M':
           mktcap *= 1000000
       elif suffix == 'B':
          mktcap *= 1000000000
       else:
          return False
       try:
           return ( mktcap / (float(self.CurrentAssets) - float(self.Liabilities)) < .7) and \
                  ( mktcap / (float(self.CurrentAssets) - float(self.Liabilities)) > 0)
       except:
           return False

    '''localcik is defined in pysec models, but needed for this model
       There is probably a better way to handle this, but this works for now.
       This problem came up when trying to separate pysec and screener tables.
    '''
    def localcik(self):
        return '%s/%s/' % (DATA_DIR, self.cik)
