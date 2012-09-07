#!/usr/bin/env python
# encoding: utf-8
import os
import re
import sys
import json
import urllib
import urllib2
import urlparse
from optparse import OptionParser

USAGE = "%prog <html dir>"

INPUT_DIR = "out2"


def mkdir_p(dirname):
    if not os.path.exists(dirname):
        os.makedirs(dirname)


BLIP_FILE_ID_FOR_URL = json.load(open("blip-map.json"))


def replacer_for_blip_redirected_url(match):
    url = match.group(1)
    file_id = BLIP_FILE_ID_FOR_URL[url]
    return "http://blip.tv/file/%s" % file_id


def query_oembed(endpoint, video_url, args):
    args = dict(args)
    args["url"] = video_url
    query = urllib.urlencode(args)
    url = endpoint + "?" + query
    request = urllib2.Request(url)

    # Required for vimeo :/ otherwise we get a 404!
    request.add_header("User-Agent", "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0")

    fl = urllib2.urlopen(request)
    return json.load(fl)


class VideoTransformer(object):
    def __init__(self, rx, url_extractor, endpoint, extra_args=None):
        self.rx = rx
        self.url_extractor = url_extractor
        self.endpoint = endpoint
        self.extra_args = extra_args or dict()

    def transform(self, html):
        return self.rx.sub(self.replacer, html)

    def replacer(self, match):
        url = self.url_extractor(match)
        dct = query_oembed(self.endpoint, url, self.extra_args)
        return dct["html"]


VIDEO_TRANSFORMERS = [
    VideoTransformer(
        re.compile('\[vimeo (\d+)\]'),
        lambda x: 'http://www.vimeo.com/' + x.group(1),
        "http://vimeo.com/api/oembed.json",
        {
            "byline": False,
            "title": False,
            "portrait": False,
        }
    ),
    VideoTransformer(
        re.compile('\[blip.tv (.*?)\]'),
        replacer_for_blip_redirected_url,
        "http://blip.tv/oembed",
    ),
    VideoTransformer(
        re.compile('\[youtube=(http://www.youtube.com/.*?)\]'),
        lambda x: x.group(1),
        "http://www.youtube.com/oembed",
    )
]

def format_videos(txt):
    for transformer in VIDEO_TRANSFORMERS:
        txt = transformer.transform(txt)
    return txt

def process_file(filename):
    assert filename.startswith(INPUT_DIR)
    relative_filename = filename[len(INPUT_DIR) + 1:]
    document_dir = os.path.dirname(relative_filename)

    with open(filename) as f:
        in_html = f.read()
        out_html = format_videos(in_html)

    if in_html == out_html:
        return False
    else:
        with open(filename, "w") as f:
            f.write(out_html)
        return True


def main():
    parser = OptionParser(usage=USAGE)

    (options, args) = parser.parse_args()

    if len(args) == 0:
        parser.error("Missing args")

    root = args[0]

    for dirname, dirs, filenames in os.walk(root):
        for filename in filenames:
            if not filename.endswith(".html"):
                continue
            name = os.path.join(dirname, filename)
            print ".",
            if process_file(name):
                print
                print "Modified", name
    return 0


if __name__ == "__main__":
    sys.exit(main())
# vi: ts=4 sw=4 et
