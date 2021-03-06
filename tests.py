import unittest
import datetime
from decimal import Decimal
from hnbexchange import RateFrame, HNBExtractor

try:
    from mock import patch
except ImportError:
    from unittest.mock import patch


sample_raw_data = """147300720133107201313
036AUD001       5,101517       5,116868       5,132219
124CAD001       5,477994       5,494477       5,510960
203CZK001       0,288837       0,289706       0,290575
208DKK001       1,001785       1,004799       1,007813
348HUF100       2,498361       2,505879       2,513397
392JPY100       5,742983       5,760264       5,777545
578NOK001       0,947629       0,950480       0,953331
752SEK001       0,860322       0,862911       0,865500
756CHF001       6,053503       6,071718       6,089933
826GBP001       8,613150       8,639067       8,664984
840USD001       5,628279       5,645215       5,662151
978EUR001       7,467601       7,490071       7,512541
985PLN001       1,767438       1,772756       1,778074"""


class TestHNBExtractor(unittest.TestCase):

    def setUp(self):
        self.extractor = HNBExtractor(sample_raw_data)

    def test_header_data(self):
        header = self.extractor.header
        self.assertEqual(header['rate_id'], 147)
        self.assertEqual(header['creation_date'], datetime.date(2013, 7, 30))
        self.assertEqual(header['application_date'], datetime.date(2013, 7, 31))
        self.assertEqual(header['items'], 13)

    def test_rates_data(self):
        rates = self.extractor.rates
        rate = rates[0]
        self.assertEqual(len(rates), self.extractor.header['items'])
        self.assertEqual(rate['currency_code'], 'AUD')
        self.assertEqual(rate['unit_value'], 1)
        self.assertEqual(rate['buying_rate'], Decimal('5.101517'))
        self.assertEqual(rate['median_rate'], Decimal('5.116868'))
        self.assertEqual(rate['selling_rate'], Decimal('5.132219'))

    def test_insufficient_data(self):
        data = ""
        self.assertRaises(ValueError, HNBExtractor, data)

    def test_invalid_header_format(self):
        data = """......\n................"""
        self.assertRaises(ValueError, HNBExtractor, data)

    def test_valid_header_but_invalid_rates(self):
        data = """147300720133107201313\nxxx123xxx     1       2       3"""
        self.assertRaises(ValueError, HNBExtractor, data)


class FakeRequest(object):

    def __init__(self, url):
        if url == 'http://www.hnb.hr/tecajn/f300713.dat':
            self.ok = True
            self.text = sample_raw_data
        else:
            self.ok = False
            self.text = ""


class TestRateFrame(unittest.TestCase):

    def setUp(self):
        self.ref_date = datetime.date(2013, 7, 30)

    def test_full_url(self):
        rf = RateFrame(self.ref_date)
        url = 'http://www.hnb.hr/tecajn/f300713.dat'
        self.assertEqual(rf.full_url(self.ref_date), url)

    def test_retrieve_date_fallback(self):
        # we mock requests.get to test condition when data for requested date is
        # not available (404, r.ok==False). If that happens RateFrame object
        # then iterates backwards throught dates until it successfully
        # retrieves some data (which for this test is faked as 2 days before
        # requested date)

        date = self.ref_date + datetime.timedelta(2)
        rf = RateFrame(date)
        with patch('requests.get', FakeRequest):
            rf.retrieve()
            rates = rf.data.rates
            rate = rates[0]
            self.assertEqual(len(rates), rf.data.header['items'])
            self.assertEqual(rf.date, self.ref_date)
            self.assertEqual(rate['currency_code'], 'AUD')
            self.assertEqual(rate['unit_value'], 1)
            self.assertEqual(rate['buying_rate'], Decimal('5.101517'))

    def test_get_rate(self):
        rf = RateFrame(self.ref_date)
        with patch('requests.get', FakeRequest):
            rf.retrieve()
            rate = rf.get_rate('EUR')
            self.assertEqual(rate['currency_code'], 'EUR')
            self.assertEqual(rate['unit_value'], 1)
            self.assertEqual(rate['buying_rate'], Decimal('7.467601'))


if __name__ == '__main__':
    unittest.main()
