import os.path
from lxml import etree
from datetime import *
import time
from elasticsearch import Elasticsearch
import glob
import json
import re
from urllib.parse import urlparse
import platform
import kassis_config

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

        record_line = 0
        for r in records:
            record_line = record_line + 1
            try:
                j = {}
                deleted_flag = False

                # 1-3
                x = r.find(".//dcndl:BibAdminResource",
                           namespaces=ns)
                if x is None:
                    x = r.find(".//ns:header", namespaces=ns)
                    for k, v in x.attrib.items():
                        if v == "deleted":
                            deleted_flag = True
                            print("WARN: this record is deleted. continue.")
                            for xl in x:
                                print(xl.tag, xl.text)

                if deleted_flag:
                    continue

                for k, v in x.attrib.items():
                    j['ndl_resource_about'] = v
                    break

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
                    v = x.find('.//rdf:Description/rdf:value', namespaces=ns)
                    if v is not None:
                        transcription = ""
                        t = r.find('.//rdf:Description/dcndl:transcription', namespaces=ns)
                        if t is not None:
                            transcription = t.text

                        xla.append({"value": v.text,
                                    "transcription": transcription
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

                # 2-59
                xla = []
                xl = r.findall(".//dcterms:date", namespaces=ns)
                for x in xl:
                    xla.append(x.text)

                j['pubdate_label'] = xla

                # 2-60
                xla = []
                xl = r.findall(".//dcterms:issued", namespaces=ns)
                for x in xl:
                    xla.append(x.text)

                j['issued'] = xla

                # 2-59 + 2-60

                # 2-69
                xla = []
                xl = r.findall(".//dcndl:partInformation", namespaces=ns)
                for x in xl:
                    jj = {}
                    jj['desc_title'] = x.find('.//rdf:Description/dcterms:title', namespaces=ns).text
                    if x.find('.//rdf:Description/dcndl:transcription', namespaces=ns):
                        jj['desc_transcription'] = x.find('.//rdf:Description/dcndl:transcription', namespaces=ns).text
                    if x.find('.//rdf:Description/dcterms:description', namespaces=ns):
                        jj['desc_desc'] = x.find('.//rdf:Description/dcterms:description', namespaces=ns).text
                    if x.findall('.//rdf:Description/dc:creator', namespaces=ns):
                        jj['desc_creator'] = [xx.text for xx in
                                              x.findall('.//rdf:Description/dc:creator', namespaces=ns)]

                    xla.append(jj)

                j['part_infos'] = xla

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

                # misc.
                j['id'] = j['jpno']

                # print(j)
                json_list.append(j)
            except AttributeError as err:
                print(f"Attribute error record_line={record_line} :{format(err)}")

        # end of xml file
        fn = os.path.basename(filename)
        name, ext = os.path.splitext(fn)
        jsonfilename = f"{name}.json"
        writepath = os.path.join(exportpath, jsonfilename)

        print(f"writepath={writepath}")

        # output_type = "json"
        output_type = "es"
        if output_type == "json":
            json_text = json.dumps(json_list, ensure_ascii=False, indent=2)
            with open(writepath, 'w', encoding='utf8') as f:
                f.write(json_text)
        else:
            with open(writepath, 'w', encoding='utf8') as f:
                for j in json_list:
                    f.write('{ "create":  { "_index": "kassis", "_type": "manifestations", "_id":' + j['id'] + '}}\n')

                    json_text = json.dumps(j, ensure_ascii=False)
                    json_text += "\n"
                    f.write(json_text)


    # ===
    print(f"total_record={total_record}")


if __name__ == '__main__':
    print(f"@start time={datetime.now().strftime('%Y/%m/%d %H:%M:%S')}")

    config = kassis_config.get()

    importpath = config['xml2kson']['xml_import']
    exportpath = config['xml2kson']['es_export']

    xml2esjson(importpath, exportpath)

    print(f"@finish time={datetime.now().strftime('%Y/%m/%d %H:%M:%S')}")
