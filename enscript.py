# -*- coding: utf-8 -*-
'''Helper functions to mimick enscript command interface
'''

import argparse
import datetime
import json
import logging
import os
import pwd
import re
import socket
import sys

def parseargs():
    '''Argument parser that supports a subset of arguments of enscript

    Returns:
        argparse namespace object
    '''
    description = 'convert text files to PDF'
    parser = argparse.ArgumentParser(description=description, add_help=False)
    parser.add_argument('file', metavar='file', nargs='*',
        help='Text files')
    parser.add_argument('--columns', default=1, type=int,
        help="specify the number of columns per page")
    parser.add_argument('-2', dest='columns', action='store_const', const=2,
        help="same as --columns=2")
    parser.add_argument('-1', dest='columns', action='store_const', const=1,
        help="same as --columns=1")
    parser.add_argument('-b', '--header',
        help="set page header")
    parser.add_argument('-B', '--no-header', action='store_true', default=False,
        help="no page headers")
    parser.add_argument('-c', '--truncate-lines', action='store_true',
        help="cut long lines (default is to wrap)")
    parser.add_argument('-C', '--line-numbers', nargs='?', type=int, const=1,
        help="precede each line with its line number")
    parser.add_argument('-E', '--highlight', nargs='?',
        help="highlight source code (see pygmentize -L lexers)")
    parser.add_argument('-f', '--font', metavar='NAME',
        help="use font NAME for body text")
    parser.add_argument('-F', '--header-font', metavar='NAME',
        help="use font NAME for header text")
    parser.add_argument('--fancy-header', metavar='NAME', nargs='?', const=True,
        help="select fancy page header")
    parser.add_argument('-h', '--no-job-header', action='store_true',
        help="suppress the job header page")
    parser.add_argument('-I', '--filter', metavar='CMD',
        help="read input files through input filter CMD")
    parser.add_argument('-j', '--borders', action='store_true',
        help="print borders around columns")
    parser.add_argument('-M', '--media', metavar='PAPER',
        help="use output media PAPER")
    parser.add_argument('-p', '-o', '--output', metavar='FILE',
        help="leave output to file FILE.  If FILE is `-', leave output to stdout.")
    parser.add_argument('-q', '--quiet', '--silent', dest='quiet', action='store_true',
        help="Suppress stdout")
    parser.add_argument('-r', '--landscape', action='store_true',
        help="print in landscape mode")
    parser.add_argument('-R', '--portrait', action='store_true',
        help="print in portrait mode")
    parser.add_argument('-s', '--baselineskip', metavar='NUM', type=int,
        help="set baselineskip to NUM")
    parser.add_argument('-T', '--tabsize', metavar='NUM', type=int,
        help="set tabulator size to NUM")
    parser.add_argument('-u', '--underlay', metavar='TEXT',
        help="print TEXT under every page") # enscript allow empty for removing underlay w.r.t config file
    parser.add_argument('-V', '--version', action='store_true', default=False,
        help="print version number")
    parser.add_argument('-X', '--encoding', metavar='NAME',
        help="use input encoding NAME")
    parser.add_argument('--color', metavar='bool', nargs='?', type=bool,
        help="create color outputs with states")
    parser.add_argument('--filter-stdin', metavar='NAME',
        help="specify how stdin is shown to the input filter")
    parser.add_argument('--footer', metavar='FOOTER',
        help="set page footer")
    parser.add_argument('--help', action="store_true",
        help="print this help and exit")
    parser.add_argument('--margins', metavar=('LEFT','RIGHT','TOP','BOTTOM'), nargs=4, type=float,
        help="adjust page marginals")
    parser.add_argument('--mark-wrapped-lines', metavar='STYLE', nargs='?',
        help="mark wrapped lines in the output with STYLE")
    parser.add_argument('--style', metavar='STYLE',
        help="use highlight style STYLE (see pygmentize -L styles)")
    parser.add_argument('--swap-even-page-margins', action="store_true",
        help="swap left and right side margins for each even numbered page")
    parser.add_argument('--toc', action="store_true",
        help="print table of contents")
    parser.add_argument('--ul-angle', metavar='ANGLE', type=float,
        help="set underlay text's angle to ANGLE")
    parser.add_argument('--ul-font', metavar='NAME',
        help="print underlays with font NAME")
    parser.add_argument('--ul-gray', metavar='NUM', type=float,
        help="print underlays with gray value NUM")
    parser.add_argument('--ul-position', metavar='POS',
        help="set underlay's starting position to POS")
    parser.add_argument('--ul-style', metavar='STYLE',
        help="print underlays with style STYLE")
    parser.add_argument('--word-wrap', action="store_true",
        help="wrap long lines from word boundaries")
    parser.add_argument('--geometry-args', metavar='OPTION', nargs='+',
        help="argument for geometry package")
    parser.add_argument('--fontspec-args', metavar='OPTION', nargs='+',
        help=r"argument for fontspec \set*font commands")
    parser.add_argument('--minted-args', metavar='OPTION', nargs='+',
        help=r"argument for \inputminted command")
    args = parser.parse_args()
    if args.help:
        parser.print_help()
        sys.exit(1)
    return args

def parseformat(formatstr, inputfile=None):
    '''convert format string into format understood by fancyhdr. This is
    different from enscript's %Format that width, such as $5% for page number in
    5 character spaces, is not supported

    Args:
        formatstr (str): format string input with escapes
        inputfile (str): filename input, in case file-dependent info are used

    Returns:
        str or list of three str: the formatted field, or left, center, and
        right part of the fields in case `|` in the format string
    '''
    if '|' in formatstr:
        # left, center, and right justified fields
        fields = formatstr.split('|')
        assert(len(fields) == 3)
        fields = [parseformat(f, inputfile) for f in fields]
        return fields
    cwd = os.getcwd()
    cwdtrail = os.path.split(os.getcwd())[-1]
    if inputfile:
        inputfile = inputfile[0]
        now = datetime.datetime.fromtimestamp(os.stat(inputfile).st_mtime)
    else:
        now = datetime.datetime.now()
    formatstr = re.sub(r'\$\((\w+)\)', lambda m:os.environ[m.group(1)],formatstr)
    formatstr = re.sub(r'\$D\{([^\}]+)\}', lambda m:now.strftime(m.group(1)),formatstr)
    formatstr = ( formatstr
                 .replace('$%',r'\thepage{}')
                 .replace('$=',r'\pageref{LastPage}') # need LastPage label
                 .replace('$C','%C').replace('$*','%C').replace('%*','%C')
                                    .replace('%C',now.strftime('%H:%M:%S'))
                 .replace('$t','%t').replace('%t',now.strftime('%I:%M %p'))
                 .replace('$T','%T').replace('%T',now.strftime('%H:%M'))
                 .replace('$D','%D').replace('%D',now.strftime('%y-%m-%d'))
                 .replace('$E','%E').replace('%E',now.strftime('%y/%m/%d'))
                 .replace('$F','%F').replace('%F',now.strftime('%d.%m.%Y'))
                 .replace('$W','%W').replace('%W',now.strftime('%m/%d/%y'))
                 .replace('%c',cwdtrail)
                 .replace('%d',cwd)
                 .replace('%m',socket.gethostname())
                 .replace('%M',socket.getfqdn())
                 .replace('%n',pwd.getpwuid(os.getuid()).pw_name)
                 .replace('$n',os.path.basename(inputfile) if inputfile else '')
                 .replace('%N',pwd.getpwuid(os.getuid()).pw_gecos)
                 .replace('$N',inputfile if inputfile else '')
                 .replace('$$','$')
                 .replace('%%','%')
                )
    # TODO %v for sequence number of input file (in case of multiple file input)
    #      rewrite above to get filename/mtime dynamically in case of multi-file input
    return formatstr

def parsefont(fontstr):
    '''Convert font string into font and size if possible. Allowed format:
        - Courier7
        - Courier,7
        - ["Courier",7]
        - Courier
    '''
    font, size = None, None
    try:
        logging.debug('Decoding font: %s' % repr(fontstr))
        fontdata = json.loads(fontstr)
        if isinstance(fontdata, basestring):
            font = fontdata
        elif isinstance(fontdata, list):
            if len(fontdata) == 2:
                font, size = fontdata
            elif len(fontdata) == 1:
                font = fontdata[0]
            else:
                raise RuntimeError # cannot parse
        else:
            raise RuntimeError # unknown format from json, cannot parse
    except ValueError:
        if not fontstr[-1].isdigit():
            font = fontstr
        elif ',' in fontstr:
            font,size = fontstr.rsplit(',',1)
        else:
            m = re.match(r"(.*[^\d])(\d+)$", fontstr)
            if m:
                font, size = m.group(1), m.group(2)
            else:
                raise RuntimeError # fontstr is pure numeric?
    try:
        size = "%fpt" % float(size) # default unit: point
    except ValueError:
        pass # pass as-is if cannot parse
    return font, size
