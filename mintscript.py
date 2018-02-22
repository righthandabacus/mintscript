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

from enscript import parseargs, parseformat

LATEXCODE = r'''
\documentclass[10pt]{article}
\usepackage{fontspec}
\usepackage[xetex, letterpaper, landscape, twocolumn, margin=15mm]{geometry}
\usepackage{minted}
\usepackage{amssymb}
\usemintedstyle{autumn}
\usepackage{tikzpagenodes}
\usepackage{background}
\usetikzlibrary{calc}
\setmonofont[Scale=0.63]{%(font)s}
\setsansfont[Scale=0.63]{%(font)s}
\setmainfont[Scale=0.63]{%(font)s}
\pagestyle{empty}

\begin{document}
\inputminted[linenos=true,baselinestretch=0.4,breaklines,fontsize=\fontsize{6pt}{6pt}]{python}{%(filename)s}
\label{LastPage}
\end{document}
'''

def latexoptions(args):
    '''Convert command line options parsed by argparse into LaTeX packages'
    options. I/O related arguments are handled elsewhere.

    Args:
        args: argparse namespace object

    Returns:
        dict: holds LaTeX packages options
    '''
    ret = {'input':args.file, 'geometry':[], 'minted':[], 'mintedlang':''
          ,'mintedstyle':''}
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
        ret['monofont'] = args.font # TODO enscript=Courier7, break this for LaTeX
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
		ret['footer'] = parseformat(args.footer)
	else:
		ret['footer'] = None
	if args.header:
		ret['header'] = parseformat(args.header)
	elif not args.no_header:
		ret['header'] = parseformat("$N\t$D{c}\t$%")
	else:
		ret['header'] = None
	if args.header_font: # also use as footer font
		ret['header_font'] = args['header_font']
	if args.underlay:
		ret['underlay'] = {'text': args.underlay}
		if args.ul_font:
			ret['underlay']['font'] = args.ul_font
		if args.ul_angle:
			ret['underlay']['angle'] = args.ul_angle # default atan(-d_page_h, d_page_w)
		if args.ul_gray:
			assert(0 <= args.ul_gray <= 1)
			ret['underlay']['gray'] = args.ul_gray # default 0.8
		if args.ul_position:
			assert(re.match(r'[+-]\d+[+-]\d+', ul_position))
			ret['underlay']['position'] = args.ul_position
		if args.ul_style:
			assert(args.ul_style in ['outline','filled'])
			ret['underlay']['style'] = args.ul_style
	if args.no_job_header or args.toc:
		raise NotImplementedError
    return ret

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
    opts = parseargs()
    if len(opts.file) != 1:
        logging.error('Multiple files, or stdin entry, are not yet supported')
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
