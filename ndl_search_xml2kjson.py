import os.path
from lxml import etree
from datetime import *
import time
from datetime import datetime
from elasticsearch import Elasticsearch
import glob
import json


def json2es():
    es = Elasticsearch()
    es.indices.create(index='my-index', ignore=400)
    es.index(index="my-index", doc_type="test-type", id=42, body={"any": "data", "timestamp": datetime.now()})
    print(es.get(index="my-index", doc_type="test-type", id=42)['_source'])


def xml2esjson(importpath, exportpath):
    total_record = 0
    print(f"importpath={importpath} exportpath={exportpath}")

    namespaces = {'ns': 'http://www.openarchives.org/OAI/2.0/',
                  'rdf': "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                  'rdfs': "http://www.w3.org/2000/01/rdf-schema#",
                  'dc': 'http://purl.org/dc/elements/1.1/',
                  'dcterms': 'http://purl.org/dc/terms/',
                  'foaf': 'http://xmlns.com/foaf/0.1/',
                  'owl': 'http://www.w3.org/2002/07/owl#'}

    files = glob.glob(importpath)
    for filename in files:
        tree = etree.parse(filename)
        root = tree.getroot()
        records = root.xpath('//ns:record', namespaces=namespaces)
        print(f"readfile name={filename} size={len(records)}")
        total_record += len(records)

        json_list = []

        for r in records:
            j = {}

            # 2-3-1
            x = r.find(".//dcterms:identifier[@rdf:datatype='http://ndl.go.jp/dcndl/terms/JPNO']",
                       namespaces=namespaces)
            j['jpno'] = x.text

            # 2-8
            x = r.find('.//dcterms:title', namespaces=namespaces)
            j['dcterms_title'] = x.text

            xl = r.findall('.//dc:title', namespaces=namespaces)

            # 2-42
            xl = r.findall('.//dcterms:creator', namespaces=namespaces)

            # 2-46
            xl = r.findall('.//dc:creator', namespaces=namespaces)
            j['creators'] = [x.text for x in xl]

            # print(j)
            json_list.append(j)

        # end of xml file
        jsonfilename = f"{filename}.json"
        writepath = os.path.join(exportpath, jsonfilename)
        jsontext = json.dumps(json_list, sort_keys=True, ensure_ascii=False, indent=2)
        with open(writepath, 'w') as f:
            f.write(jsontext)

    # ===
    print(f"total_record=#{total_record}")


if __name__ == '__main__':
    print(f"@start time={datetime.now().strftime('%Y/%m/%d %H:%M:%S')}")

    importpath = "D:\\data\\xml\\ndl_oaipmh_2013-06-22-11.xml"
    exportpath = "D:\\data\\json"

    xml2esjson(importpath, exportpath)

    print(f"@finish time={datetime.now().strftime('%Y/%m/%d %H:%M:%S')}")
