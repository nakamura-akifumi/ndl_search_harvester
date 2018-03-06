from datetime import *
import glob
import kassis_config
import kassis_ndl_xmlloader
import csv
import os

def pickup(item):
    row = []
    row.append(item['dcterms_title'])
    return row

def xml2csv(importpath, exportpath):
    total_record = 0
    print(f"importpath={importpath} exportpath={exportpath}")

    files = glob.glob(importpath)
    for filename in files:
        jsonlist = kassis_ndl_xmlloader.xml2json(filename)
        if len(jsonlist) == 0:
            print("Warn: json data is zero")
        else:
            fn = os.path.basename(filename)
            name, ext = os.path.splitext(fn)
            jsonfilename = f"{name}.csv"
            writepath = os.path.join(exportpath, jsonfilename)

            with open(writepath, 'w') as csvfile:
                writer = csv.writer(csvfile, lineterminator='\n')
                # header
                writer.writerow(['タイトル'])

                for i in jsonlist:
                    writer.writerow(pickup(i))


    # end of loop

if __name__ == '__main__':
    print(f"@start time={datetime.now().strftime('%Y/%m/%d %H:%M:%S')}")

    config = kassis_config.get()

    importpath = config['xml2csv']['xml_import']
    exportpath = config['xml2csv']['csv_export']

    xml2csv(importpath, exportpath)

    print(f"@finish time={datetime.now().strftime('%Y/%m/%d %H:%M:%S')}")
