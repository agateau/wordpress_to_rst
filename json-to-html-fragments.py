#!/usr/bin/env python
import errno
import os
import json
import re
import sys
import xml.sax.saxutils

from optparse import OptionParser
from datetime import datetime

from pygments import highlight
from pygments.lexers import get_lexer_by_name, TextLexer
from pygments.formatters import HtmlFormatter

USAGE = "%prog <json-file>"

def fix_paragraphs(txt):
    def fix_paragraph(txt):
        def wrap_p(txt):
            if txt.startswith('<'):
                return txt
            else:
                return '<p>' + txt + '</p>'

        if txt.startswith('<pre'):
            return txt
        paras = txt.split('\n\n')
        return '\n'.join(wrap_p(x) for x in paras)

    rx = re.compile('(<pre[ >].*?</pre>)', re.DOTALL)
    src = rx.split(txt)
    dst = [fix_paragraph(x) for x in src]
    return ''.join(dst)


def format_source_code(txt):
    def unescape(txt):
        return xml.sax.saxutils.unescape(txt, {'&quot;': '"'})

    def pygmentize(match):
        language = match.group(1)
        txt = unescape(match.group(2))
        try:
            lexer = get_lexer_by_name(language)
        except ValueError:
            print "WARNING: no lexer found for language '%s'" % language
            lexer = TextLexer()
        return highlight(txt, lexer, HtmlFormatter())

    rx = re.compile('\[sourcecode language="?([a-z]+)"?\]\n*(.*?)\n*\[/sourcecode\]', re.DOTALL)
    return rx.sub(pygmentize, txt)

VIDEO_RX_LIST = [
    (
        re.compile('\[vimeo (?P<id>\d+)\]'),
        '<a class="vimeo" href="http://www.vimeo.com/\g<id>">Video</a>'
    ),
]

def format_videos(txt):
    for rx, replacement in VIDEO_RX_LIST:
        txt = rx.sub(replacement, txt)
    return txt


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
            content = item[u'content']
            content = format_source_code(content)
            content = format_videos(content)
            content = fix_paragraphs(content)

            print >> outfile, 'public: ' + status
            print >> outfile, ('tags: [%s]' % ','.join(quote(x) for x in tags)).encode('utf-8')
            print >> outfile, 'title: ' + quote(item[u'title']).encode('utf-8')
            print >> outfile
            print >> outfile, content.encode('utf-8')

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
