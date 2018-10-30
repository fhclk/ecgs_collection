#!/usr/bin/env python
#-*-coding:utf-8-*-

import websocket
import sys
import multiprocessing
import json

from protocol.taskQueue import taskQueue
from time import sleep
from util.util import *
from protocol.terminalDevice import Device,Terminal

class InnerCommunication(object):
    """
    """

    def __init__(self,conf):
        self.wsAddr = conf.get('webSocketAddr'.lower(),'ws://127.0.0.1:8080/waterSupply/websocket/tcpipServer')
        self.ws = None
        self._lock = multiprocessing.Lock()

        if not self.reconnectServer():
            sys.exit(0)


    def createMultiProc(self):
        multiprocessing.Process(target=self.sendHandle, args=(), name="INNER_COMMU_SEND_PROC").start()
        multiprocessing.Process(target=self.recvHandle, args=(), name="INNER_COMMU_RECV_PROC").start()

    def createSingleProc(self):
        multiprocessing.Process(target=self.handle, args=(), name="INNER_COMMU_PROC").start()

    def sendHandle(self):
        """
        """

        MAX_NULL_LOOP = 60
        loop_count = 0;

        while True:
            if not taskQueue.resultQueueEmpty():
                result = taskQueue.frontResult()
                try:
                    #resultStr = json.dumps(result)
                    resultStr = result
                except Exception, e:
                    log.error('转json字符串错误: ' + str(result))
                if resultStr:
                    self._lock.acquire()
                    try:
                        self.ws.send(resultStr)
                    except websocket.WebSocketTimeoutException,e:
                        pass
                    except websocket.WebSocketConnectionClosedException,e:
                        log.error('向web服务器发送信息失败: ' + resultStr)
                        self.reconnectServer()
                    finally:
                        self._lock.release()
                    log.info('send to web: ' + str(result))

                loop_count = 0;

            sleep(1)
            loop_count += 1
            if loop_count == MAX_NULL_LOOP:
                loop_count = 0
                self._lock.acquire()
                # self.reconnectServer()
                try:
                    self.ws.send('a')
                except websocket.WebSocketTimeoutException, e:
                    pass
                except websocket.WebSocketConnectionClosedException, e:
                    log.error('向web服务器发送测试连接信息失败: ' + str(e))
                    self.reconnectServer()
                finally:
                    self._lock.release()
                pass


    def recvHandle(self):
        """
        """

        while True:
            sleep(1)
            recvData = None
            self._lock.acquire()
            try:
                recvData = self.ws.recv()
            except websocket.WebSocketTimeoutException,e:
                pass
            except Exception,e:
                log.error('websocket error:'+str(e))
                self.reconnectServer()
            finally:
                self._lock.release()

            sleep(0.5)
            if recvData and len(recvData) > 0:
                self.handleRecvData(recvData)

            sleep(0.5)


    def handle(self):

        MAX_NULL_LOOP = 60
        loop_count = 0;
        while True:
            sleep(0.5)
            recvData = None
            try:
                recvData = self.ws.recv()
            except websocket.WebSocketTimeoutException,e:
                pass
            except websocket.WebSocketConnectionClosedException,e:
                log.error('websocket error:'+str(e))
                self.reconnectServer()
            finally:
                pass

            sleep(0.5)
            if recvData and len(recvData) > 0:
                self.handleRecvData(recvData)

            sleep(0.5)

            if not taskQueue.resultQueueEmpty():
                result = taskQueue.frontResult()
                try:
                    # resultStr = json.dumps(result)
                    resultStr = result
                except Exception, e:
                    log.error('转json字符串错误: ' + str(result))
                if resultStr:
                    try:
                        self.ws.send(resultStr)
                    except websocket.WebSocketTimeoutException, e:
                        pass
                    except websocket.WebSocketConnectionClosedException, e:
                        log.error('向web服务器发送信息失败: ' + resultStr)
                        self.reconnectServer()
                    finally:
                        pass
                    log.info('send to web: ' + str(result))

                loop_count = 0;

            sleep(1)
            loop_count += 1
            if loop_count == MAX_NULL_LOOP:
                loop_count = 0
                try:
                    self.ws.send('a')
                except websocket.WebSocketTimeoutException, e:
                    pass
                except websocket.WebSocketConnectionClosedException, e:
                    log.error('向web服务器发送测试连接信息失败: ' + str(e))
                    self.reconnectServer()
                finally:
                    pass


    def handleRecvData(self, recvData):
        '''
        处理从web端接收到的数据
        :param recvData: 接收到的数据
        :return: 
        '''
        if not recvData or len(recvData) == 0:
            return
        try:
            command = json.loads(recvData)
            log.info('接收到web服务器的指令: ' + recvData)
        except websocket.WebSocketConnectionClosedException, e:
            log.error('解析web命令错误: ' + str(e))
        if command:
            if command.get('id'):
                dic = {'dataType': '',
                       'terminalId': '',
                       'value': '',
                       'command': 'setParams',
                       'deviceId': '',
                       'deviceType': '2'}
                dic['command'] = 'setParams'
                dic['value'] = '0'
                dic['count'] = 0
                dic['id'] = command.get('id')

                data = Device.getDistributeData(command.get('id'))

                print type(data), len(data)

                if len(data) == 0:
                    data = Terminal.getDistributeData(command.get('id'))

                if data:
                    data = data[0]
                if data and len(data) > 0:
                    sendCommand = data[0]
                    dic['terminalId'] = data[-2]
                    dic['deviceId'] = data[-1]
                    dic['count'] = data[2]
                    if sendCommand == '0':
                        dic['dataType'] = ''
                        dic['command'] = 'updateTerm'
                        pass
                    if sendCommand == '1':
                        dic['dataType'] = '6'
                        dic['value'] = dic['deviceId']
                        dic['command'] = 'addClock'
                        pass
                    if sendCommand == '2':
                        dic['dataType'] = '7'
                        dic['value'] = dic['deviceId']
                        dic['command'] = 'deleteClock'
                        pass
                    if sendCommand == '3':
                        dic['dataType'] = '13'
                        dic['value'] = '1'
                        pass
                    if sendCommand == '4':
                        dic['dataType'] = '13'
                        dic['value'] = '0'
                        pass
                    if sendCommand == '5':
                        dic['dataType'] = '12'
                        dic['value'] = data[3]
                        pass
                    if sendCommand == '6':
                        dic['dataType'] = '11'
                        dic['value'] = data[3]
                        pass

                    if sendCommand == '7':
                        dic['dataType'] = '8'
                        cardId = data[1]
                        cardPwdL = Device.getCardPwdByCardId(cardId)
                        cardPwd = 0
                        cardCode = '0'
                        if cardPwdL and len(cardPwdL) > 0:
                            cardPwd = cardPwdL[0][0]
                            cardCode = cardPwdL[0][1]
                        try:
                            value = 0
                            if isinstance(cardPwd, int):
                                value = (int(cardCode, 16) << 64) + (int(cardPwd) << 16) + int(data[3], 16)
                            if isinstance(cardPwd, str) or isinstance(cardCode, unicode):
                                value = (int(cardCode, 16) << 64) + (int(cardPwd, 16) << 16) + int(data[3], 16)
			    print dic, type(cardPwd)
                            dic['value'] = value
                        except:
                            pass
                        pass
                    # 删除卡权限
                    if sendCommand == '8':
                        dic['dataType'] = '8'
                        cardId = data[1]
                        cardPwdL = Device.getCardPwdByCardId(cardId)
                        cardPwd = 0
                        cardCode = '0'
                        if cardPwdL and len(cardPwdL) > 0:
                            cardCode = cardPwdL[0][1]
                        try:
                            if isinstance(cardCode, int):
                                value = (int(cardCode) << 64) + (int(cardPwd) << 16) + int(data[3], 16)
                            if isinstance(cardCode, str) or isinstance(cardCode, unicode):
                                value = (int(cardCode, 16) << 64) + (int(cardPwd) << 16) + int(data[3], 16)
                            dic['value'] = value
                        except:
                            pass
                        pass
                    if sendCommand == '9':
                        dic['dataType'] = '14'
                        orginV = data[3] or 0
                        realV = int(float(orginV) * 100.0)
                        dic['value'] = realV
                        pass
                    if sendCommand == '10':
                        dic['dataType'] = '15'
                        dic['value'] = data[3]
                        pass
                    if sendCommand == '16':
                        dic['dataType'] = '16'
                        dic['value'] = data[3]
                        pass
                    if sendCommand == '17':
                        dic['dataType'] = '17'
                        dic['value'] = data[3]
                        pass
                taskQueue.addTask(dic)

    def reconnectServer(self):
        if self.ws:
            try:
                self.ws.close()
            except Exception,e:
                pass
        connectResult = False
        for i in xrange(3):
            try:
                log.info('连接web服务器: ' + self.wsAddr)
                self.ws = websocket.create_connection(self.wsAddr)
                self.ws.settimeout(0.8)
                log.info('连接web服务器成功')
                connectResult = True
            except websocket.WebSocketTimeoutException,e:
                log.error('连接web服务器超时')
                connectResult = False
                sleep(1)
            except Exception,e:
                log.error('连接web服务器失败'+str(e))
                connectResult = False
                sleep(1)
            if connectResult:
                break
        return connectResult


    def __del__(self):
        try:
            self.ws.close()
        except Exception,e:
            pass
