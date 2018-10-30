#!/usr/bin/env python
#-*-coding:utf-8-*-


import sys
sys.path.append("..")
import multiprocessing
import eventlet
from eventlet.green import socket
from eventlet import sleep as eventletSleep
from util.util import *
from protocol.protocols import *
from protocol.taskQueue import taskQueue
from protocol.terminalDevice import *
import time
import json
import uuid
from protocol.onlineTerminalPool import onlineTerminalPool as onlinePool
from .socketOpt import *
import platform


class Collection(object):

    def __init__(self, conf):
        self.serverPort = int(conf.get("collectServerPort".lower(), '9000'))
        self.maxGreenThreadsNum = int(conf.get("maxGreenThreadsNum".lower(),10000))
        self.threadsNum = int(conf.get("threadsNum".lower(), 2))
        self._lock = multiprocessing.Lock()
        self.terminalTimeout = int(conf.get('terminalTimeout'.lower(),'120'))
        try:
            self.server = eventlet.listen(('0.0.0.0',self.serverPort))
            self.server.settimeout(1.8)
            if platform.system() == 'Linux':
                set_keepalive_linux(self.server,interval_sec=60)
            if platform.system() == 'Darwin':
                # set_keepalive_osx(self.server, interval_sec=60)
                pass
        except Exception,e:
            log.error('创建服务器失败...' + str(e))
            sys.exit(0)


    def createThreads(self):
        num = self.threadsNum if self.threadsNum else 1
        processes = [None for i in range(num)]
        for i in range(num):
            processes[i] = multiprocessing.Process(target=self.startServer, args=(taskQueue,), name="CollectionProcess"+str(i))
            processes[i].start()
        for i in range(num):
            processes[i].join()


    def handle(self,sock,taskqueue):
        """
        """

        data = []
        currentTerminalId = ''
        currentUUID = '{0}'.format(uuid.uuid1())
        loopCount = 0 #轮巡计数,基数到300的时候检查一遍在线状态
        MAX_LOOP_COUNT = 30
        sock.settimeout(1.5)
        while True:
            # print '*-*-*',currentTerminalId,currentUUID,onlinePool.getCollectPool(),onlinePool.getOldCollectPool()
            print '*-*-*', currentTerminalId, currentUUID
            if currentTerminalId:
                if onlinePool.isOldTerminalCollection(currentTerminalId, currentUUID):
                    eventletSleep(60)
                    self.closeOldConnect(currentTerminalId, sock, currentUUID)
                    return

            try:
                recvData = sock.recv(1024)
                if isinstance(recvData,str) and len(recvData) == 0:
                    log.info('客户端已经断开' + currentTerminalId)
                    self.closeConnect(currentTerminalId,sock)
                    return

                if len(recvData) > 0:
                    #log.info('接收数据: ' + str(recvData))
                    if isinstance(recvData, str) or isinstance(recvData[0], str):
                        log.info('接收数据1: ' + str([hex(ord(str(n))) for n in recvData]))
                        recvData = [ord(s) for s in recvData]
                    else:
                        log.info('接收数据: ' + str([str(hex(n)) for n in recvData]))
                    data.extend(recvData)
            except socket.timeout, e:
                pass
            except socket.error, e:
                log.error('接收数据网络异常' + str(e))
                self.closeConnect(currentTerminalId,sock)
                return

            eventletSleep(0.2)
            time.sleep(0.2)

            packetType = 0x00
            packet = None
            if len(data) > 0:
                (packetType,packet,endIndex) = BaseProtocol.getProtocolFromData(data)
                endIndex = endIndex if endIndex else 0
                if endIndex > 0:
                    if endIndex == len(data):
                        data = []
                    else:
                        data = data[endIndex:len(data)]

            if packet and len(packet) > 0:
                subProtocol = ProtocolFactory.makeProtocol(packetType)

                if subProtocol is not None:
                    subProtocol.parseRecvPacket(packet)
                    # 报文有效
                    if subProtocol.valid:
                        if not currentTerminalId:
                            terminalId = str(hexListToInt(subProtocol.deviceid))
                            newTerminal = Terminal(terminalId)
                            isHas = newTerminal.hasTerminal()
                            if not isHas:
                                self.closeConnect(currentTerminalId, sock)
                                return

                            newTerminal.hasnotAndAddTerminalRecord()
                            onlinePool.addTerminal(terminalId, currentUUID)

                        subProtocol.handleTransaction()
                        currentTerminalId = str(hexListToInt(subProtocol.deviceid))

                        # 终端发来的数据，返回响应数据
                        if subProtocol.source == SendSource.HARDWARE_TERMINAL and not isinstance(subProtocol, DeviceUpdateProtocol):
                            if subProtocol.needResponse:
                                try:
                                    backPacket = subProtocol.buildBackPacket()
                                except Exception:
                                    pass
                                else:
                                    buf = bytearray(backPacket)
                                    for i in xrange(3):
                                        try:
                                            sock.send(buf)
                                        except socket.timeout, e:
                                            log.warn('响应终端超时' + str(e))
                                            continue
                                        except Exception, e:
                                            log.error('响应终端网络异常' + str(e))
                                            if i != 2:
                                                continue
                                            else:
                                                self.closeConnect(currentTerminalId, sock)
                                                return
                                        log.info('响应终端: ' + str([str(hex(n)) for n in backPacket]))
                                        break
                            else:
                                if isinstance(subProtocol, NormalDataProtocol):
                                    if subProtocol.ownContentDataType == [0x00, 0x17]:
                                        recordId = subProtocol.updateToDoResult(False)
                                        dic = {'at': 'send', 'type': 'end', 'id': recordId, 'result': '1'}
                                        taskqueue.addResult(json.dumps(dic))

                        # 服务器下达的命令，将相应数据返回给服务器
                        if subProtocol.source == SendSource.WEB_SERVER:
                            recordId = subProtocol.updateToDoResult()
                            dic = {'at': 'send', 'type': 'end', 'id': recordId, 'result': '1'}
                            taskqueue.addResult(json.dumps(dic))


            eventletSleep(0.5)
            time.sleep(0.5)

            #不是最新的连接不下发参数
            if onlinePool.isOldTerminalCollection(currentTerminalId, currentUUID):
                eventletSleep(0.5)
                continue

            if not taskqueue.taskQueueEmpty():
                taskItem = taskqueue.getTaskByTerminalId(currentTerminalId)
                if taskItem:
                    ptypeStr = taskItem.get('command','')
                    ptype = {'setParams':0x92,'updateTerm':0x93,'addClock':0x94,'deleteClock':0x95}.get(ptypeStr,0x00)
                    subProtocol = ProtocolFactory.makeProtocol(ptype)
                    terminalId = taskItem.get('terminalId','0')
                    if terminalId == currentTerminalId:
                        subProtocol.deviceid = intToHexListWithLen(int(terminalId),5)
                        backPacket = subProtocol.buildPacket(taskItem) or []
                        buf = bytearray(backPacket)
                        for i in xrange(3):
                            try:
                                sock.send(buf)
                            except socket.timeout,e:
                                log.warn('向终端发送数据超时' + str(e))
                                continue
                            except Exception,e:
                                log.error('网络异常' + str(e))
                                if i != 2:
                                    continue
                                else:
                                    self.closeConnect(currentTerminalId,sock)
                                    return
                            log.info('下达数据: ['+currentTerminalId+'] ('+currentUUID+') ' + str([str(hex(n)) for n in backPacket]))
                            dic = {'at':'send','type':'start','id':taskItem.get('id','')}
                            taskqueue.addResult(json.dumps(dic))
                            break

            # if packetType == 0x03: #固件更新
            #     subProtocol = DeviceUpdateProtocol()
            #     subProtocol.parseRecvPacket(packet)
            #     if subProtocol.valid:
            #         if subProtocol.source == 'terminal':
            #             finished = True
            #             for readData in subProtocol.readUpdateFileIter():
            #                 if readData:
            #                     subProtocol.asyncCount += 1
            #                     subProtocol.backContentData = readData
            #                     backPacket = subProtocol.buildBackPacket()
            #                     buf = bytearray(backPacket)
            #                     try:
            #                         sock.send(buf)
            #                     except Exception,e:
            #                         log.error('发送固件更新程序失败' + str(e))
            #                         finished = False
            #                         #sock.close()
            #                         self.closeConnect(currentTerminalId,sock)
            #                         return
            #             if finished:
            #                 subProtocol.asyncCount += 1
            #                 subProtocol.backContentData = []
            #                 backPacket = subProtocol.buildBackPacket()
            #                 buf = bytearray(backPacket)
            #                 try:
            #                     sock.send(buf)
            #                 except Exception,e:
            #                     log.error('发送固件更新程序失败' + str(e))
            #                     finished = False
            #                     #sock.close()
            #                     self.closeConnect(currentTerminalId,sock)
            #                     return

            loopCount += 1
            if loopCount == MAX_LOOP_COUNT:
                loopCount = 0
                if KeepaliveProtocol.isTimeout(currentTerminalId, self.terminalTimeout):
                    self.closeConnect(currentTerminalId,sock)
                    return



    def closeConnect(self,deviceid,sock):
        log.info('断开终端连接: ' + deviceid)
        try:
            sock.close()
        except Exception,e:
            log.info('关闭socket失败' + str(e))
            return
        finally:
            pass
        KeepaliveProtocol.updateTerminalStatus(deviceid,False)

        onlinePool.deleteTerminal(deviceid)

    def closeOldConnect(self,deviceid,sock, UUID):
        log.info('断开已连接终端连接: ' + deviceid)
        try:
            sock.close()
        except Exception,e:
            log.info('关闭socket失败' + str(e))
            self.closeOldConnect(deviceid,sock)
            return
        finally:
            pass

        onlinePool.deleteFromOldCollectPool(UUID)



    def startServer(self,taskqueue):
        """
        """

        #server = eventlet.listen(('0.0.0.0',self.serverPort))
        pool = eventlet.GreenPool(self.maxGreenThreadsNum)

        while True:
            new_sock = None
            address = None
            self._lock.acquire()
            try:
                new_sock, address = self.server.accept()
            except Exception,e:
                pass
            self._lock.release()
            if new_sock:
                log.info('新终端连接:' +  str(address))
                try:
                    pool.spawn_n(self.handle, new_sock,taskqueue)
                except Exception,e:
                    log.error(str(e))
            time.sleep(1.5)
