#!/usr/bin/env python

"""
Converts a CSS file's url() image rules paths to base64 data URIs in order to
minimize HTTP requests.
Similar effect can be achieved using CSS Sprites, but they are a pain to
maintain
"""

import re
import sys
from urllib import urlopen
from os.path import abspath, dirname, join, realpath, splitext


class TooBigFileException(Exception):
    """ This exception will be raised if the to be converted file exceeds
    the threshold file size """
    pass


def get_data(path):
    """ Returns the resources data, either by opening it or fetching it from
    a url """
    if path.startswith('http://'):
        # Fetch web resource
        bdata = urlopen(path).read()
    else:
        # Open local fs file
        bdata = open(path).read()

    return bdata


class CssConvert(object):
    """ This class takes a CSS filename and will convert all url() paths
    into b64 encoded data uris as long as they are smaller than a threshold """

    RULE_URL_RE = re.compile('\((?P<path>.+)\)')
    MIME_TYPES = {
        '.gif': 'image/gif',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
    }

    RES_SIZE_THRESHOLD = 2 * 1024  # 2KB

    def __init__(self, input_fname, output_fname):
        self.in_fname = input_fname
        self.out_fname = output_fname
        self.base_path = dirname(abspath(self.in_fname))

    def write_output(self):
        output = open(self.out_fname, 'w')
        for converted_line in self.parse():
            output.write(converted_line)

    def parse(self):
        for rule in open(self.in_fname):
            yield self.convert_rule(rule)

    def convert_rule(self, rule):
        if 'url(' not in rule:
            return rule

        url_path = self.extract_url_path(rule)
        if self.is_supported(url_path):
            return self.replace_url_path(rule, url_path)

        return url_path

    def is_supported(self, url_path):
        base, ext = splitext(url_path)  # Get extension
        return ext in self.MIME_TYPES

    def extract_url_path(self, rule):
        return self.RULE_URL_RE.search(rule).groupdict()['path']

    def get_absolute_path(self, path):
        if path.startswith('http://'):
            return path

        return realpath(join(self.base_path, path))

    def replace_url_path(self, rule, url_path):
        full_path = self.get_absolute_path(url_path)
        try:
            b64data = self.get_b64_datauri(full_path)
        except TooBigFileException:
            # File is too big, don't convert
            return rule

        return rule.replace(url_path, b64data)

    def get_b64_datauri(self, path):
        bdata = get_data(path)

        if len(bdata) > self.RES_SIZE_THRESHOLD:
            raise TooBigFileException

        # Convert to one line string
        line_bdata = ''.join(bdata.encode('base64').split('\n'))
        base, ext = splitext(path)  # Get extension
        mime_type = self.MIME_TYPES[ext]
        return 'data:%s;base64,%s' % (mime_type, line_bdata)


if __name__ == '__main__':
    in_fname = sys.argv[1]
    out_fname = sys.argv[2]

    css = CssConvert(in_fname, out_fname)
    css.write_output()
