#!/usr/bin/env python

import click
import sys
import json
from datetime import datetime
import os
import threading
import time
from random import random
sys.path.append("libs");
from log import log
import worker

class Config(object):

    def __init(self):
        self.debug = False

pass_config = click.make_pass_decorator(Config, ensure=True)

@click.group()
@click.option('--debug', is_flag = True)
@click.option('--path', type = click.Path())
@pass_config
def cli(opt, debug, path):
    ''' This script is built upon worker lib\n
    e.g.\n
    '''
    opt.debug = debug
    if path is None:
        path = '.'
    opt.path = path

@cli.command()
@click.option('--mode', default = 'm', help = 'd/w/m/y: daily, weekly, monthly or yearly')
@click.argument('code', required = True)
@pass_config
def get_basics(opt, mode, code):
    ''' This command get stock basics\n
    e.g.\n
    '''
    if opt.debug:
        click.echo('opt path: %s' %opt.path)
        click.echo('out: %s' %out)
    print json.loads(worker.get_stock_basics())[code]
    return None

def add_quarter(year, quarter):
    if (quarter == 4):
        q = 1
        y = year + 1
    else:
        q = quarter + 1
        y = year
    return y, q

def get_report_thread(fq):
    y = fq.split('q')[0]
    q = fq.split('q')[1]
    try:
        print "[%s] exec %s" % (datetime.now().strftime("%H:%M:%S.%f"), fq)
        #do get
	#time.sleep(random())
        worker.get_report_data(y, q)
        print "[%s] done %s" % (datetime.now().strftime("%H:%M:%S.%f"), fq)
    except Exception, e:
        print '%s failed, err%s' % (fq, e)

@cli.command()
@click.option('--mode', default = 'oneshot', help = 'oneshot|iterate')
@click.argument('year', required = True)
@click.argument('quarter', required = True)
@pass_config
def get_report(opt, mode, year, quarter):
    ''' This command get stock report\n
    oneshot: get report for particular fiscal quarter\n
    iterate: get all history report from given time to now\n
    e.g.\n
    '''
    if mode == 'iterate':
        fqs = []

        # fill in fqs (fiscal quarters)
        y = int(year)
        q = int(quarter)
        y_now = datetime.now().year
        q_now = (datetime.now().month-1)/3
        while (y < y_now) | ((y == y_now) & (q <= q_now)):
            fqs.append(str(y) + 'q' + str(q))
            y, q = add_quarter(y, q)
	print fqs

        print "[%s] start" % datetime.now().strftime("%H:%M:%S.%f")

        # multi thread
        threads = []
        for fq in fqs:
            th = threading.Thread(target=get_report_thread, args=(fq,))
            th.start()
            threads.append(th)

        for th in threads:
            th.join()

        '''
        # single thread
        for fq in fqs:
            get_report_thread(fq)
        '''

        print "[%s] finish" % datetime.now().strftime("%H:%M:%S.%f")
    else:
        worker.get_report_data(year, quarter)
    return None

@cli.command()
@click.option('--mode', default = 'pe', help = 'pe|ebit|ebitda')
@click.option('--years', default = 5, help = 'number of years')
@click.argument('security', required = True)
@pass_config
def eval(opt, mode, years, security):
    ''' Evaluate security price range according to different key indicators\n
    mode:\n
        pe: make use of Gaussian Distribution of P/E history\n
        ebit: make use of EV/EBIT\n
        ebitda: make use of EV/EBITDA\n
    years:\n
        number of years we trace back, to take the hitory data into account\n
    security:\n
        one or more security code, separated by ','\n
    e.g.\n
    evaluate 600690 according to pe history in 5 years\n
    # flats eval --mode pe --years 5 600690,600422,002415\n
    '''
    log.info('mode: %s', mode)
    log.info('years: %d', years)
    s_arr = security.split(',')
    log.info('security(%d): %s', len(s_arr), security)
    for s in s_arr:
        log.debug('eval %s(%s)', s, worker.get_name_by_code(s))
        l, c, r = worker.get_est_price(mode, years, s)
        log.debug('dynamic est: %.2f~%.2f~%.2f', l, c, r)

    return None

# Below lines are used to run this script directly in python env:
if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding("utf-8")
    cli()
