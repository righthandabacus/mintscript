#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''Replacement of enscript using XeLaTeX and minted
'''

import argparse
import contextlib
import datetime
import json
import logging
import os
import pwd
import re
import shutil
import socket
import subprocess
import sys
import tempfile

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
    parser.add_argument('-1', dest='columns', action='store_const', const=1,
        help="same as --columns=1")
    parser.add_argument('-2', dest='columns', action='store_const', const=2,
        help="same as --columns=2")
    parser.add_argument('-3', dest='columns', action='store_const', const=3,
        help="same as --columns=3")
    parser.add_argument('-4', dest='columns', action='store_const', const=4,
        help="same as --columns=4")
    parser.add_argument('-5', dest='columns', action='store_const', const=5,
        help="same as --columns=5")
    parser.add_argument('-6', dest='columns', action='store_const', const=6,
        help="same as --columns=6")
    parser.add_argument('-7', dest='columns', action='store_const', const=7,
        help="same as --columns=7")
    parser.add_argument('-8', dest='columns', action='store_const', const=8,
        help="same as --columns=8")
    parser.add_argument('-9', dest='columns', action='store_const', const=9,
        help="same as --columns=9")
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
    parser.add_argument('--margins', metavar=('LEFT','RIGHT','TOP','BOTTOM'), nargs=4,
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
                 .replace('$n',os.path.basename(inputfile.replace('_','\\_')) if inputfile else '')
                 .replace('%N',pwd.getpwuid(os.getuid()).pw_gecos)
                 .replace('$N',inputfile.replace('_','\\_') if inputfile else '')
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
    except (TypeError,ValueError):
        pass # pass as-is if cannot parse
    return font, size

def latexoptions(args):
    '''Convert command line options parsed by argparse into LaTeX packages'
    options. I/O related arguments are handled elsewhere.

    Args:
        args: argparse namespace object

    Returns:
        dict: holds LaTeX packages options
    '''
    ret = {'input':args.file, 'geometry':['xetex'], 'minted':[], 'mintedlang':'text'
          ,'mintedstyle':'autumn', 'font':('inconsolata','8pt'), 'multicols':None
          ,'header_font':('inconsolata','8pt'), 'header':None, 'footer':None
          ,'fontspec_args':['AutoFakeSlant','AutoFakeBold']}
    if args.columns==1:
        ret['geometry'].append('onecolumn')
    elif args.columns==2:
        ret['geometry'].append('twocolumn')
    else:
        ret['multicols'] = args.columns
    if args.line_numbers is not None:
        ret['minted'].append('linenos')
        if args.line_numbers != 1:
            ret['minted'].append('firstnumber=%s' % args.line_numbers)
    if args.color == True and not args.highlight:
        raise NotImplementedError # color needs a language for pygmentize
    if args.highlight is not None:
        highlight = args.highlight.lower()
        if highlight == 'auto':
            highlight = os.path.splitext(args.file[0])[1][1:]
        if highlight == 'python3':
            ret['minted'].append('python3')
            ret['mintedlang']  = 'python'
        else:
            ret['mintedlang']  = highlight
    if args.borders:
        ret['minted'].append('frame=single')
    if args.media:
        ret['geometry'].append(args.media) # TODO need sanitation check
    else:
        ret['geometry'].append('letterpaper')
    if args.landscape:
        ret['geometry'].append('landscape')
    if args.portrait:
        ret['geometry'].append('portrait')
    if args.tabsize:
        ret['minted'].append('tabsize=%d' % args.tabsize)
    if args.encoding:
        ret['minted'].append('encoding=%s' % args.encoding)
    if args.margins:
        ret['geometry'].extend(
            "%s=%s" % (t,v)
            for t,v in zip(["left","right","top","bottom"], args.margins)
        )
    else:
        ret['geometry'].append('margin=15mm') # default margin
    if args.truncate_lines:
        ret['minted'].append('breaklines=false')
    else:
        ret['minted'].append('breaklines')
    if not args.word_wrap:
        ret['minted'].append('breakanywhere')
    if args.baselineskip:
        ret['minted'].append('baselinestretch=%s' % args.baselineskip)
    if args.style:
        ret['mintedstyle'] = args.style
    if args.swap_even_page_margins:
        ret['geometry'].append('twoside')
    if args.font:
        ret['font'] = parsefont(args.font) # Courier7 -> ('Courier',7)
    if args.geometry_args:
        ret['geometry'].extend(args.geometry_args)
    if args.minted_args:
        ret['minted'].extend(args.minted_args)
    if args.fontspec_args:
        ret['fontspec_args'] += args.fontspec_args
    if args.mark_wrapped_lines:
        if args.mark_wrapped_lines == 'plus':
            ret['minted'].append(r'breaksymbolright=\small+')
        elif args.mark_wrapped_lines == 'box':
            ret['minted'].append(r'breaksymbolright=\small$\Box$')
        elif args.mark_wrapped_lines == 'arrow':
            ret['minted'].append(r'breaksymbolright=\small\carriagereturn')
        elif args.mark_wrapped_lines != 'none':
            ret['minted'].append(r'breaksymbolright=\small%s' % args.mark_wrapped_lines)
    if args.footer:
        ret['footer'] = parseformat(args.footer, args.file)
    if args.header:
        ret['header'] = parseformat(args.header, args.file)
    elif not args.no_header:
        ret['header'] = parseformat("$N\t$D{%c}\t$%", args.file)
    if args.header_font: # also use as footer font
        ret['header_font'] = parsefont(args.header_font)
    if args.underlay:
        ret['underlay'] = {'text':args.underlay, 'gray':20, 'angle':45
                          ,'xpos':0, 'ypos':0, 'style':'filled', 'font':(None,64)}
        if args.ul_font:
            ret['underlay']['font'] = parsefont(args.ul_font)
        if args.ul_angle:
            ret['underlay']['angle'] = args.ul_angle # default atan(-d_page_h, d_page_w)
        if args.ul_gray:
            assert(0 <= args.ul_gray <= 1)
            ret['underlay']['gray'] = args.ul_gray*100 # default 0.8
        if args.ul_position:
            m = re.match(r'([+-]\d+)([+-]\d+)', args.ul_position) # e.g. +10-10
            assert(m)
            ret['underlay']['xpos'] = int(m.group(1))
            ret['underlay']['ypos'] = int(m.group(2))
        if args.ul_style:
            assert(args.ul_style in ['outline','filled'])
            ret['underlay']['style'] = args.ul_style
    if args.no_job_header or args.toc:
        raise NotImplementedError
    return ret

def buildlatex(opt, filenames):
    '''Generate latex code
    '''
    fontspecargs = ','.join(opt['fontspec_args'])
    preamble = [''
       ,r'\documentclass{article}'
       ,r'\usepackage[%s]{geometry}' % ','.join(opt['geometry'])
       ,r'\usepackage{amssymb}' # for symbols at line wrapping, just in case
       ,r'\usepackage{fontspec}'
       ,r'\usepackage{minted}'
       ,r'\usemintedstyle{%s}'%opt['mintedstyle'] if opt['mintedstyle'] else None
    ]+([''
       ,r'\setmonofont[%(a)s]{%(f)s}' % {'a':fontspecargs,'f':opt['font'][0]}
       ,r'\setsansfont[%(a)s]{%(f)s}' % {'a':fontspecargs,'f':opt['font'][0]}
       ,r'\setmainfont[%(a)s]{%(f)s}' % {'a':fontspecargs,'f':opt['font'][0]}
    ] if opt['font'][0] else [])+([''
       ,r'\usepackage{tikz}'
       ,r'\usepackage{tikzpagenodes}'
       ,r'\usetikzlibrary{calc}'
       ,r'\makeatletter' # https://tex.stackexchange.com/questions/165929/semiverbatim-with-tikz-in-beamer/165937#165937
       ,r'\global\let\tikz@ensure@dollar@catcode=\relax'
       ,r'\makeatother'
    ] if 'underlay' in opt else [])+([''
        r'\usepackage{multicol}'
       ,r'\setlength{\columnsep}{5mm}'
    ] if opt['multicols'] else [])

    lh,ch,rh,lf,cf,rf = range(6)
    headfoot = ['']*6
    if not opt['header'] and not opt['footer'] and 'underlay' not in opt:
        preamble.extend([
            r'\pagestyle{empty}'
        ])
    else:
        preamble.extend([''
           ,r'\usepackage{fancyhdr}'
           ,r'\pagestyle{fancy}'
           ,r'\renewcommand{\headrulewidth}{0pt}'
           ,r'\renewcommand{\footrulewidth}{0pt}'
           ,r'\fancyhf{}'
        ])
        for i,hf in [(lh,'header'),(lf,'footer')]:
            if isinstance(opt[hf], list):
                headfoot[i:i+3] = opt[hf] # assumed len=3
            elif opt[hf]: # string type = header/footer at center
                headfoot[i+1] = opt[hf].replace('\t',r'\hfill{}')
        font,size = opt.get('header_font',[None,None])
        fontprepend = ''
        if font: # header font provided
            preamble.extend([''
               ,r'\newfontfamily\Headerfont{%s}' % font
            ])
            fontprepend = r'\Headerfont'
        if size: # header font size provided
            fontprepend+=r'\fontsize{%(s)s}{%(s)s}' % {'s':size}
        if fontprepend: # header font/fontsize not default, modify header strings
            fontprepend+=r'\selectfont{}'
            for i,v in enumerate(headfoot):
                if v:
                    headfoot[i] = fontprepend+headfoot[i]
        left, right = ('LO,RE', 'RO,LE') if 'twoside' in opt['geometry'] else ('L', 'R')
        if 'underlay' in opt:
            if opt['underlay']['font'][0]:
                preamble.extend([''
                    ,r'\newfontfamily\Overlayfont{%s}' % opt['underlay']['font'][0]
                ])
            headfoot[rh] += '\n'.join(filter(None,[''
                ,r'\begin{tikzpicture}[remember picture,overlay]'
                ,    r'\Overlayfont' if opt['underlay']['font'][0] else None
                ,   (r'\fontsize{%(s)d}{%(s)d}' % {'s':opt['underlay']['font'][1]})
                        if opt['underlay']['font'][1] else None
                ,    r'\selectfont' if any(opt['underlay']['font']) else None
                ,    r'\node[text=black!%(gray)f!white,rotate=%(angle)f] at '
                            '($(current page.center) + (%(xpos)s,%(ypos)s)$)'
                            ' {%(text)s};' % opt['underlay']
                ,r'\end{tikzpicture}'
            ]))
        preamble.extend(['' # header and footers config
           ,r'\fancyhead[%s]{%s}' % (left,headfoot[lf])  if headfoot[lh] else None
           ,r'\fancyhead[C]{%s}'  % headfoot[ch]         if headfoot[ch] else None
           ,r'\fancyhead[%s]{%s}' % (right,headfoot[rh]) if headfoot[rh] else None
           ,r'\fancyfoot[%s]{%s}' % (left,headfoot[lf])  if headfoot[lf] else None
           ,r'\fancyfoot[C]{%s}'  % headfoot[cf]         if headfoot[cf] else None
           ,r'\fancyfoot[%s]{%s}' % (right,headfoot[rf]) if headfoot[rf] else None
        ])

    body = [''
       ,r'\begin{document}'
       ,r'\fontsize{%(s)s}{%(s)s}\selectfont' % {'s':opt['font'][1]} if opt['font'][1] else None
    ]+([r'\begin{multicols*}{%d}' % opt['multicols']
    ] if opt['multicols'] else [])+[
       (r'\inputminted[%(a)s]{%(l)s}{%(f)s}' + '\n')
            % {'a':','.join(opt['minted']), 'l':opt['mintedlang'], 'f':f}
        for f in filenames
    ]+([r'\end{multicols*}'
    ] if opt['multicols'] else [])+[''
       ,r'\label{LastPage}'
       ,r'\end{document}'
    ]
    return '\n'.join(filter(None, preamble+body))

@contextlib.contextmanager
def cd(newdir, cleanup=lambda: True):
    '''change the current working directory and yield. Upon context close, goes
    back to the original directory and execute the clean up function.

    Args:
        newdir (str): path to new working dir, ~username supported
        cleanup (callable): will execute this upon context close
    '''
    prevdir = os.getcwd()
    os.chdir(os.path.expanduser(newdir))
    try:
        yield
    finally:
        os.chdir(prevdir)
        cleanup()

@contextlib.contextmanager
def tempdir():
    '''a context manager to create a temp dir and change the working directory
    to it. Useful for learning up after running code that generate files in the
    local dir.
    '''
    dirpath = tempfile.mkdtemp()
    def cleanup():
        shutil.rmtree(dirpath)
    with cd(dirpath, cleanup):
        yield dirpath

def main():
    args = parseargs()
    if len(args.file) < 1:
        logging.error('stdin entry is not yet supported')
        sys.exit(1)
    logging.getLogger('').setLevel(logging.ERROR if args.quiet else logging.DEBUG)
    logging.debug(args)
    options = latexoptions(args)
    logging.debug(options)
    files = ["source%d%s"%(i, os.path.splitext(f)[-1]) for i,f in enumerate(args.file)]
    latexcode = buildlatex(options, files)
    texfile = 'mintscript_temp.tex'
    pdffile = texfile[:-3] + 'pdf'
    cwd = os.getcwd()
    with tempdir() as _:
        for oldpath,newpath in zip(args.file, files):
            oldpath = os.path.join(cwd, oldpath)
            if not os.path.isfile(oldpath):
                logging.error('Cannot read file %s' % oldpath)
                sys.exit(1)
            shutil.copyfile(oldpath, newpath)
            logging.debug('Copied %s to %s' % (oldpath, newpath))
        assert(texfile not in files)
        with open(texfile,'w') as fp:
            fp.write(latexcode)
        logging.debug('LaTeX code:\n%s' % latexcode)
        if args.quiet:
            commandline = ['xelatex','-shell-escape','-interaction=batchmode','-8bit',texfile]
        else:
            commandline = ['xelatex','-8bit','-shell-escape','-interaction=nonstopmode','-halt-on-error',texfile]
        for i in range(2): # run latex twice due to labels
            status = subprocess.call(commandline)
            if status != 0:
                logging.error('xelatex failed with return code %s' % status)
                sys.exit(status)
        if not os.path.isfile(pdffile):
            logging.error('xelatex completed but %s not found in output' % pdffile)
            sys.exit(1)
        if not args.output:
            args.output = os.path.splitext(args.file[0])[0] + '.pdf'
        logging.debug('Output to %s' % args.output)
        if args.output == '-':
            sys.stdout.buffer.write(open(pdffile).read()) # dump binary to stdout
        elif args.output:
            shutil.copyfile(pdffile, os.path.join(cwd,args.output))

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s:%(name)s(%(lineno)d):%(levelname)s:%(message)s')
    main()

# vim:set et sw=4 ts=4:
