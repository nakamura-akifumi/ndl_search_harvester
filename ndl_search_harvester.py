import urllib.request
import requests
import os.path
from lxml import etree

# lxml package for windows (http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml)
# get lxml‑3.7.3‑cp36‑cp36m‑win_amd64.whl
# pip install lxml-3.7.3-cp36-cp36m-win_amd64.whl

# references
# http://ailaby.com/ndl_search/
# http://ymotongpoo.hatenablog.com/entry/20110729/1311900747

base_url = "http://iss.ndl.go.jp/api/oaipmh"
query = "verb=ListRecords&metadataPrefix=dcndl&set=iss-ndl-opac-national&from=2013-07-15&until=2013-07-16"

params = {}
params['verb'] = "ListRecords"
params['metadataPrefix'] = "dcndl"
params['set'] = "iss-ndl-opac-national"
params['from'] = "2013-07-15"
params['until'] = "2013-07-16"

print(f"start request {base_url}")

index = 0
total_record_cnt = 0
s = requests.session()

while True:
    print("params", params)
    r = s.get(base_url, params=params)
    print(f"status={r.status_code}")

    root = etree.fromstring(r.text.encode('utf-8'))

    records = root.xpath('//ns:record', namespaces={'ns': 'http://www.openarchives.org/OAI/2.0/'})
    total_record_cnt = total_record_cnt + len(records)

    # store
    folder = "c:\\tmp"
    filename = f"ndl_oaipmh_{index}.xml"
    writepath = os.path.join(folder, filename)

    str = r.text.encode('utf-8')
    f = open(writepath, 'w')
    f.write(str)
    f.close()

    print(f"index=#{index} records={len(records)} / parse resumptionToken")

    params['resumptionToken'] = None
    resumption_tokens = root.xpath('//ns1:ListRecords/ns2:resumptionToken',
                                   namespaces={'ns1': 'http://www.openarchives.org/OAI/2.0/',
                                               'ns2': 'http://www.openarchives.org/OAI/2.0/'})
    if (len(resumption_tokens) == 1):
        x = resumption_tokens[0]
        params['resumptionToken'] = x.text

    if resumption_tokens == None or len(resumption_tokens) == 0 or params['resumptionToken'] == None:
        break

    index = index + 1

##################
print("===")
print(f"total read = {index}")
print(f"total record count = {total_record_cnt}")
