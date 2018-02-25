import re
from enscript import parseformat, parsefont

def latexoptions(args):
    '''Convert command line options parsed by argparse into LaTeX packages'
    options. I/O related arguments are handled elsewhere.

    Args:
        args: argparse namespace object

    Returns:
        dict: holds LaTeX packages options
    '''
    ret = {'input':args.file, 'geometry':['xetex'], 'minted':[], 'mintedlang':'text'
          ,'mintedstyle':'autumn', 'font':('Inconsolata','8pt')
          ,'header_font':('Inconsolata','8pt'), 'header':None, 'footer':None}
    if args.columns==1:
        ret['geometry'].append('onecolumn')
    elif args.columns==2:
        ret['geometry'].append('twocolumn')
    else:
        raise NotImplementedError
    if args.line_numbers is not None:
        ret['minted'].append('linenos')
        if args.line_numbers != 1:
            ret['minted'].append('firstnumber=%s' % args.line_numbers)
    if args.color == True and not args.highlight:
        raise NotImplementedError # color needs a language for pygmentize
    if args.highlight is not None:
        if args.highlight.lower() == 'python3':
            ret['minted'].append('python3')
            ret['mintedlang']  = 'python'
        else:
            ret['mintedlang']  = args.highlight
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
        ret['underlay'] = {'text':args.underlay, 'gray':80, 'angle':45
                          ,'xpos':0, 'ypos':0, 'style':'filled', 'font':(None,None)}
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
    preamble = [''
       ,r'\documentclass{article}'
       ,r'\usepackage[%s]{geometry}' % ','.join(opt['geometry'])
       ,r'\usepackage{amssymb}' # for symbols at line wrapping, just in case
       ,r'\usepackage{fontspec}'
       ,r'\usepackage{minted}'
       ,r'\usemintedstyle{%s}'%opt['mintedstyle'] if opt['mintedstyle'] else None
    ]+([''
       ,r'\usepackage{tikz}'
       ,r'\usepackage{tikzpagenodes}'
       ,r'\usetikzlibrary{calc}'
    ] if 'underlay' in opt else [])+([''
       ,r'\setmonofont[%(a)s]{%(f)s}' % {'a':opt.get('fontspec_args',''),'f':opt['font'][0]}
       ,r'\setsansfont[%(a)s]{%(f)s}' % {'a':opt.get('fontspec_args',''),'f':opt['font'][0]}
       ,r'\setmainfont[%(a)s]{%(f)s}' % {'a':opt.get('fontspec_args',''),'f':opt['font'][0]}
    ] if opt['font'][0] else [])

    lh,ch,rh,lf,cf,rf = range(6)
    headfoot = [None]*6
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
            ''])
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
                ''])
            headfoot[rh].append('\n'.join(filter(None,[''
                ,r'\begin{tikzpicture}[remember picture,overlay]'
                ,    r'\Overlayfont' if opt['underlay']['font'][0] else None
                ,   (r'\fontsize{%(s)d}{%(s)d}' % {'s':opt['underlay']['font'][1]})
                        if opt['underlay']['font'][1] else None
                ,    r'\selectfont' if any(opt['underlay']['font']) else None
                ,    r'\node[text=black!%(gray)f!white,rotate=%(angle)f] at '
                            '($(current page.center) + (%(xpos)s,%(ypos)s)$)'
                            ' {%(text)s};' % opt['underlay']
                ,r'\end{tikzpicture}'
            ])))
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
    ]+[
       (r'\inputminted[%(a)s]{%(l)s}{%(f)s}' + '\n')
            % {'a':','.join(opt['minted']), 'l':opt['mintedlang'], 'f':f}
        for f in filenames
    ]+[''
       ,r'\label{LastPage}'
       ,r'\end{document}'
    ]
    return '\n'.join(filter(None, preamble+body))
