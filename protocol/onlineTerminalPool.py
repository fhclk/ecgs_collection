#!/usr/bin/env python
#-*-coding:utf-8-*-

import multiprocessing

from util.util import log

class OnlineTerminalPool(object):
    onlineTerminalPool = None
    manager = multiprocessing.Manager()
    collectPool = manager.dict()
    oldCollectPool = manager.list()
    lock = multiprocessing.Lock()

    def __init__(self):
        pass

    def addTerminal(self, terminalNo, uuid):
        self.lock.acquire()
        if terminalNo in self.collectPool.keys():
            old = self.collectPool[terminalNo]
            if old and old != uuid:
                self.oldCollectPool.append(old)
        self.collectPool[terminalNo] = uuid
        self.lock.release()


    def isOldTerminalCollection(self, terminalNo, uuid):
        if not terminalNo:
            return False
        result = False
        self.lock.acquire()
        if uuid in self.oldCollectPool or uuid != self.collectPool[terminalNo]:
            result = True
        self.lock.release()
        return result

    def deleteTerminal(self, terminalNo):
        self.lock.acquire()
        try:
            if terminalNo in self.collectPool:
                UUID = self.collectPool[terminalNo]
                if UUID in self.oldCollectPool:
                    self.oldCollectPool.remove(UUID)
                del self.collectPool[terminalNo]
        except Exception,e:
            log.error('从连接池中删除数据' + terminalNo + ' error:' + str(e))
        self.lock.release()

    def deleteFromOldCollectPool(self, uuid):
        self.lock.acquire()
        try:
            if uuid in self.oldCollectPool:
                self.oldCollectPool.remove(uuid)
        except Exception,e:
            log.error('从旧连接池中删除数据' + uuid + ' error:' +str(e))
            pass
        self.lock.release()

    def getCollectPool(self):
        pool = {}
        self.lock.acquire()
        pool = self.collectPool.copy()
        self.lock.release()
        return pool

    def getOldCollectPool(self):
        pool = []
        self.lock.acquire()
        pool = self.oldCollectPool[:]
        self.lock.release()
        return pool


    @staticmethod
    def getOnlineTerminalPool():
        if OnlineTerminalPool.onlineTerminalPool is not None:
            return OnlineTerminalPool.onlineTerminalPool
        OnlineTerminalPool.onlineTerminalPool = OnlineTerminalPool()
        return OnlineTerminalPool.onlineTerminalPool

onlineTerminalPool = OnlineTerminalPool.getOnlineTerminalPool()
