#!/home/sumup/anaconda2/bin/python
# -*- coding: utf-8 -*-

import os
import os.path
import sys
import hashlib
from time import gmtime, strftime
import json

print(os.path.dirname(os.path.abspath(__file__)) + "/tika-app-1.10.jar")

os.environ['CLASSPATH'] = os.path.dirname(os.path.abspath(__file__)) + "/tika-app-1.10.jar"

from jnius import autoclass

# Import Java classes
Tika = autoclass('org.apache.tika.Tika')
Metadata = autoclass('org.apache.tika.metadata.Metadata')
FileInputStream = autoclass('java.io.FileInputStream')

extr_files = set(['.xls', '.xlsx', '.ppt', '.pptx', '.doc', '.docx', 
                  '.odt', '.ods', '.odg', '.odp', '.pdf', '.html'])

documents = []

def get_txt(fname):
    tika = Tika()
    meta = Metadata()
    tika.parseToString(FileInputStream(fname), meta)
    text = tika.parseToString(FileInputStream(fname), meta)
###this prints all metadata:
    #dump_metadata(meta)
    return (meta,text)

def dump_text(pathname):
    pass

def dump_metadata(meta):
    ''' output the metadata returned by Tika on screen '''
    print('==================== METADATA: ====================')
    metadataNames = meta.names();
    for name in metadataNames:		        
         print(name + ": " + meta.get(name));
    print('===================================================')

def json_from_tika(meta,txt,filename,pathname):
    ''' generate a document object that can be dumped with
    json.dumps() and then sent to anseri for analysis'''
    document = {
        'filename':os.path.splitext(filename)[0],
        'fullpath':pathname,
        'title':meta.get('title').decode('utf-8') if (meta.get('title') is not None) else None,
        'created':meta.get('created'),
        'author':meta.get('Author'),
        'text':txt.decode('utf-8'), #use [:20] to truncate for testing
        'checksum': hashlib.md5(pathname.encode('utf-8')).hexdigest(),
        'acquired_on': strftime("%d %b %Y %X +0000", gmtime())
    }
    return document

def walktree(top):
    ''' recursively descend the directory tree rooted at top,
    searching for interesting files and converting to text.
    Populates the global variable 'documents' with them'''
    for f in os.listdir(top):
        pathname = os.path.join(top, f)
        print(pathname)
        if os.path.isdir(pathname):
            # It's a directory, recurse into it
            walktree(pathname)
        elif os.path.isfile(pathname):
            # It's a file, but do we care about?
            extension = os.path.splitext(pathname)[1]
            if extension in extr_files:
                print top, pathname
                tn = ''.join((os.path.splitext(f)[0], '.txt'))
                tname = os.path.join(top, tn)
                meta,txt = get_txt(pathname)
                documents.append(json_from_tika(meta,txt,f,pathname))
        else:
            print('Skipping %s' % pathname)


if __name__ == '__main__':
    if (len(sys.argv)!=2):
        print("USAGE: dump_json.py /path/to/folder/containing/the/files")
        exit(1)
    top = sys.argv[1]
    #use utf-8 as file paths may contain non-ascii strings
    walktree(top.decode('utf-8'))
    output = json.dumps(documents, ensure_ascii=False, sort_keys=True, indent=4, separators=(',', ': '))
    with open('./output.json', 'w') as fd:
        fd.write(output.encode('utf-8'))

