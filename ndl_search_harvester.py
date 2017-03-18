import urllib.request
import requests
import os.path
from lxml import etree
from datetime import *

# lxml package for windows (http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml)
# get lxml‑3.7.3‑cp36‑cp36m‑win_amd64.whl
# pip install lxml-3.7.3-cp36-cp36m-win_amd64.whl

# references
# http://ailaby.com/ndl_search/

def fetch_from_ndl(date_from, date_until):
    base_url = "http://iss.ndl.go.jp/api/oaipmh"

    params = {}
    params['verb'] = "ListRecords"
    params['metadataPrefix'] = "dcndl"
    params['set'] = "iss-ndl-opac-national"

    if date_from is None:
        date_from = datetime.today()
    if date_until is None:
        date_until = datetime.today() + 1

    params['from'] = date_from.strftime('%Y-%m-%d')
    params['until'] = date_until.strftime('%Y-%m-%d')

    print(f"start request {base_url}")

    index = 0
    total_record_cnt = 0
    s = requests.session()

    while True:
        print("params", params)
        r = s.get(base_url, params=params)
        print(f"status={r.status_code}")
        if r.status_code != 200:
            break

        root = etree.fromstring(r.text.encode('utf-8'))

        records = root.xpath('//ns:record', namespaces={'ns': 'http://www.openarchives.org/OAI/2.0/'})
        total_record_cnt = total_record_cnt + len(records)

        # store
        folder = "c:\\tmp"
        filename = f"ndl_oaipmh_{params['from']}-{index}.xml"
        writepath = os.path.join(folder, filename)

        with open(writepath, 'wb') as f:
            f.write(r.content)

        print(f"index=#{index} records={len(records)} / parse resumptionToken")

        params['resumptionToken'] = None
        resumption_tokens = root.xpath('//ns1:ListRecords/ns2:resumptionToken',
                                       namespaces={'ns1': 'http://www.openarchives.org/OAI/2.0/',
                                                   'ns2': 'http://www.openarchives.org/OAI/2.0/'})
        if len(resumption_tokens) == 1:
            x = resumption_tokens[0]
            params['resumptionToken'] = x.text

        if resumption_tokens is None or len(resumption_tokens) == 0 or params['resumptionToken'] is None:
            break

        index = index + 1

    ##################
    print("===")
    print(f"total read = {index}")
    print(f"total record count = {total_record_cnt}")


if __name__ == '__main__':
    # tdatetime_from = datetime.now()
    tdatetime_from = datetime(2013, 7, 14)
    tdatetime_until = tdatetime_from + timedelta(days=1)
    fetch_from_ndl(tdatetime_from, tdatetime_until)
