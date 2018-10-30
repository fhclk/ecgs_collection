#! /usr/bin/env python
#-*-coding:utf-8-*-

import sys
sys.path.append('..')

import multiprocessing


from util.util import *


def main():
    log.info('===============================>>>')
    log.info('启动服务器...')


    from database.mysqlConnPool import MysqlConn
    mysqlConner = MysqlConn(readconf('config.conf', 'mysql'))
    if not mysqlConner.testConnection():
        sys.exit(0)

    from collection.collection import Collection
    from communication.innerCommunication import InnerCommunication
    from monitor.monitor import Monitor


    innerCommun = InnerCommunication(readconf('config.conf','web-server'))
    innerCommun.createSingleProc()

    monitor = Monitor(readconf('config.conf','collection-server'))
    monitor.createProc()

    collection = Collection(readconf('config.conf','collection-server'))
    collection.createThreads()


import signal
def signal_handle(signum, frame):
    print '终止程序，信号:', signum

    from protocol.terminalDevice import Terminal, Device
    Terminal.setAllTerminalOffline()
    Device.setAllDeviceOffline()
    sys.exit(0)

if __name__ == '__main__':

    signal.signal(signal.SIGHUP, signal_handle)
    signal.signal(signal.SIGTERM, signal_handle)
    signal.signal(signal.SIGINT, signal_handle)

    main()

    signal.pause()
