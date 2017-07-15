#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# * * * * * * * * * * * * * * * * * * * *
#   pokey_appmap.py : map a web application based on a local directory hierarchy
#   https://github.com/wnormandin/pokey_appmap
#   Requires python3
# * * * * * * * * * * * * * * * * * * * *
#
#   MIT License
#
#   Copyright (c) 2017 William Normandin
#
#   Permission is hereby granted, free of charge, to any person obtaining a copy
#   of this software and associated documentation files (the "Software"), to deal
#   in the Software without restriction, including without limitation the rights
#   to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#   copies of the Software, and to permit persons to whom the Software is
#   furnished to do so, subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be included in all
#   copies or substantial portions of the Software.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#   SOFTWARE.
#
# * * * * * * * * * * * * * * * * * * * *

import queue
import threading
import os
import sys
import requests
import argparse
import time
import tempfile
import zipfile
import tarfile
import json

from urllib.parse import urljoin, urlparse

this = sys.modules[__name__]
session = requests.Session()

class Formatter(argparse.RawDescriptionHelpFormatter):
    def _split_lines(self, text, width):
        text = self._whitespace_matcher.sub(' ', text).strip()
        return _textwrap.wrap(text, width)

def cprint(val, col=None, verbose=False):
    if not args.verbose and verbose:
        return
    if col==None:
        msg = val
    else:
        msg = color_wrap(val, col)
    print(msg)

def color_wrap(val, col):
    if args.nocolor:
        return str(val)
    return ''.join([col, str(val), Color.END])

class Color:
    BLACK_ON_GREEN = '\x1b[1;30;42m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'
    MSG = '\x1b[1;32;44m'
    ERR = '\x1b[1;31;44m'
    TST = '\x1b[7;34;46m'

def cli():
    def handle_args():
        if args.local is None and args.remote is None:
            print(color_wrap('[*] --local or --remote source required', Color.ERR))
            sys.exit(1)
        if args.local is not None and args.remote is not None:
            print(color_wrap('[*] --local and --remote passed, using --local', Color.MSG))
            assert os.path.exists(args.local)
        if args.local is not None and args.remote is None:
            assert os.path.exists(args.local)
        if not args.map_images:
            default_filter = ['.jpg', '.css', '.png', '.gif']
        else:
            default_filter = []
        if args.ignore:
            default_filter.extend(args.ignore)
            args.ignore = default_filter
        else:
            args.ignore = default_filter
        if args.outfile is None:
            args.outfile = '{}.json'.format(int(time.time()))
        try:
            with open(args.outfile, 'w+') as outfile:
                pass
        except OSError as e:
            print(color_wrap('[*] Error accessing {}: {}'.format(f, e), Color.ERR))
            sys.exit(1)
        this.result = {t:{'pass':{}, 'fail':{}} for t in args.target}

    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--target', type=str, nargs='*', help='Specify target domain(s)', required=True)
    parser.add_argument('-l', '--local', type=str, help='Specify a local directory to compare')
    parser.add_argument('-r', '--remote', type=str, help='Specify a URL to software for comparison')
    parser.add_argument('--ignore', type=str, nargs='*', help='Specify file extensions to ignore (default = .jpg, .css, .png, .gif)')
    parser.add_argument('--map-images', action='store_true', help='Disable default image filtering')
    parser.add_argument('-o', '--outfile', type=str, help='Path to output file (default = <epoch timestamp>.json)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('-C', '--nocolor', action='store_true', help='Suppress colors in output')
    parser.add_argument('-m', '--max-threads', type=int, default=2, help='Specify the max number of worker threads')
    parser.add_argument('--save', action='store_true', help='Keep downloaded software (in ./.path_templates)')
    parser.add_argument('--showall', action='store_true', help='Show failed paths')
    parser.add_argument('--dryrun', action='store_true', help='Performs preparatory steps only, no targets hit')
    this.args = parser.parse_args()
    handle_args()

def display_args():
    col = Color.BLUE
    pre = ' - ' # Default line prefix
    cprint('[*] Argument Summary', Color.MSG, True)
    report_list = [
            ('Target(s)', ', '.join(args.target)),
            ('Source', args.local),
            ('Remote', args.remote),
            ('Outfile', args.outfile),
            ('Filtering', args.ignore),
            ('Max Threads', args.max_threads),
            ('Verbose', args.verbose),
            ('Save', args.save),
            ('Show All', args.showall),
            ('Include Images', args.map_images),
            ('No Color', args.nocolor),
            ('Dry Run', args.dryrun),
            ]
    for item in report_list:
        key, val = item
        msg = '{} {:<15}: {}'.format(pre, key, val)
        cprint(msg, col, True)

def test_url(base_url, local):
    while not this.web_paths.empty():
        path = web_paths.get()
        url = urljoin(base_url, path.replace(local, ''))
        cprint(' -  Checking {}'.format(url), Color.BLUE, True)
        result = session.get(url)
        verb = False
        if result.status_code == 200:
            col = Color.GREEN
            sig = '==>'
        elif result.status_code in range(300,303):
            col = Color.CYAN
            sig = '<_>'
            if not args.showall:
                verb = True
        elif result.status_code in range(400,405):
            col = Color.YELLOW
            sig = '_!_'
            if not args.showall:
                verb = True
        else:
            col = Color.RED
            sig = '_X_'
            if not args.showall:
                verb = True
        result_q.put((base_url,
                      path.replace(local, ''),
                      result.status_code == 200,
                      result.status_code
                      ))
        cprint('{} [{}] {}'.format(result.status_code, sig, url), col, verb)

def extract(path):
    opath = os.path.dirname(path)
    start = os.listdir(opath)
    cprint(' -  Extracting {} to {}'.format(path, opath), Color.BLUE, True)
    if path.endswith('.zip'):
        with zipfile.ZipFile(path, 'r') as zip_f:
            zip_f.extractall(opath)
    elif '.tar' in path:
        if path.endswith('.tar.gz'):
            mode = 'r:gz'
        if path.endswith('.tar'):
            mode = 'r'
        if path.endswith('.tar.bz'):
            mode = 'r:bz'
        with tarfile.open(path, mode) as tar_f:
            os.mkdir(opath)
            tar_f.extractall(opath)
    new = set(os.listdir(opath)) - set(start)
    assert len(new) == 1, 'Extracted to root'
    retpath = os.path.join(opath, new.pop())
    return retpath

def pull_source(url, base_path):

    def write_outfile(ofile):
        with open(ofile, 'wb') as fout:
            cprint(' -  Writing to {}'.format(ofile), Color.BLUE, True)
            for bl in resp.iter_content(1024):
                fout.write(bl)
        return extract(ofile)

    cprint(' -  Pulling source from {}'.format(url), Color.BLUE, True)
    resp = session.get(url, stream=True)
    if resp.status_code == 200:
        fname = urlparse(resp.url).path.split('/')[-1]
        opath = write_outfile(os.path.join(base_path, fname))
    else:
        raise AssertionError("Invalid HTTP response: {}".format(resp.status_code))
    return opath

def walk_local(path):
    cprint(' -  Walking local path: {}'.format(path), Color.BLUE, True)
    nfiles = 0
    for root, dirs, files in os.walk(path):
        nfiles += len(files)
        for f in files:
            rmt_path = os.path.join(root, f)
            if rmt_path.startswith('.'):
                rmt_path = rmt_path[1:]
            if os.path.splitext(f)[1] not in args.ignore:
                this.web_paths.put(rmt_path)
    cprint(' -  Found {} files in software template'.format(nfiles), Color.BLUE, True)

def gather_results():
    count = 0
    while not result_q.empty():
        base, path, success, status = result_q.get()
        count += 1
        key = 'pass' if success else 'fail'
        this.result[base][key][path] = status
    cprint(' -  Gathered {} results'.format(count), Color.BLUE, True)

if __name__ == '__main__':
    try:
        cli()
        display_args()
        this.web_paths = queue.Queue()
        this.result_q = queue.Queue()
        cprint('[*] Preparing local template', Color.MSG)
        with tempfile.TemporaryDirectory() as this.outdir:
            if args.remote is not None:
                localpath = os.path.join(os.getcwd(), '.path_templates') if args.save else outdir
                localpath = pull_source(args.remote, localpath)
            elif args.local is not None:
                localpath = args.local
            else:
                raise ValueError('Invalid arg combo')   # Shouldn't happen
            for target in args.target:
                walk_local(localpath)   # Refresh the queue each iteration
                for i in range(args.max_threads):
                    cprint(' -  Starting thread {}'.format(i+1), Color.BLUE, True)
                    t = threading.Thread(target=test_url, args=(target, localpath))
                    if not args.dryrun:
                        t.start()
                if not args.dryrun:
                    while not this.web_paths.empty():
                        # Let the workors wrap up this round
                        time.sleep(1)
        cprint('[*] Collecting results...', Color.MSG)
        gather_results()
        if not args.dryrun:
            with open(args.outfile, 'w+') as of:
                json.dump(result, of, sort_keys=True, indent=2)
            cprint('[*] Wrote {}'.format(args.outfile), Color.MSG)
    except KeyboardInterrupt:
        sys.exit(0)
