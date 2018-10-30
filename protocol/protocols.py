#! /usr/bin/env python
#-*-coding:utf-8-*-

from datetime import datetime
import pdb
from util.util import *
from protocol.terminalDevice import *
import json
from taskQueue import taskQueue

class SendSource(object):
    WEB_SERVER = 'web-server'
    HARDWARE_TERMINAL = 'terminal'


class BaseProtocol(object):
    """
    终端通信协议基类，包含服务器接收到的报文，以及要返回给终端的报文
    """

    baseHeader = [0x61,0x78]

    def __init__(self):
        self.length = [0x00, 0x00]
        self.deviceid = []  #5bytes
        self.hardwareVersion = 0x00
        self.syncCount = 0x00
        self.packetType = 0x00
        self.softwareVersion = 0x00
        self.year = 0x00
        self.month = 0x00
        self.day = 0x00
        self.hour = 0x00
        self.minute = 0x00
        self.second = 0x00
        self.contentData = [] #N bytes
        self.CRC = 0x00

        self.packet = []

        """
        服务器返回数据
        """
        self.backBaseHeader = [0x61, 0x78]
        self.backLength = [0x00, 0x00]
        self.backDeviceid = [] #5bytes
        self.backKeep = 0x00
        self.backSyncCount = 0x00
        self.backPacketType = 0x00
        self.backSoftwareVersion = 0x00
        self.backYear = 0x00
        self.backMonth = 0x00
        self.backDay = 0x00
        self.backHour = 0x00
        self.backMinute = 0x00
        self.backSecond = 0x00
        self.backContentData = [] #N bytes
        self.backCRC = 0x00

        self.valid = False  #解析报文，如果报文是有效的，则该值为True
        self.source = SendSource.HARDWARE_TERMINAL #
        self.needResponse = True

        pass

    @classmethod
    def getProtocolFromData(cls, data):
        """
        从收到的数据中识别出报文，并取出报文
        para data: 接收到的数据
        return (报文类型, 报文, 报文长度)
        """
        if len(data) < 10:
            return (None,None,None)
        for i in range(0, len(data) - 1):
            if data[i] == cls.baseHeader[0] and data[i + 1] == cls.baseHeader[1]:
                lengthList = data[i+2:i+2+2]
                length = cls.getLength(lengthList)
                if length + 5 > len(data):
                    return (None,None,None)
                packetType = data[i+11]
                contentDataLen = length - 15
                packet = data[i:i+19+contentDataLen+1]
                return (packetType,packet,i + 18 + contentDataLen + 1)
        return (None,None,None)

    @classmethod
    def getLength(cls,length):
        """
        """
        if len(length) == 2:
            return length[0] * 256 + length[1]
        return 0

    def parseRecvPacket(self,packet):
        """
        解析收到的报文
        """
        log.info('解析报文: ' + str([hex(n) for n in packet]))
        self.length = packet[2:2+2]
        length = self.getLength(self.length)
        contentDataLen = length - 15
        if len(packet) < length + 5:
            log.error('解析报文错误: ' + str([hex(n) for n in packet]))
            return
        self.deviceid = packet[4:4+5]
        self.hardwareVersion = packet[9]
        self.syncCount = packet[10]
        self.packetType = packet[11]
        self.softwareVersion = packet[12]
        self.year = packet[13]
        self.month = packet[14]
        self.day = packet[15]
        self.hour = packet[16]
        self.minute = packet[17]
        self.second = packet[18]
        self.contentData = packet[19: 19+contentDataLen]
        self.CRC = packet[19+contentDataLen]
        self.valid = True if self.CRC == self.calCRC(packet) else False


    def buildBackPacket(self):
        """
        构建返回的报文
        """
        self.backDeviceid = self.deviceid #5bytes
        self.backSyncCount = self.syncCount
        self.backSoftwareVersion = self.softwareVersion

        now = datetime.now()
        self.backYear = now.year - 2000
        self.backMonth = now.month
        self.backDay = now.day
        self.backHour = now.hour
        self.backMinute = now.minute
        self.backSecond = now.second
        backPacket = []

        backPacket.extend(self.backBaseHeader)
        backPacket.extend(self.backLength)
        backPacket.extend(self.backDeviceid)
        backPacket.append(self.backKeep)
        backPacket.append(self.backSyncCount)
        backPacket.append(self.backPacketType)
        backPacket.append(self.backSoftwareVersion)
        backPacket.append(self.backYear)
        backPacket.append(self.backMonth)
        backPacket.append(self.backDay)
        backPacket.append(self.backHour)
        backPacket.append(self.backMinute)
        backPacket.append(self.backSecond)
        backPacket.extend(self.backContentData)
        backPacket.append(self.backCRC)

        self.backLength[0] = (len(backPacket) - 5) >> 8
        self.backLength[1] = (len(backPacket) - 5) & 0xff

        backPacket[2] = self.backLength[0]
        backPacket[3] = self.backLength[1]

        self.backCRC = self.calCRC(backPacket)
        backPacket[-1] = self.backCRC
        return backPacket

    def buildPacket(self,dataDict):
        pass


    def calCRC(self, packet):
        """
        计算校验码
        """
        if len(packet) < 5:
            return 0x00
        s = 0x00
        for i in range(4, 4+(len(packet)-5)):
            s += packet[i]
        return s&0xff

    def handleTransaction(self):
        """
        处理具体的协议事务,子类重写该方法
        """
        pass


class AddNewLockProtocol(BaseProtocol):
    """
    新增锁
    """

    def __init__(self):
        super(AddNewLockProtocol,self).__init__()
        self.pecketType = 0x94
        self.backPacketType = 0x04
        self.source = SendSource.WEB_SERVER


    def handleTransaction(self):
        pass

    def buildPacket(self,dataDict):
        if dataDict:
            self.backSyncCount = int(dataDict.get('count',0) or 0) & 0xff
            self.syncCount = int(dataDict.get('count',0) or 0) & 0xff
            dataValue = int(dataDict.get('value','0') or 0)
            self.backContentData = intToHexListWithLen(dataValue,4)
        return self.buildBackPacket()

    def updateToDoResult(self):
        if self.contentData and len(self.contentData) > 0:
            device = Device(str(hexListToInt(self.deviceid)),str(hexListToInt(self.contentData)))
            data = device.getSendRecord(self.syncCount)
        else:
            terminal = Terminal(str(hexListToInt(self.deviceid)))
            print '=====',terminal.terminalId,terminal.terminalUUID
            data = terminal.getSendRecord(self.syncCount)
        if data and len(data) > 0:
            return data[0][0]
        return ''

class DeleteLockProtocol(BaseProtocol):
    """
    删除锁
    """

    def __init__(self):
        super(DeleteLockProtocol,self).__init__()
        self.pecketType = 0x95
        self.backPacketType = 0x05
        self.source = SendSource.WEB_SERVER


    def handleTransaction(self):
        pass

    def buildPacket(self,dataDict):
        if dataDict:
            self.backSyncCount = int(dataDict.get('count',0) or 0) & 0xff
            self.syncCount = int(dataDict.get('count',0) or 0) & 0xff
            dataValue = int(dataDict.get('value','0') or 0)
            self.backContentData = intToHexListWithLen(dataValue,4)
        return self.buildBackPacket()

    def updateToDoResult(self):
        if self.contentData and len(self.contentData) > 0:
            device = Device(str(hexListToInt(self.deviceid)),str(hexListToInt(self.contentData)))
            data = device.getSendRecord(self.syncCount)
        else:
            terminal = Terminal(str(hexListToInt(self.deviceid)))
            print '=====',terminal.terminalId,terminal.terminalUUID
            data = terminal.getSendRecord(self.syncCount)
        if data and len(data) > 0:
            return data[0][0]
        return ''

class KeepaliveProtocol(BaseProtocol):
    """
    主机心跳
    """

    def __init__(self):
        super(KeepaliveProtocol,self).__init__()
        self.pecketType = 0x01
        self.backPacketType = 0x91
        self.terminal = None

    @staticmethod
    def isTimeout(deviceid, timeout):
        if not deviceid:
            return
        if isinstance(deviceid,list):
            deviceid = str(hexListToInt(deviceid))
        terminal = Terminal(deviceid)
        return terminal.isTerminalTimeout(timeout)

    @staticmethod
    def updateTerminalStatus(deviceid, status):
        """
        更新终端的在线情况
        para status:是否在线  True:在线   False:离线
        """
        if not deviceid:
            return
        if isinstance(deviceid,list):
            deviceid = str(hexListToInt(deviceid))
        terminal = Terminal(deviceid)
        terminal.updateTerminalStatus(status)

    def updateKeepaliveTime(self):
        """
        跟新数据库中记录的最新心跳时间
        """
        import time
        tim = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        self.terminal.updateTerminalKeepalive(tim)

    def handleTransaction(self):
        self.terminal = Terminal(str(hexListToInt(self.deviceid)))
        self.updateKeepaliveTime()
        KeepaliveProtocol.updateTerminalStatus(self.deviceid,True)



class NormalDataProtocol(BaseProtocol):
    """
    正常数据上传
    """

    def __init__(self):
        super(NormalDataProtocol,self).__init__()
        self.packetType = 0x02
        self.backPacketType = 0x92

        self.ownContentLength = [0x00, 0x00]
        self.ownContentDeviceType = [] #4bytes
        self.ownContentDeviceid = [] #4bytes
        self.ownContentDataType = [0x00, 0x00]
        self.ownContentData = [] #n bytes
        self.device = None

    def parseContentData(self):
        if len(self.contentData) < 12:
            self.valid = False
            return False
        self.ownContentLength = self.contentData[0:2]
        length = self.getLength(self.ownContentLength)
        length -= 10
        self.ownContentDeviceType = self.contentData[2:2+4]
        self.ownContentDeviceid = self.contentData[6:6+4]
        self.ownContentDataType = self.contentData[10:10+2]
        self.ownContentData = self.contentData[12:12+length] if length > 0 else []
        return True

    def handleData(self):
        if not self.device:
            return

        if len(self.ownContentData) < 6:
            return

        dataType = self.ownContentDataType[0] * 256 + self.ownContentDataType[1]
        content = '设备类型:' + str([hex(n) for n in self.ownContentDeviceType]) +  \
        ' 设备id:' + str([hex(n) for n in self.ownContentDeviceid]) + \
        ' 内容:' + str([hex(n) for n in self.ownContentData])

        try:
            tim = datetime(2000 + self.year,self.month,self.day,self.hour,self.minute,self.second)
        except:
            tim = datetime.now()

        timStr = tim.strftime('%Y-%m-%d %H:%M:%S')

        ownContentTim = self.ownContentData[0:6]
        ownContentData = self.ownContentData[6:]

        uploadTim = self.parseUploadTim(ownContentTim)
        timStr = timStr if not uploadTim else uploadTim.strftime('%Y-%m-%d %H:%M:%S')


        deviceOffLine = self.device.isOffline()
        if deviceOffLine:
            self.device.updateDeviceStatus(True)
        otherInfo = '1' if deviceOffLine else None


        # if dataType == 0x0001:
        #     log.info('锁心跳: ' + content)
        #     import time
        #     ktim = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        #     self.device.updateDeviceKeepalive(ktim)
        #     self.device.updateDeviceStatus(True)

        if dataType == 0x0002:
            log.info('震动报警: ' + content)
            contentData = hexListToHexStrBlank(self.ownContentData)
            recordId = self.device.addUploadRecord(timStr,'','5',contentData)
            # self.device.notifyExcepMessage(dataType)
            exceptRecordId = self.device.addUploadExceptRecord(recordId)
            if exceptRecordId:
                self.device.notifyExcepMessage(dataType, recordId, exceptRecordId)
            self.device.updateDeviceStatus(True)

        if dataType == 0x0003:
            log.info('电压: ' + content)
            v = hexListToInt(ownContentData) / 100.0
            self.device.updateDeviceV(v)
            self.device.updateDeviceVStatus(v)
            self.device.updateDeviceStatus(True)

        if dataType == 0x0004:
            log.info('打卡巡检: ' + content)
            if len(self.ownContentData) < 17:
                log.info('打卡巡检, 上报数据不对')
                return
            cardNoList = ownContentData[0:4]
            cardNo = hexListToHexStr(cardNoList)
            cardPwdList = ownContentData[4:10]
            cardPwd = hexListToHexStr(cardPwdList)
            cardGroup = ownContentData[10]
            contentData = hexListToHexStrBlank(self.ownContentData)
            self.device.addUploadRecord(timStr,cardNo,'4',contentData,otherInfo)
            self.device.updateDeviceStatus(True)
            self.device.addDailyCheckReport(timStr, cardNo, cardPwd)

        if dataType == 0x0005:
            log.info('打卡开锁: ' + content)
            if len(self.ownContentData) < 17:
                return
            cardNoList = ownContentData[0:4]
            cardNo = hexListToHexStr(cardNoList)
            cardPwdList = ownContentData[4:10]
            cardPwd = hexListToHexStr(cardPwdList)
            cardGroup = ownContentData[10]
            self.device.addOpenOrCloseRecord(timStr,None,cardNo)
            contentData = hexListToHexStrBlank(self.ownContentData)
            recordId = self.device.addUploadRecord(timStr,cardNo,'1',contentData,otherInfo)
            exceptRecordId = self.device.addUploadExceptRecord(recordId)
            if exceptRecordId:
                self.device.notifyExcepMessage(dataType, recordId, exceptRecordId)
            self.device.updateDeviceStatus(True)

        if dataType == 0x0006:
            log.info('打卡关锁: ' + content)
            if len(self.ownContentData) < 17:
                return
            cardNoList = ownContentData[0:4]
            cardNo = hexListToHexStr(cardNoList)
            cardPwdList = ownContentData[4:10]
            cardPwd = hexListToHexStr(cardPwdList)
            cardGroup = ownContentData[10]
            self.device.addOpenOrCloseRecord(None,timStr,cardNo)
            contentData = hexListToHexStrBlank(self.ownContentData)
            recordId = self.device.addUploadRecord(timStr,cardNo,'2',contentData,otherInfo)
            exceptRecordId = self.device.addUploadExceptRecord(recordId)
            if exceptRecordId:
                self.device.notifyExcepMessage(dataType, recordId, exceptRecordId)
            self.device.updateDeviceStatus(True)

        if dataType == 0x0008:
            log.info('设置锁的卡ID开锁权限: ' + content)
            pass
        if dataType == 0x0009:
            log.info('删除锁的卡ID开锁权限: ' + content)
            pass
        if dataType == 0x000a:
            log.info('上传锁没有关好的报警信息: ' + content)
            cardNoList = ownContentData[0:4]
            cardNo = hexListToHexStr(cardNoList)
            cardPwdList = ownContentData[4:10]
            cardPwd = hexListToHexStr(cardPwdList)
            cardGroup = ownContentData[10]
            contentData = hexListToHexStrBlank(self.ownContentData)
            recordId = self.device.addUploadRecord(timStr,cardNo,'3',contentData,otherInfo)
            exceptRecordId = self.device.addUploadExceptRecord(recordId)
            if exceptRecordId:
                self.device.notifyExcepMessage(dataType, recordId, exceptRecordId)
            self.device.updateDeviceStatus(True)

        if dataType == 0x000b:
            log.info('设置震动报警值: ' + content)
            pass
        if dataType == 0x000c:
            log.info('设置检测锁有没有关好的时间值: ' + content)
            pass
        if dataType == 0x000d:
            log.info('设置锁是否可用: ' + content)
            pass
        if dataType == 0x000e:
            log.info('设置低电压开锁电压值: ' + content)
            pass
        if dataType == 0x000f:
            log.info('设置定时心跳时间: ' + content)
            pass
        if dataType == 0x0010:
            log.info('上传锁内积水报警信息: ' + content)
            contentData = hexListToHexStrBlank(self.ownContentData)
            self.device.addUploadRecord(timStr, '', '6', contentData,otherInfo)
            self.device.updateDeviceStatus(True)
            pass
        if dataType == 0x0011:
            log.info(': ' + content)
            pass
        if dataType == 0x0012:
            log.info(': ' + content)
            pass
        if dataType == 0x0013:
            log.info('上传锁故障报警信息: ' + content)
            contentData = hexListToHexStrBlank(self.ownContentData)
            recordId = self.device.addUploadRecord(timStr, '', '7', contentData,otherInfo)
            exceptRecordId = self.device.addUploadExceptRecord(recordId)
            if exceptRecordId:
                self.device.notifyExcepMessage(dataType, recordId, exceptRecordId)
            self.device.updateDeviceStatus(True)
            pass
        if dataType == 0x0014:
            log.info('上传锁失联报警信息: ' + content)
            uploadValue = hexListToInt(ownContentData)
            contentData = hexListToHexStrBlank(self.ownContentData)
            if uploadValue == 1:
                log.info('锁上线: ' + content)
                self.device.updateDeviceStatus(True)
                self.device.addUploadRecord(timStr, '', '8', contentData)
            if uploadValue == 0:
                log.info('锁掉线: ' + content)
                self.device.updateDeviceStatus(False)
                recordId = self.device.addUploadRecord(timStr, '', '10', contentData)
                exceptRecordId = self.device.addUploadExceptRecord(recordId)
                if exceptRecordId:
                    self.device.notifyExcepMessage(dataType, recordId, exceptRecordId)
            pass
        if dataType == 0x0015:
            log.info('上传主机断电报警信息: ' + content)
            uploadValue = hexListToInt(ownContentData)
            self.device.updateDevicePowerStatus(uploadValue)

            contentData = hexListToHexStrBlank(self.ownContentData)
            recordId = self.device.addUploadRecord(timStr, '', '9', contentData,otherInfo)
            self.device.notifyExcepMessage(dataType, recordId,'')
            self.device.updateDeviceStatus(True)
            pass


        if dataType == 0x0017:
            log.info('读取主机工作信道: ' + content)
            if len(self.ownContentData) != 1:
                return
            channel = self.ownContentData[0]
            self.device.updateDeviceChannel(channel)

            # otherInfo = str(channel)

            contentData = hexListToHexStrBlank(self.ownContentData)
            self.device.addUploadRecord(timStr,'','17',contentData,otherInfo)
            self.needResponse = False


        if dataType == 0x0018:
            log.info('上传锁钩锁到位信息: ' + content)
            if len(ownContentData) < 11:
                return
            cardNoList = ownContentData[0:4]
            cardNo = hexListToHexStr(cardNoList)
            cardPwdList = ownContentData[4:10]
            cardPwd = hexListToHexStr(cardPwdList)
            cardGroup = ownContentData[10]
            self.device.addOpenOrCloseRecord(None,timStr,cardNo)
            contentData = hexListToHexStrBlank(self.ownContentData)
            self.device.addUploadRecord(timStr,cardNo,'18',contentData,otherInfo)
            self.device.updateDeviceStatus(True)

        if dataType == 0x0019:
            log.info('上传锁钩拔出信息: ' + content)
            if len(ownContentData) < 11:
                return
            cardNoList = ownContentData[0:4]
            cardNo = hexListToHexStr(cardNoList)
            cardPwdList = ownContentData[4:10]
            cardPwd = hexListToHexStr(cardPwdList)
            cardGroup = ownContentData[10]
            contentData = hexListToHexStrBlank(self.ownContentData)
            self.device.addUploadRecord(timStr,cardNo,'19',contentData,otherInfo)
            self.device.updateDeviceStatus(True)

        if dataType == 0x001a:
            log.info('上报锁电池电压值: ' + content)
            contentData = hexListToHexStrBlank(self.ownContentData)
            self.device.addUploadRecord(timStr, '', '1a', contentData,otherInfo)
            self.device.updateDeviceStatus(True)



    def handleTransaction(self):
        if self.parseContentData():
            self.device = Device(str(hexListToInt(self.deviceid)),str(hexListToInt(self.ownContentDeviceid)))
            isHas = self.device.hasDevice()
            if isHas:
                self.device.hasnotAndAddDeviceRecord()
                self.handleData()
                self.updateTerminalKeepaliveTime(self.device.terminal)
            else:
                #上传主机断电报警
                log.info('上传主机断电报警信息')
                dataType = self.ownContentDataType[0] * 256 + self.ownContentDataType[1]
                terminal = Terminal(str(hexListToInt(self.deviceid)))
                try:
                    tim = datetime(2000 + self.year, self.month, self.day, self.hour, self.minute, self.second)
                except:
                    tim = datetime.now()
                timStr = tim.strftime('%Y-%m-%d %H:%M:%S')

                if len(self.ownContentData) > 6:
                    uploadTim = self.parseUploadTim(self.ownContentData[0:6])
                    timStr = timStr if not uploadTim else uploadTim.strftime('%Y-%m-%d %H:%M:%S')

                if dataType == 0x0015:
                    ownContentData = self.ownContentData[6:]
                    uploadValue = hexListToInt(ownContentData)
                    terminal.updateTerminalPowerStatus(uploadValue)

                    contentData = hexListToHexStrBlank(self.ownContentData)
                    recordId = terminal.addUploadRecord(timStr, '', '9',contentData)
                    self.updateTerminalKeepaliveTime(terminal)
                    terminal.notifyExcepMessage(dataType, recordId)
                if dataType == 0x0017:
                    if len(self.ownContentData) != 1:
                        return
                    channel = self.ownContentData[0]
                    terminal.updateTerminalChannel(channel)

                    contentData = hexListToHexStrBlank(self.ownContentData)
                    terminal.addUploadRecord(timStr, '', '17', contentData)
                    self.needResponse = False


    def parseUploadTim(self, timList):
        '''
        根据上报的报文，解析报文中的时间
        :param timList: 
        :return: 
        '''
        if isinstance(timList, list) and len(timList) == 6:
            year = 2000 + timList[0]
            month = timList[1]
            day = timList[2]
            hour = timList[3]
            minute = timList[4]
            second = timList[5]
            try:
                return datetime(year, month, day, hour, minute, second)
            except Exception,e:
                return None
        return None

    def updateTerminalKeepaliveTime(self, terminal):
        """
        跟新数据库中记录的最新心跳时间
        """
        import time
        tim = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        terminal.updateTerminalKeepalive(tim)

    def updateToDoResult(self, isDevice=True):
        if self.device and isDevice and self.device.deviceId:
            data = self.device.getSendRecord(self.syncCount)
        else:
            terminal = Terminal(str(hexListToInt(self.deviceid)))
            data = terminal.getSendRecord(self.syncCount)
        if data and len(data) > 0:
            return data[0][0]
        return ''



class DistributeDataProtocol(BaseProtocol):
    """
    下发参数
    """

    def __init__(self):
        super(DistributeDataProtocol,self).__init__()
        self.packetType = 0x92
        self.backPacketType = 0x02
        self.source = SendSource.WEB_SERVER

        self.ownContentLength = [0x00, 0x00]
        self.ownContentDeviceType = [] #4bytes
        self.ownContentDeviceid = [0x00,0x00,0x00,0x00] #4bytes
        self.ownContentDataType = [0x00, 0x00]
        self.ownContentData = [] #n bytes

    def buildContentData(self,dataDict):
        dataTypeStr = dataDict.get('dataType','')
        dataTypeDict = {'6':0x06,'7':0x07,'8':0x08,'9':0x09,'10':0x0a,'11':0x0b,'12':0x0c,'13':0x0d,'14':0x0e,'15':0x0f,'16':0x16,'17':0x17}
        dataType = dataTypeDict.get(dataTypeStr,0)
        self.ownContentDeviceType = intToHexListWithLen(int(dataDict.get('deviceType','0')),4)
        self.ownContentDeviceid = intToHexListWithLen(int(dataDict.get('deviceId','0')),4)
        self.ownContentDataType = intToHexListWithLen(dataType,2)

        self.backSyncCount = int(dataDict.get('count',0) or 0) & 0xff
        self.syncCount = int(dataDict.get('count',0) or 0) & 0xff

        dataValue = int(dataDict.get('value','0') or 0)
        self.ownContentData = intToHexList(dataValue)
        oneLenType = [0x16]
        sixLenType = [0x06,0x07,0x0a,0x0c,0x0d,0x0e,0x0f]
        eightLenType = [0x09]
        twelveLenType = [0x08]
        if dataType in oneLenType:
            self.ownContentData = [int(dataValue)]
        if dataType in sixLenType:
            self.ownContentData = intToHexListWithLen(dataValue,6)
        if dataType in eightLenType:
            self.ownContentData = intToHexListWithLen(dataValue,8)
        if dataType in twelveLenType:
            self.ownContentData = intToHexListWithLen(dataValue,12)

        length = 10 + len(self.ownContentData)
        self.ownContentLength[0] = length >> 8
        self.ownContentLength[1] = length & 0xff

        self.backContentData.extend(self.ownContentLength)
        self.backContentData.extend(self.ownContentDeviceType)
        self.backContentData.extend(self.ownContentDeviceid)
        self.backContentData.extend(self.ownContentDataType)
        self.backContentData.extend(self.ownContentData)

    def buildPacket(self,dataDict):
        if dataDict:
            self.buildContentData(dataDict)
        return self.buildBackPacket()

    def parseContentData(self):
        if len(self.contentData) < 12:
            self.valid = False
            return False
        self.ownContentLength = self.contentData[0:2]
        length = self.getLength(self.ownContentLength)
        length -= 10
        self.ownContentDeviceType = self.contentData[2:2+4]
        self.ownContentDeviceid = self.contentData[6:6+4]
        self.ownContentDataType = self.contentData[10:10+2]
        self.ownContentData = self.contentData[12:12+length] if length > 0 else []
        if hexListToInt(self.ownContentDeviceid) == 0:
            return False
        return True


    def updateToDoResult(self):
        if self.parseContentData():
            device = Device(str(hexListToInt(self.deviceid)),str(hexListToInt(self.ownContentDeviceid)))
            data = device.getSendRecord(self.syncCount)
        else:
            terminal = Terminal(str(hexListToInt(self.deviceid)))
            data = terminal.getSendRecord(self.syncCount)
        if data and len(data) > 0:
            return data[0][0]
        return ''




class NotifyUpdateDeviceProtocol(BaseProtocol):
    """
    通知主机更新固件
    """

    def __init__(self):
        super(NotifyUpdateDeviceProtocol,self).__init__()
        self.packetType = 0x93
        self.backPacketType = 0x03
#        self.source = 'server'

    def buildPacket(self,dataDict):
        return self.buildBackPacket()



class DeviceUpdateProtocol(BaseProtocol):
    """
    """

    def __init__(self):
        super(DeviceUpdateProtocol,self).__init__()
        self.packetType = 0x03
        self.backPacketType = 0x93
        self.source = SendSource.HARDWARE_TERMINAL

    def buildBackPacket(self):
        self.backSyncCount = self.syncCount
        buf = self.readUpdateFile()
        if buf == None:
            raise Exception
        else:
            buf_num = []
            if len(buf) == 0:
                self.backContentData = []
            elif len(buf) == 1024:
                buf_num = buf
            elif len(buf) < 1024:
                buf = buf + '\xff' * (1024-len(buf))
            else:
                buf = buf[:1024]
        return super(DeviceUpdateProtocol, self).buildBackPacket()


    def getUpdateFilePath(self):
        """
        从数据中读取更新文件的路径
        """
        return ''

    def readUpdateFileIter(self):
        """
        """
        filePath = self.getUpdateFilePath()
        try:
            updateFile = open(filePath)
        except Exception,e:
            log.error('打开固件更新文件出错，请检查...')
            yield None
        try:
            yield updateFile.read(1024)
        except Exception,e:
            log.error('读取固件更新文件数据出错')
            yield None
        finally:
            updateFile.close()

    def readUpdateFile(self):
        """
        """
        filePath = self.getUpdateFilePath()
        try:
            updateFile = open(filePath)
        except Exception,e:
            log.error('打开固件更新文件出错，请检查...')
            return None
        try:
            updateFile.seek(self.syncCount * 1024)
            return updateFile.read(1024)
        except Exception,e:
            log.error('读取固件更新文件数据出错')
            return None
        finally:
            updateFile.close()





class ProtocolFactory(object):
    """
    协议工厂模式
    """

    def __init__(self):
        pass

    @classmethod
    def makeProtocol(cls, protocolType):
        if protocolType == 0x01:
            return KeepaliveProtocol()

        if protocolType == 0x02:
            return NormalDataProtocol()

        if protocolType == 0x03:
            return DeviceUpdateProtocol()

        if protocolType == 0x92:
            return DistributeDataProtocol()

        if protocolType == 0x93:
            return NotifyUpdateDeviceProtocol()

        if protocolType == 0x94:
            return AddNewLockProtocol()

        if protocolType == 0x95:
            return DeleteLockProtocol()

        return None


