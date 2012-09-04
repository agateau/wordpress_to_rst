#!/usr/bin/env python
import errno
import os
import json
import sys

from optparse import OptionParser
from datetime import datetime

USAGE = "%prog <json-file>"

def fix_paragraphs(txt):
    paras = txt.split('\n\n')
    return '\n'.join('<p>' + x + '</p>' for x in paras)

def quote(txt):
    return '"' + txt.replace('"', r'\"') + '"'

def post_dir_formatter(item):
    dt = datetime.strptime(item[u'post_date'], '%Y/%m/%d %H:%M:%SZ')
    return '%04d/%02d/%02d/%s' % (dt.year, dt.month, dt.day, item[u'name'])

def page_dir_formatter(item):
    """
    path = urlparse.urlsplit(item['link'])[2]
    path = path.strip('/')
    """
    path = item[u'name']
    if not path:
        path = item[u'title'].lower()
    assert path
    return path

def process_items(items, dir_formatter):
    for item in items:
        title = item[u'title']
        path = dir_formatter(item)

        print '"%s" => %s' % (title, path)

        try:
            os.makedirs('out/%s' % path)
        except OSError, e:
            if e.errno != errno.EEXIST:
                raise

        with open('out/%s/index.html' % path, 'w') as outfile:
            tags = item[u'categories'] + item[u'tags']
            status = item[u'status'] == 'publish' and 'yes' or 'no'
            print >> outfile, 'public: ' + status
            print >> outfile, ('tags: [%s]' % ','.join(quote(x) for x in tags)).encode('utf-8')
            print >> outfile, 'title: ' + quote(item[u'title']).encode('utf-8')
            print >> outfile
            print >> outfile, fix_paragraphs(item[u'content']).encode('utf-8')

def main():
    parser = OptionParser(usage=USAGE)
    parser.add_option("-b", "--blog",
                      action="store_true", dest="posts", default=False,
                      help="Process blog posts")
    parser.add_option("-p", "--pages",
                      action="store_true", dest="pages", default=False,
                      help="Process pages")
    (options, args) = parser.parse_args()

    if len(args) == 0:
        parser.error("Missing args")

    if not options.posts and not options.pages:
        parser.error("At least one of --blog or --pages options should be set")

    infile = open(args[0], 'r')
    tree = json.loads(infile.read())

    if options.posts:
        print "# Processing blog posts"
        process_items(tree["posts"], post_dir_formatter)
    if options.pages:
        print "# Processing pages"
        process_items(tree["pages"], page_dir_formatter)

    return 0

if __name__ == "__main__":
    sys.exit(main())
# vi: ts=4 sw=4 et
