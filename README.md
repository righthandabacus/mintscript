Converting text into PDF
========================

enscript cannot do the job. I always cannot figure out how to change the font
for enscript output, and the language support for highlighting in enscript is
limited. With pygmentize and xelatex, we can do a better job.

## Synopsis

```
usage: mintscript.py [--columns COLUMNS] [-2] [-1] [-b HEADER] [-B] [-c]
                     [-C [LINE_NUMBERS]] [-E [HIGHLIGHT]] [-f NAME] [-F NAME]
                     [--fancy-header [NAME]] [-h] [-I CMD] [-j] [-M PAPER]
                     [-p FILE] [-q] [-r] [-R] [-s NUM] [-T NUM] [-u TEXT] [-V]
                     [-X NAME] [--color [bool]] [--filter-stdin NAME]
                     [--footer FOOTER] [--help]
                     [--margins LEFT RIGHT TOP BOTTOM]
                     [--mark-wrapped-lines [STYLE]] [--style STYLE]
                     [--swap-even-page-margins] [--toc] [--ul-angle ANGLE]
                     [--ul-font NAME] [--ul-gray NUM] [--ul-position POS]
                     [--ul-style STYLE] [--word-wrap]
                     [--geometry-args OPTION [OPTION ...]]
                     [--fontspec-args OPTION [OPTION ...]]
                     [--minted-args OPTION [OPTION ...]]
                     [file [file ...]]

convert text files to PDF

positional arguments:
  file                  Text files

optional arguments:
  --columns COLUMNS     specify the number of columns per page
  -2                    same as --columns=2
  -1                    same as --columns=1
  -b HEADER, --header HEADER
                        set page header
  -B, --no-header       no page headers
  -c, --truncate-lines  cut long lines (default is to wrap)
  -C [LINE_NUMBERS], --line-numbers [LINE_NUMBERS]
                        precede each line with its line number
  -E [HIGHLIGHT], --highlight [HIGHLIGHT]
                        highlight source code (see pygmentize -L lexers)
  -f NAME, --font NAME  use font NAME for body text
  -F NAME, --header-font NAME
                        use font NAME for header text
  --fancy-header [NAME]
                        select fancy page header
  -h, --no-job-header   suppress the job header page
  -I CMD, --filter CMD  read input files through input filter CMD
  -j, --borders         print borders around columns
  -M PAPER, --media PAPER
                        use output media PAPER
  -p FILE, -o FILE, --output FILE
                        leave output to file FILE. If FILE is `-', leave
                        output to stdout.
  -q, --quiet, --silent
                        Suppress stdout
  -r, --landscape       print in landscape mode
  -R, --portrait        print in portrait mode
  -s NUM, --baselineskip NUM
                        set baselineskip to NUM
  -T NUM, --tabsize NUM
                        set tabulator size to NUM
  -u TEXT, --underlay TEXT
                        print TEXT under every page
  -V, --version         print version number
  -X NAME, --encoding NAME
                        use input encoding NAME
  --color [bool]        create color outputs with states
  --filter-stdin NAME   specify how stdin is shown to the input filter
  --footer FOOTER       set page footer
  --help                print this help and exit
  --margins LEFT RIGHT TOP BOTTOM
                        adjust page marginals
  --mark-wrapped-lines [STYLE]
                        mark wrapped lines in the output with STYLE
  --style STYLE         use highlight style STYLE (see pygmentize -L styles)
  --swap-even-page-margins
                        swap left and right side margins for each even
                        numbered page
  --toc                 print table of contents
  --ul-angle ANGLE      set underlay text's angle to ANGLE
  --ul-font NAME        print underlays with font NAME
  --ul-gray NUM         print underlays with gray value NUM
  --ul-position POS     set underlay's starting position to POS
  --ul-style STYLE      print underlays with style STYLE
  --word-wrap           wrap long lines from word boundaries
  --geometry-args OPTION [OPTION ...]
                        argument for geometry package
  --fontspec-args OPTION [OPTION ...]
                        argument for fontspec \set*font commands
  --minted-args OPTION [OPTION ...]
                        argument for \inputminted command
```

## Requirements

It invokes `xelatex` command with `-shell-escape` option. The LaTeX code
generated will use `minted` package, which in turn calls `pygmentize` command to
format source code. It uses `fancyhdr` package for header and footers and `tikz`
package for page underlays (i.e. watermarks). Font support is provided by
`fontspec` package. By default, it expects a font named "Inconsolata" available
and accessible by `fontspec`. This has been tested with TexLive 2017. An older
version of TexLive or older version of LaTeX packages may not compatible.

## Example and output

Most arguments are same as that of enscript. The following command

    $ mintscript.py -M a4paper --footer 'sample output' -u 'TESTING' -r -2 <some_plain_text_file>

Generates the following LaTeX code and run through XeLaTeX to generate the PDF,
in the same directory as the input file.

```tex
\documentclass{article}
\usepackage[xetex,twocolumn,a4paper,landscape,margin=15mm]{geometry}
\usepackage{amssymb}
\usepackage{fontspec}
\usepackage{minted}
\usemintedstyle{autumn}
\setmonofont[AutoFakeSlant,AutoFakeBold]{Inconsolata}
\setsansfont[AutoFakeSlant,AutoFakeBold]{Inconsolata}
\setmainfont[AutoFakeSlant,AutoFakeBold]{Inconsolata}
\usepackage{tikz}
\usepackage{tikzpagenodes}
\usetikzlibrary{calc}
\makeatletter
\global\let\tikz@ensure@dollar@catcode=\relax
\makeatother
\usepackage{fancyhdr}
\pagestyle{fancy}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}
\fancyhf{}
\newfontfamily\Headerfont{Inconsolata}
\fancyhead[C]{\Headerfont\fontsize{8pt}{8pt}\selectfont{}yourfilename.txt\hfill{}Fri Feb 23 18:01:46 2018\hfill{}\thepage{}}
\fancyhead[R]{\begin{tikzpicture}[remember picture,overlay]
\fontsize{64}{64}
\selectfont
\node[text=black!20.000000!white,rotate=45.000000] at ($(current page.center) + (0,0)$) {TESTING};
\end{tikzpicture}}
\fancyfoot[C]{\Headerfont\fontsize{8pt}{8pt}\selectfont{}sample output}
\begin{document}
\fontsize{8pt}{8pt}\selectfont
\inputminted[breaklines,breakanywhere]{text}{source0.txt}

\label{LastPage}
\end{document}
```

XeLaTeX is used in order to make use of TTF available in the system. Currently
we set all fonts used in the LaTeX document to be the same (default Inconsolata,
adjustable by `-f` option). Additional options pass on to `geometry` package,
set font command of `fontspec` package, or `\inputminted` command of `minted`
package are allowed via the options `--geometry-args`, `--fontspec-args`,
`--minted-args`, respectively.

Intermediate files will be generated for and by LaTeX system but they will be
cleaned up automatically.
