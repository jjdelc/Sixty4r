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

class CssConvert(object):
    RULE_URL_RE = re.compile('\((?P<path>.+)\)')
    MIME_TYPES = {
        '.gif': 'image/gif',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
    }

    def __init__(self, in_fname, out_fname):
       self.in_fname = in_fname
       self.out_fname = out_fname
       self.base_path = self.calculate_base_path(self.in_fname)

    def write_output(self):
        fh = open(self.out_fname, 'w')
        for converted_line in self.parse():
            fh.write(converted_line)

    def parse(self):
        fh = open(self.in_fname)
        for rule in fh:
            yield self.convert_rule(rule)

    def convert_rule(self, rule):
        if 'url(' not in rule:
            return rule

        url_path = self.extract_url_path(rule)
        return self.replace_url_path(rule, url_path)

    def extract_url_path(self, rule):
        return self.RULE_URL_RE.search(rule).groupdict()['path']

    def get_absolute_path(self, path):
        if path.startswith('http://'):
            return path

        return realpath(join(self.base_path, path))

    def replace_url_path(self, rule, url_path):
        full_path = self.get_absolute_path(url_path)
        b64data = self.get_b64_datauri(full_path)
        return rule.replace(url_path, b64data)

    def get_b64_datauri(self, path):
        if path.startswith('http://'):
            # Fetch web resource 
            bdata = urlopen(path).read()
        else:
            # Open local fs file
            bdata =  open(path).read()

        # Convert to one line string
        line_bdata = ''.join(bdata.encode('base64').split('\n'))
        base, ext = splitext(path) # Get extension
        mime_type = self.MIME_TYPES[ext]
        return 'data:%s;base64,%s' % (mime_type, line_bdata)
 
    def calculate_base_path(self, filename):
        return dirname(abspath(filename))

       

if __name__ == '__main__':
    in_fname = sys.argv[1]
    out_fname = sys.argv[2]

    css = CssConvert(in_fname, out_fname)
    css.write_output()

