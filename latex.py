import re

def latexoptions(args):
    '''Convert command line options parsed by argparse into LaTeX packages'
    options. I/O related arguments are handled elsewhere.

    Args:
        args: argparse namespace object

    Returns:
        dict: holds LaTeX packages options
    '''
    ret = {'input':args.file, 'geometry':[], 'minted':[], 'mintedlang':''
          ,'mintedstyle':'', 'font':(None,None), 'header':None, 'footer':None}
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
        ret['header_font'] = parsefont(args['header_font'])
    if args.underlay:
        ret['underlay'] = {'text':args.underlay, 'gray':80, 'angle':45
                          ,'xpos':0, 'ypos':0, 'style':'filled'}
        if args.ul_font:
            ret['underlay']['font'] = parsefont(args.ul_font)
        if args.ul_angle:
            ret['underlay']['angle'] = args.ul_angle # default atan(-d_page_h, d_page_w)
        if args.ul_gray:
            assert(0 <= args.ul_gray <= 1)
            ret['underlay']['gray'] = args.ul_gray*100 # default 0.8
        if args.ul_position:
            m = re.match(r'([+-]\d+)([+-]\d+)', ul_position) # e.g. +10-10
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
       ,r'\usepackage{fontspec}'
       ,r'\usepackage{minted}'
       ,r'\usepackage{amssymb}' # for symbols at line wrapping, just in case
       ,r'\usemintedstyle{%s}'%opt['mintedstyle'] if opt['mintedstyle'] else None
    ]+(['' # underlay
       ,r'\usepackage{tikz}'
       ,r'\usepackage{tikzpagenodes}'
       ,r'\usepackage{background}'
       ,r'\usetikzlibrary{calc}'
      ,(r'\newfontfamily\Overlayfont{%s}' % opt['underlay']['font'][0])
             if opt['underlay']['font'][0] else None
       ,r'\backgroundsetup{'
       ,r'   angle=0,'
       ,r'   opacity=1,'
       ,r'   scale=1,'
       ,r'   color=black,'
       ,r'   contents={'
       ,r'     \begin{tikzpicture}[remember picture,overlay]'
       ,r'       ', r'\Overlayfont' if opt['underlay']['font'][0] else None
       ,       (r'\fontsize{%(s)d}{%(s)d}' % {'s':opt['underlay']['font'][1]})
                      if opt['underlay']['font'][1] else None
       ,        r'\selectfont' if opt['underlay']['font'] else None
       ,r'       \node[text=black!%(gray)f!white,rotate=%(angle)f] at '
                   '($(current page text area.south west)'
                   '!0.5!'
                   '(current page text area.north east) + (%(xpos)s,%(ypos)s)$)'
                   ' {%(text)s};' % opt['underlay']['gray']
       ,r'     \end{tikzpicture}'
       ,r'   }'
       ,r'}'
    ] if 'underlay' in opt else [])+([''
       ,r'\setmonofont[%(a)s]{%(f)s}' % {'a':opt.get('fontspec_args',''),'f':opt['font'][0]}
       ,r'\setsansfont[%(a)s]{%(f)s}' % {'a':opt.get('fontspec_args',''),'f':opt['font'][0]}
       ,r'\setmainfont[%(a)s]{%(f)s}' % {'a':opt.get('fontspec_args',''),'f':opt['font'][0]}
    ] if opt['font'][0] else [])+([
        # header and footer
    ])
    body = [''
       ,r'\begin{document}'
       ,r'\fontsize{%d}{%d}\selectfont' % opt['font'][1] if opt['font'][1] else None
    ]+[
       (r'\inputminted[%(a)s]{%(l)s}{%(f)s}' + '\n')
            % {'a':','.join(opt['minted']), 'l':opt['mintedlang'], 'f':f}
        for f in filenames
    ]+[''
       ,r'\label{LastPage}'
       ,r'\end{document}'
    ]
    return '\n'.join(filter(None, preamble+body))
