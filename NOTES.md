Use XeLaTeX and minted as drop-in replacement to enscript

Minted: <ftp://ftp.dante.de/tex-archive/macros/latex/contrib/minted/minted.pdf>

# TikZ to make watermark

<https://tex.stackexchange.com/questions/280672/draft-watermark-in-both-margins-using-the-background-package>

```tex
\documentclass{article}
\usepackage[inner=30mm, outer=50mm, top=5mm, bottom=90mm, twoside]{geometry}
\usepackage{tikzpagenodes}
\usepackage{background}

% for coordinate computations
\usetikzlibrary{calc}

% allows for arbitrarily large font sizes
\usepackage{lmodern}

% dummy text
\usepackage{lipsum}

\backgroundsetup%
{   angle=0,
    opacity=1,
    scale=1,
    color=black,
    contents=%
    {   \begin{tikzpicture}[remember picture,overlay]
            \fontsize{80}{108}\selectfont
            % nodes for illustration purposes
            \node[circle,minimum width=4mm,fill=green] (PTAW) at (current page text area.west) {};
            \node[circle,minimum width=4mm,fill=orange] (PW) at (current page.west) {};         
            \node[circle,minimum width=4mm,fill=red] (BMW) at ($(current page text area.west -| current page.west)!0.5!(current page text area.west)$) {};
            \node[circle,minimum width=4mm,fill=blue] (GMW) at ($(current page.west)!0.5!(current page text area.west)$) {};
            \node[circle,minimum width=4mm,fill=black] (GW) at (current page text area.west -| current page.west) {};
            % the watermarks
            %\node[text=gray,rotate=90] at ($(current page text area.west -| current page.west)!0.5!(current page text area.west)$) {DRAFT 1};
            \node[text=gray,rotate=-90] at ($(current page text area.east -| current page.east)!0.5!(current page text area.east)$) {DRAFT 2};          
        \end{tikzpicture}
    }
}

\begin{document}

\lipsum \lipsum

\end{document}
```

# minted usage

use `\inputminted` only - to read code from file without mixing with latex code

`\usemintedstyle{name}` - match Pygments style, check

    from pygments.styles import get_all_styles()
    assert(name in list(get_all_styles()))

or by command `pygmentize -L styles`

languages supported: `pygmentize -L lexers`

options used in `\inputminted[...]`: all are comma-sep key=val pairs, with =true optional

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

# Geometry package options

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

# fancyhdr settings/options

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

# fontspec

    \fontsize{10pt}{12pt}\selectfont blahblahblah

# enscript %format definition

Original definition as in enscript

    %Format: name format

	Define a new string constant name according to the format string format.
    Format string start from the first non-space character and it ends to the  end
	of  the  line.   Format string can contain general `%' escapes and input
    file related `$' escapes.  Currently following escapes are supported:
    
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
			format string string with the strftime(3) function.  `%D{}' refers
            to the current date and `$D{}' to the input file's last modification date.
    %E ($E) current date (file modification date) in `yy/mm/dd' format
    %F ($F) current date (file modification date) in `dd.mm.yyyy' format
    %H      document title
	$L      number of lines in the current input file.  This is valid only for
            the toc entries, it can't be used in header strings.
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
	$V      the  sequence  number  of  the  current  input file in the `Table
            of Contents' format: if the --toc option is given, escape expands to `num-'; if
            the --toc is not given, escape expands to an empty string.
    %W ($W) current date (file modification date) in `mm/dd/yy' format
    
	All format directives except `$=' can also be given in format escape width
	directive where width specifies the width of the column to which the escape
	is printed.  For example, escape "$5%" will expand to something like " 12".
	If the  width  is  negative,  the value will be printed left-justified.
    
    For example, the `emacs.hdr' defines its date string with the following format comment:
    
    %Format: eurdatestr %E
    
    which expands to:
    
    /eurdatestr (96/01/08) def
