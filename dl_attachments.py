#!/usr/bin/env python
# encoding: utf-8
import math
import os
import re
import sys
import urllib2
import urlparse
from optparse import OptionParser

from lxml import etree
from lxml.html import soupparser

USAGE = "%prog <html dir>"

IMAGE_URL_PREFIX = "http://agateau.files.wordpress.com"

THUMBNAIL_PREFIX = "thumb_"

INPUT_DIR = "out"
OUTPUT_DIR = "out2"


def mkdir_p(dirname):
    if not os.path.exists(dirname):
        os.makedirs(dirname)


def download(url, dst):
    BUFFER = 16384

    real_dst = os.path.join(OUTPUT_DIR, dst)
    print "Downloading %s to %s" % (url, real_dst),
    if os.path.exists(real_dst):
        print "Skipping, already exists"
        return
    print

    mkdir_p(os.path.dirname(real_dst))
    dstf = open(real_dst, "w")

    srcf = urllib2.urlopen(url)
    length_str = srcf.info().get("content-length")
    if length_str and length_str.isdigit():
        length = float(length_str)
        print "_" * int(math.ceil(length / BUFFER))

    while True:
        chunk = srcf.read(BUFFER)
        if not chunk:
            break
        dstf.write(chunk)
        sys.stdout.write("#")
        sys.stdout.flush()
    print


def fake_download(url, dst):
    print "Would have downloaded %s" % url


def download_path_for_url(document_dir, url):
    result = urlparse.urlsplit(url)
    name = os.path.basename(result.path)
    if result.query:
        assert result.query.startswith("w=")
        name = THUMBNAIL_PREFIX + name
    return os.path.join(document_dir, name)


def process_elements(document_dir, parent, tag, attribute, download_function):
    def match(elt):
        value = elt.get(attribute)
        return value is not None and value.startswith(IMAGE_URL_PREFIX)
    elements = [x for x in parent.iter(tag) if match(x)]

    for elt in elements:
        url = elt.get(attribute)
        dest = download_path_for_url(document_dir, url)
        download_function(url, dest)
        elt.set(attribute, os.path.basename(dest))

        if tag == "a":
            css_class = elt.get("class", " ") + "image-reference"
            elt.set("class", css_class)


def read_header(fl):
    lst = []
    while True:
        line = fl.readline()
        if line != "\n":
            lst.append(line)
        else:
            break
    return "".join(lst) + "\n"


def process_file(filename, download_function):
    assert filename.startswith(INPUT_DIR)
    relative_filename = filename[len(INPUT_DIR) + 1:]
    out_filename = os.path.join(OUTPUT_DIR, relative_filename)
    document_dir = os.path.dirname(relative_filename)

    with open(filename) as f:
        header = read_header(f)

        # I don't use soupparser.parse(f) because I can't get it to properly
        # read utf-8!
        soup = unicode(f.read(), "utf-8")
        root = soupparser.fromstring(soup)

    print "# Images"
    process_elements(document_dir, root, "img", "src", download_function)
    print "# Links"
    process_elements(document_dir, root, "a", "href", download_function)

    mkdir_p(os.path.dirname(out_filename))

    with open(out_filename, "w") as f:
        f.write(header)
        html = etree.tostring(root)
        html = re.search("^<html>(.*)</html>$", html, re.DOTALL).group(1)
        f.write(html)


def main():
    parser = OptionParser(usage=USAGE)

    parser.add_option("-d", "--download",
                      action="store_true", dest="download", default=False,
                      help="Download images")

    (options, args) = parser.parse_args()

    if len(args) == 0:
        parser.error("Missing args")

    root = args[0]

    if options.download:
        download_function = download
    else:
        download_function = fake_download

    for dirname, dirs, filenames in os.walk(root):
        for filename in filenames:
            name = os.path.join(dirname, filename)
            print
            print "*** Processing %s ***" % name
            print
            process_file(name, download_function)
    return 0


if __name__ == "__main__":
    sys.exit(main())
# vi: ts=4 sw=4 et
