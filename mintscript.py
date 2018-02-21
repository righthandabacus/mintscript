#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import contextlib
import logging
import os
import shutil
import subprocess
import tempfile
import sys

LATEXCODE = r'''
\documentclass[10pt]{article}
\usepackage{fontspec}
\usepackage[xetex, letterpaper, landscape, twocolumn, margin=15mm]{geometry}
\usepackage{minted}
\usemintedstyle{autumn}
\setmonofont[Scale=0.63]{%(font)s}
\setsansfont[Scale=0.63]{%(font)s}
\setmainfont[Scale=0.63]{%(font)s}
\pagestyle{empty}

\begin{document}
\inputminted[linenos=true,baselinestretch=0.4,breaklines,fontsize=\footnotesize]{python}{%(filename)s}
\end{document}
'''

MINTED_OPTIONS = r'''
use \inputminted only - to read code from file without mixing with latex code
\usemintedstyle{name} - match Pygments style, check:
    from pygments.styles import get_all_styles()
    assert(name in list(get_all_styles()))

    or by command "pygmentize -L styles"
languages supported: "pygmentize -L lexers"

options used in \inputminted[...]: all are comma-sep key=val pairs, with =true optional
      linenos=true : show line numbers
      mathescape   : LaTeX math mode allowed inside comments
      gobble       : remove unnecessary whitespace from code
      autogobble   : detect length of whitespace automatically
      showspace    : show space char in output
      baselinestretch : numerical argument
      breaklines   : wrap line if too long
      breakanywhere : wrap line at anywhere, not just spaces
      breakautoindent : preserve indent on wrap
      codetagify : highlight special codes, default XXX, TODO, BUG, NOTE
      curlyquotes : replace ` and ' with curly quotation marks
      encoding : file encoding for Pygments
      firstline : integer, skip firstline-1 lines in input, default 1, i.e. no skip
      firstnumber : line number for first line
      fontfamily : default tt
      fontseries : default auto, current font
      fontsize : default auto, current font, or e.g. \footnotesize
      fontshape 
      frame : none, leftline, topline, bottomline, lines, single (type of frame around listing)
      framerule : width of frame
      framesep : sep between from and code
      lastline : last line of input to show
      linenos : enable line numbers
      numbers : left, right, both, none (side on which numbers appear)
      numberblanklines : blank line are numbered, default true
      numbersep : gap between number and start of line
      python3 : python lexer means python3
      rulecolor : color of frame
      samepage : force whole listing in same page even it doesn't fit
      obeytabs : do not convert tab into spaces
      showtabs : show tab symbol for tabs
      stepnumber : interval for line numbers to appear
      stepnumberfromfirst : default line numbers printted iff N%step==0, this make N%step==1
      stepnumberoffsetvalues: this make line numbers printted on N%step==0 as well as N==1
      stripall : strip all elading and trailing space from input
      stripnl : strip leading and trailing newlines from input
      tabsize : default 8
      texcomments : enable LaTeX code inside comments
      xleftmargin : added indentation before listing, default 0
      xrightmargin : added indentation after the listing, default 0

geometry package options
    text={7in,10in},centering
    margin=1.5in
    total={6.5in,8.75in},top=1.2in,left=0.9in,includefoot
    paper=a4paper (or [abc][0-6]paper, b[0-6]j, ansi[a-e]paper, letterpaper,
          executivepaper, legalpaper
    papersize={11in,17in},landscape
    portrait
    body={10in,16in} -- textwidth and textheight
    includehead, includefoot, includeheadfoot -- include head/foot in textheight (body)
    ignorehead, ignorefoot, ignoreheadfoot -- exclude head/foot in textheight (body)
    left,right,top,bottom -- margins of body
    twoside
    headsep, footskip -- text and header/footer baseline separation (thus no footheight)
    headheight -- height of header
    onecolumn,twocolumn
    columnsep
    textwidth, textheight

fancyhdr settings/options:
    \pagestyle{empty} or fancy
    \[lcr]head{}
    \[lcr]foot{}
    \fancyhead{}
    \fancyfoot{}
    \fancyhead[RO,LE]{\thepage}
    \renewcommand{\headrulewidth}{0.4pt}
    \renewcommand{\footrulewidth}{0.4pt}
    \renewcommand{\headrule}{\vbox to 0pt{\hbox to\headwidth{\dotfill}\vss}}

    \usepackage{fourier-orns}
    \renewcommand\headrule{
    \hrulefill
    \raisebox{-2.1pt}[10pt][10pt]{\quad\decofourleft\decotwo\decofourright\quad}
    \hrulefill
    }

fontspec
    \fontsize{10pt}{12pt}\selectfont blahblahblah
'''

def parseFormat(formatstr):
    '''convert format string into format understood by fancyhdr
    Original definition as in enscript
       %Format: name format
               Define a new string constant name according to the format string format.  Format string start from the first non-space character and it ends to the  end  of  the  line.   Format
               string can contain general `%' escapes and input file related `$' escapes.  Currently following escapes are supported:

               %%      character `%'

               $$      character `$'

               $%      current page number

               $=      number of pages in the current file

               $p      number of pages processed so far

               $(VAR)  value of the environment variable VAR.

               %c      trailing component of the current working directory

               %C ($C) current time (file modification time) in `hh:mm:ss' format

               %d      current working directory

               %D ($D) current date (file modification date) in `yy-mm-dd' format

               %D{string} ($D{string})
                       format string string with the strftime(3) function.  `%D{}' refers to the current date and `$D{}' to the input file's last modification date.

               %E ($E) current date (file modification date) in `yy/mm/dd' format

               %F ($F) current date (file modification date) in `dd.mm.yyyy' format

               %H      document title

               $L      number of lines in the current input file.  This is valid only for the toc entries, it can't be used in header strings.

               %m      the hostname up to the first `.' character

               %M      the full hostname

               %n      the user login name

               $n      input file name without the directory part

               %N      the user's pw_gecos field up to the first `,' character

               $N      the full input file name

               %t ($t) current time (file modification time) in 12-hour am/pm format

               %T ($T) current time (file modification time) in 24-hour format `hh:mm'

               %* ($*) current time (file modification time) in 24-hour format with seconds `hh:mm:ss'

               $v      the sequence number of the current input file

               $V      the  sequence  number  of  the  current  input file in the `Table of Contents' format: if the --toc option is given, escape expands to `num-'; if the --toc is not given,
                       escape expands to an empty string.

               %W ($W) current date (file modification date) in `mm/dd/yy' format

               All format directives except `$=' can also be given in format

               escape width directive

               where width specifies the width of the column to which the escape is printed.  For example, escape "$5%" will expand to something like " 12".  If  the  width  is  negative,  the
               value will be printed left-justified.

               For example, the `emacs.hdr' defines its date string with the following format comment:

               %Format: eurdatestr %E

               which expands to:

               /eurdatestr (96/01/08) def
    '''
def parseargs():
    description = 'convert text files to PDF'
    parser = argparse.ArgumentParser(description=description, add_help=False)
    parser.add_argument('file', metavar='file', nargs='*',
        help='Text files')
    parser.add_argument('--columns', dest='columns', default=1, type=int,
        help="specify the number of columns per page")
    parser.add_argument('-2', dest='columns', action='store_const', const=2,
        help="same as --columns=2")
    parser.add_argument('-1', dest='columns', action='store_const', const=1,
        help="same as --columns=1")
    parser.add_argument('-b', '--header', dest='header',
        help="set page header")
    parser.add_argument('-B', '--no-header', action='store_true', default=False,
        help="no page headers")
    parser.add_argument('-C', '--line-numbers', dest="start", nargs='?', type=int, const=1,
        help="precede each line with its line number")
    parser.add_argument('-E', '--highlight', dest="lang", nargs='?',
        help="highlight source code")
    parser.add_argument('-f', '--font', metavar='NAME', dest="font", nargs=1,
        help="use font NAME for body text")
    parser.add_argument('-F', '--header-font', metavar='NAME', dest="font", nargs=1,
        help="use font NAME for header text")
    parser.add_argument('-G', dest="fancy_header", action='store_true', default=None,
        help="same as --fancy-header")
    parser.add_argument('--fancy-header', metavar='NAME', nargs='?', const=True,
        help="select fancy page header")
    parser.add_argument('-h', '--no-job-header', action='store_true',
        help="suppress the job header page")
    parser.add_argument('-H', '--highlight-bars', metavar='NUM', nargs='?', type=int, const=1,
        help="specify how high highlight bars are") # 1 = shade alternate source lines
    parser.add_argument('-i', '--indent', metavar='NUM', nargs=1, type=int,
        help="set line indent to NUM characters")
    parser.add_argument('-I', '--filter', metavar='CMD', nargs=1,
        help="read input files through input filter CMD")
    parser.add_argument('-j', '--borders', action='store_true',
        help="print borders around columns")
    parser.add_argument('-M', '--media', metavar='NAME', nargs=1,
        help="use output media NAME")
    parser.add_argument('-p', '-o', '--output', metavar='FILE', nargs=1,
        help="leave output to file FILE.  If FILE is `-', leave output to stdout.")
    parser.add_argument('-q', '--quiet', '--silent', dest='quiet', action='store_true',
        help="Suppress stdout")
    parser.add_argument('-r', '--landscape', action='store_true',
        help="print in landscape mode")
    parser.add_argument('-R', '--portrait', action='store_true',
        help="print in portrait mode")
    parser.add_argument('-s', '--baselineskip', metavar='NUM', nargs=1, type=int,
        help="set baselineskip to NUM")
    parser.add_argument('-T', '--tabsize', metavar='NUM', nargs=1, type=int,
        help="set tabulator size to NUM")
    parser.add_argument('-u', '--underlay', metavar='TEXT', nargs=1,
        help="print TEXT under every page") # enscript allow empty for removing underlay w.r.t config file
    parser.add_argument('-V', '--version', action='store_true', default=False,
        help="print version number")
    parser.add_argument('-X', '--encoding', metavar='NAME', nargs=1,
        help="use input encoding NAME")
    parser.add_argument('--color', metavar='bool', nargs='?', type=bool,
        help="create color outputs with states")
    parser.add_argument('--filter-stdin', metavar='NAME', nargs=1,
        help="specify how stdin is shown to the input filter")
    parser.add_argument('--footer', metavar='FOOTER', nargs=1,
        help="set page footer")
    parser.add_argument('--h-column-height', metavar='HEIGHT', nargs=1,
        help="set the horizontal column height to HEIGHT")
    parser.add_argument('--help', action="store_true",
        help="print this help and exit")
    parser.add_argument('--highlight-bar-gray', metavar='NUM', nargs=1, type=float,
        help="print highlight bars with gray NUM (0 - 1)")
    parser.add_argument('--margins', metavar=('LEFT','RIGHT','TOP','BOTTOM'), nargs=4, type=float,
        help="adjust page marginals")
    parser.add_argument('--mark-wrapped-lines', metavar='STYLE', nargs='?',
        help="mark wrapped lines in the output with STYLE")
    parser.add_argument('--slice', metavar='NUM', nargs=1, type=int,
        help="print vertical slice NUM")
    parser.add_argument('--style', metavar='STYLE', nargs=1,
        help="use highlight style STYLE")
    parser.add_argument('--swap-even-page-margins', action="store_true",
        help="swap left and right side margins for each even numbered page")
    parser.add_argument('--toc', action="store_true",
        help="print table of contents")
    parser.add_argument('--ul-angle', metavar='ANGLE', nargs=1, type=float,
        help="set underlay text's angle to ANGLE")
    parser.add_argument('--ul-font', metavar='NAME', nargs=1,
        help="print underlays with font NAME")
    parser.add_argument('--ul-gray', metavar='NUM', nargs=1, type=float,
        help="print underlays with gray value NUM")
    parser.add_argument('--ul-position', metavar='POS', nargs=1, type=float,
        help="set underlay's starting position to POS")
    parser.add_argument('--ul-style', metavar='STYLE', nargs=1,
        help="print underlays with style STYLE")
    parser.add_argument('--word-wrap', action="store_true",
        help="wrap long lines from word boundaries")
    args = parser.parse_args()
    if args.help:
        parser.print_help()
        sys.exit(1)
    return args

@contextlib.contextmanager
def cd(newdir, cleanup=lambda: True):
    prevdir = os.getcwd()
    os.chdir(os.path.expanduser(newdir))
    try:
        yield
    finally:
        os.chdir(prevdir)
        cleanup()

@contextlib.contextmanager
def tempdir():
    dirpath = tempfile.mkdtemp()
    def cleanup():
        shutil.rmtree(dirpath)
    with cd(dirpath, cleanup):
        yield dirpath

def main():
    opts = parseargs()
    print(opts)
    if len(opts.file) > 1:
        logging.error('Multiple files are not yet supported')
        sys.exit(1)
    sys.exit(1)
    cwd = os.getcwd()
    fullpath = os.path.abspath(os.path.expanduser(opts.file[0]))
    if not os.path.isfile(fullpath):
        logging.error('Cannot read file %s' % opts.file[0])
        sys.exit(1)
    statinfo = os.stat(opts.file[0])
    mtime = statinfo.st_mtime
    size  = statinfo.st_size
    with tempdir() as dirpath:
        shutil.copyfile(fullpath, 'code.txt')
    params = {
         'font': 'Inconsolata'
        ,'filename': 'code.tex'
    }
    with open('code.tex','w') as fp:
        fp.write(texcode)
    commandline = ['xelatex','-shell-escape','-batch','code.tex']
    status = subprocess.call(commandline)
    if status != 0:
        logging.error('xelatex failed with return code %s' % status)


if __name__ == '__main__':
    main()

# vim: set et sw=4 ts=4:
