#!/usr/bin/env python
#-*-coding:utf-8-*-

"""
"""

import eventlet
from eventlet.semaphore import Semaphore
import multiprocessing


class TaskQueue(object):
    tasker = None
    taskQueue = multiprocessing.Queue(5000)
    resultQueue = multiprocessing.Queue(5000)

    semaphore = Semaphore()
    lock = multiprocessing.Lock()

    @staticmethod
    def getTaskQueue():
        if TaskQueue.tasker is not None:
            return TaskQueue.tasker
        TaskQueue.tasker = TaskQueue()
        return TaskQueue.tasker

    def addTask(self, item):
        self.semaphore.acquire()
        self.lock.acquire()
        try:
            self.taskQueue.put(item,False)
        except:
            pass
        self.lock.release()
        self.semaphore.release()

    def frontTask(self):
        item = None
        self.semaphore.acquire()
        self.lock.acquire()
        if not self.taskQueue.empty():
            try:
                item = self.taskQueue.get(False)
            except:
                pass
        self.lock.release()
        self.semaphore.release()
        return item

    def getFirstTask(self):
        self.semaphore.acquire()
        self.lock.acquire()
        #print '******',self.taskQueue.empty()
        items = []
        while not self.taskQueue.empty():
            try:
                item = self.taskQueue.get(False)
                items.append(item)
            except:
                pass
        for i in items:
            try:
                self.taskQueue.put(i,False)
            except:
                pass
        item = items[0] if len(items) > 0 else None
        #print '------******',self.taskQueue.empty(),item
        self.lock.release()
        self.semaphore.release()
        return item

    def getTaskByTerminalId(self,terminalId):
        if not terminalId:
            return None
        item = None
        self.semaphore.acquire()
        self.lock.acquire()
        items = []
        while not self.taskQueue.empty():
            try:
                item = self.taskQueue.get(False)
                items.append(item)
            except:
                pass
        for i in items:
            if i.get('terminalId','') == terminalId:
                item = i
                break
            try:
                self.taskQueue.put(i,False)
            except:
                pass
        #print '------******',self.taskQueue.empty(),item
        self.lock.release()
        self.semaphore.release()
        return item


    def taskQueueLength(self):
        size = 0
        self.semaphore.acquire()
        self.lock.acquire()
        try:
            size = self.taskQueue.qsize()
        except:
            pass
        self.lock.release()
        self.semaphore.release()
        return size

    def taskQueueEmpty(self):
        isEmpty = True
        self.semaphore.acquire()
        self.lock.acquire()
        isEmpty = self.taskQueue.empty()
        self.lock.release()
        self.semaphore.release()
        return isEmpty


    def addResult(self, item):
        self.semaphore.acquire()
        self.lock.acquire()
        try:
            self.resultQueue.put(item,False)
        except:
            pass
        self.lock.release()
        self.semaphore.release()

    def frontResult(self):
        item = None
        self.semaphore.acquire()
        self.lock.acquire()
        if not self.resultQueue.empty():
            try:
                item = self.resultQueue.get(False)
            except:
                pass
        self.lock.release()
        self.semaphore.release()
        return item

    def resultQueueLength(self):
        size = 0
        self.semaphore.acquire()
        self.lock.acquire()
        try:
            size = self.resultQueue.qsize()
        except:
            pass
        self.lock.release()
        self.semaphore.release()
        return size

    def resultQueueEmpty(self):
        isEmpty = True
        self.semaphore.acquire()
        self.lock.acquire()
        isEmpty = self.resultQueue.empty()
        self.lock.release()
        self.semaphore.release()
        return isEmpty

    def getFirstResult(self):
        self.semaphore.acquire()
        self.lock.acquire()
        items = []
        while not self.resultQueue.empty():
            try:
                item = self.resultQueue.get(False)
                items.append(item)
            except:
                pass
        self.lock.release()
        self.semaphore.release()
        for i in items:
            self.addResult(i)
        item = items[0] if len(items) > 0 else None
        return item

taskQueue = TaskQueue.getTaskQueue()
