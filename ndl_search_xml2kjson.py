import os.path
from lxml import etree
from datetime import *
import time
from datetime import datetime
from elasticsearch import Elasticsearch
import glob
import json
import re
from urllib.parse import urlparse

def json2es():
    es = Elasticsearch()
    es.indices.create(index='my-index', ignore=400)
    es.index(index="my-index", doc_type="test-type", id=42, body={"any": "data", "timestamp": datetime.now()})
    print(es.get(index="my-index", doc_type="test-type", id=42)['_source'])


def xml2esjson(importpath, exportpath):
    total_record = 0
    print(f"importpath={importpath} exportpath={exportpath}")

    ns = {'ns': 'http://www.openarchives.org/OAI/2.0/',
                  'rdf': "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                  'rdfs': "http://www.w3.org/2000/01/rdf-schema#",
                  'dc': 'http://purl.org/dc/elements/1.1/',
                  'dcterms': 'http://purl.org/dc/terms/',
          'dcndl': 'http://ndl.go.jp/dcndl/terms/',
                  'foaf': 'http://xmlns.com/foaf/0.1/',
                  'owl': 'http://www.w3.org/2002/07/owl#'}

    files = glob.glob(importpath)
    for filename in files:
        tree = etree.parse(filename)
        root = tree.getroot()
        records = root.xpath('//ns:record', namespaces=ns)
        print(f"readfile name={filename} size={len(records)}")
        total_record += len(records)

        json_list = []

        for r in records:
            j = {}

            # 2-3-1
            x = r.find(".//dcterms:identifier[@rdf:datatype='http://ndl.go.jp/dcndl/terms/JPNO']",
                       namespaces=ns)
            j['jpno'] = x.text

            # 2-6-1
            xl = r.findall(".//dcterms:identifier[@rdf:datatype='http://ndl.go.jp/dcndl/terms/ISBN']",
                           namespaces=ns)
            j['isbn'] = [x.text for x in xl]

            # 2-8
            x = r.find('.//dcterms:title', namespaces=ns)
            j['dcterms_title'] = x.text

            xl = r.findall('.//dc:title', namespaces=ns)
            xla = []
            for x in xl:
                if r.find('.//rdf:Description/rdf:value', namespaces=ns):
                    xla.append({"value": r.find('.//rdf:Description/rdf:value', namespaces=ns).text,
                                "transcription": r.find('.//rdf:Description/dcndl:transcription', namespaces=ns).text
                                })
            j['dc_titles'] = xla

            # 2-42
            xl = r.findall('.//dcterms:creator', namespaces=ns)

            # 2-46
            xl = r.findall('.//dc:creator', namespaces=ns)
            j['creators'] = [x.text for x in xl]

            # 2-51
            xla = []
            xl = r.findall('.//dcterms:publisher', namespaces=ns)
            for x in xl:
                jj = {}
                jj['name'] = x.find('.//foaf:Agent/foaf:name', namespaces=ns).text

                t = x.find('.//foaf:Agent/dcndl:transcription', namespaces=ns)
                if t is not None:
                    jj['transcription'] = t.text

                t = x.find('.//foaf:Agent/dcterms:description', namespaces=ns)
                if t is not None:
                    jj['description'] = t.text

                t = x.find('.//foaf:Agent/dcndl:location', namespaces=ns)
                if t is not None:
                    jj['location'] = t.text

                xla.append(jj)

            j['publishers'] = xla

            # 2-81-n/2-82-n
            xla = []
            # 1st:2-81-n
            xl = r.findall(".//dcterms:subject", namespaces=ns)
            for x in xl:
                for k, v in x.attrib.items():
                    if k == "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource":
                        o = urlparse(v)
                        m = re.match(r"/class/(\w+)/(\w+)", o.path)
                        if m:
                            # print(m.group(1), m.group(2))
                            xla.append({m.group(1): m.group(2)})


            # 2nd:2-82-n
            xl = r.findall(".//dc:subject", namespaces=ns)
            for x in xl:
                for k, v in x.attrib.items():
                    if v in {"http://ndl.go.jp/dcndl/terms/NDC",
                             "http://ndl.go.jp/dcndl/terms/NDC8",
                             "http://purl.org/dc/terms/LCC",
                             "http://purl.org/dc/terms/UDC"}:
                        o = urlparse(v)
                        m = re.match(r"/(\w+)/terms/(\w+)", o.path)
                        xla.append({m.group(2): x.text})

            j['classes'] = xla

            # 2-83
            xl = r.findall(".//dcterms:language[@rdf:datatype='http://purl.org/dc/terms/ISO639-2']",
                           namespaces=ns)
            j['languages'] = [x.text for x in xl]

            # 2-84
            xl = r.findall(".//dcndl:originalLanguage[@rdf:datatype='http://purl.org/dc/terms/ISO639-2']",
                           namespaces=ns)
            j['original_languages'] = [x.text for x in xl]

            # 2-85
            xl = r.findall(".//dcndl:price", namespaces=ns)
            j['price'] = [x.text for x in xl]

            # 2-86
            xl = r.findall(".//dcterms:extent", namespaces=ns)
            j['extent'] = [x.text for x in xl]

            # 2-89
            xla = []
            xl = r.findall(".//dcndl:materialType", namespaces=ns)
            for x in xl:
                for k, v in x.attrib.items():
                    o = urlparse(v)
                    m = re.match(r"/ndltype/(\w+)", o.path)
                    if m:
                        xla.append(m.group(1))

            j['matrialtype'] = xla

            # print(j)
            json_list.append(j)

        # end of xml file
        fn = os.path.basename(filename)
        name, ext = os.path.splitext(fn)
        jsonfilename = f"{name}.json"
        writepath = os.path.join(exportpath, jsonfilename)

        print(f"writepath={writepath}")

        json_text = json.dumps(json_list, sort_keys=True, ensure_ascii=False, indent=2)

        with open(writepath, 'w', encoding='utf8') as f:
            f.write(json_text)

    # ===
    print(f"total_record={total_record}")


if __name__ == '__main__':
    print(f"@start time={datetime.now().strftime('%Y/%m/%d %H:%M:%S')}")

    # importpath = "D:\\data\\xml\\ndl_oaipmh_2013-06-22-4789.xml"
    importpath = "D:\\data\\xml\\ndl_oaipmh_2013-06-22-1043.xml"

    exportpath = "D:\\data\\json"

    xml2esjson(importpath, exportpath)

    print(f"@finish time={datetime.now().strftime('%Y/%m/%d %H:%M:%S')}")
