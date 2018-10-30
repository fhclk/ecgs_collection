#!/usr/bin/env python
#-*-coding:utf-8-*-


from time import sleep
from datetime import datetime
import multiprocessing
from protocol.terminalDevice import Terminal

class Monitor(object):
    """
    监测主机和锁的在离线状态，超过规定时间，就更新表中设备的在离线状态
    """

    def __init__(self, conf):
        self.deviceTimeout = int(conf.get('deviceTimeout'.lower(), '600'))
        self.terminalTimeout = int(conf.get('terminalTimeout'.lower(), '120'))

    def createProc(self):
        '''
        创建监管进程
        '''
        multiprocessing.Process(target=self.handle, args=(), name="MONITOR_PROC").start()

    def handle(self):
        """
        """

        terminalTimeout = self.terminalTimeout
        while True:
            data = Terminal.getOnlineTerminals()
            timeoutTerminalIdList = []

            for item in data:
                s = item[1]
                if not s:
                    continue
                if isinstance(s, str):
                    lastTim = datetime.strptime(s, '%Y-%m-%d %H:%M:%S')
                else:
                    lastTim = s

                now = datetime.now()
                nt = now - lastTim
                if nt.total_seconds() > terminalTimeout:
                    timeoutTerminalIdList.append(str(item[-1]))
                    pass

            #批量更新主机离线状态
            if len(timeoutTerminalIdList) > 0:
                Terminal.updateTerminalOfflineStatus(timeoutTerminalIdList)

            sleep(2)

            #主机离线时，挂在主机下的锁离线
            Terminal.updateTerminalDeviceOfflineStatus()

            sleep(10)


