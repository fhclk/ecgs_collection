#!/usr/bin/env python
#-*-coding:utf-8-*-

import uuid
from database.mysqlConnPool import MysqlConn
from datetime import datetime

from util import jPush
from util.util import log

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

mysqlConn = MysqlConn.getProcMysqlConn

class Terminal(object):
    '''
    主机终端
    '''

    def __init__(self,terminalId):
        self.terminalId = terminalId
        self.terminalRecordUUID = ''
        ter = self.queryTerminal()
        if ter:
            self.terminalUUID = ter[0][0]
        else:
#            self.terminalUUID = uuid.uuid1()
#            self.addTerminal()
            return
        terRd = self.queryTerminalRecord()
        if terRd:
            self.terminalRecordUUID = terRd[0][0]
        else:
            self.terminalRecordUUID = uuid.uuid1()
            self.addTerminalRecord()

        print mysqlConn(),'object'


    def addTerminal(self):
        sql = "insert into bus_equip (id,deleted,odr,equipCode,equipType,status,parent_equip_id) values('{0}',b'0',0,'{1}','1','2',Null)".format(self.terminalUUID,self.terminalId)
        return mysqlConn().insertData(sql)

    def queryTerminal(self):
        sql = "select id from bus_equip where equipCode='{0}' and deleted=0".format(self.terminalId)
        return mysqlConn().selectData(sql)

    def hasTerminal(self):
        if not self.queryTerminal():
            return False
        return True

    def hasnotAndAddTerminal(self):
        if not self.queryTerminal():
            return self.addTerminal()
        return True

    def addTerminalRecord(self):
        sql = "insert into bus_equip_status (id,deleted,odr,equipType,equip_id)" + \
                " values('{0}',b'0',0,'1','{1}')".format(self.terminalRecordUUID,self.terminalUUID)
        return mysqlConn().insertData(sql)

    def queryTerminalRecord(self):
        sql = "select id from bus_equip_status where equip_id='{0}' and deleted=0".format(self.terminalUUID)
        return mysqlConn().selectData(sql)

    def hasTerminalRecord(self):
        if not self.queryTerminalRecord():
            return False
        return True

    def hasnotAndAddTerminalRecord(self):
        if not self.queryTerminalRecord():
            return self.addTerminalRecord()
        return True

    def updateTerminalStatus(self,state):
        now = datetime.now()
        timStr = now.strftime('%Y-%m-%d %H:%M:%S')
        sta = '1' if state else '2'
        sql = "update bus_equip_status set status='{0}', last_date='{1}' where id='{2}'".format(sta, timStr, self.terminalRecordUUID)
        if not state:
            sql2 = "update bus_equip_status set status=(CASE status WHEN '1' THEN '3' WHEN '2' THEN '4' ELSE status END), last_date='{0}' where equip_id in (select id from bus_equip where parent_equip_id = '{1}')".format(
                timStr, self.terminalUUID)
            return mysqlConn().updateData(sql) and mysqlConn().updateData(sql2)
        else:
            sql2 = "update bus_equip_status set status=(CASE status WHEN '3' THEN '1' WHEN '4' THEN '2' ELSE status END), last_date='{0}' where equip_id in (select id from bus_equip where parent_equip_id = '{1}')".format(
                timStr, self.terminalUUID)
            return mysqlConn().updateData(sql) and mysqlConn().updateData(sql2)
        

    def updateTerminalV(self,v):
        sql = "update bus_equip_status set equipV='{0}' where id='{1}'".format(v,self.terminalRecordUUID)
        return mysqlConn().updateData(sql)

    def updateTerminalKeepalive(self,datetime):
        sql = "update bus_equip_status set last_date='{0}' where id='{1}'".format(datetime,self.terminalRecordUUID)
        return mysqlConn().updateData(sql)

    def isTerminalTimeout(self,second):
        sql = "select last_date from bus_equip_status where equip_id='{0}'".format(self.terminalUUID)
        data = mysqlConn().selectData(sql)
        if data and len(data) > 0:
            s = data[0][0]
            if isinstance(s,str):
                lastDate = datetime.strptime(s,'%Y-%m-%d %H:%M:%S')
            else:
                lastDate = s
            now = datetime.now()
            nt = now - lastDate
            if nt.total_seconds() > second:
                return True
            else:
                return False
        return True

    def getSendRecord(self, syncCount):
        sql = "select id from bus_send_commond_record where equip1_id='{0}' and code%256={1} order by -code".format(self.terminalUUID, syncCount)
        return mysqlConn().selectData(sql)

    @classmethod
    def getOnlineTerminals(cls):
        print mysqlConn()
        sql = "select id,last_date,equip_id from bus_equip_status where equipType='1' and status='1'"
        return mysqlConn().selectData(sql)

    @classmethod
    def getOfflineTerminals(cls):
        sql = "select id,last_date,equip_id from bus_equip_status where equipType='1' and status='2'"
        return mysqlConn().selectData(sql)

    @classmethod
    def updateTerminalOfflineStatusById(cls,terminalUUId):
        now = datetime.now()
        timStr = now.strftime('%Y-%m-%d %H:%M:%S')
        sql = "update bus_equip_status set status='2', last_date='{0}' where equip_id='{1}'".format(timStr,terminalUUId)
        sql2 = "update bus_equip_status set status=(CASE status WHEN '1' THEN '3' WHEN '2' THEN '4' ELSE status END), last_date='{0}' where equip_id in (select id from bus_equip where parent_equip_id = '{1}')".format(
            timStr, terminalUUId)
        return mysqlConn().updateData(sql) and mysqlConn().updateData(sql2)

    @classmethod
    def updateTerminalOfflineStatus(cls, terminalUUIdList):
        if len(terminalUUIdList) == 1:
            terminalUUIdList.append('')
        terminalUUIdTuple = tuple(terminalUUIdList)
        now = datetime.now()
        timStr = now.strftime('%Y-%m-%d %H:%M:%S')
        sql = "update bus_equip_status set status='2', last_date='{0}' where equip_id in {1}".format(timStr, terminalUUIdTuple)
        sql2 = "update bus_equip_status set status=(CASE status WHEN '1' THEN '3' WHEN '2' THEN '4' ELSE status END), last_date='{0}' where equip_id in (select id from bus_equip where parent_equip_id in {1})".format(
            timStr, terminalUUIdTuple)
        return mysqlConn().updateData(sql) and mysqlConn().updateData(sql2)

    @classmethod
    def updateTerminalDeviceOfflineStatusById(cls, terminalUUId):
        now = datetime.now()
        timStr = now.strftime('%Y-%m-%d %H:%M:%S')
        sql2 = "update bus_equip_status set status=(CASE status WHEN '1' THEN '3' WHEN '2' THEN '4' ELSE status END), last_date='{0}' where equip_id in (select id from bus_equip where parent_equip_id = '{1}')".format(
            timStr, terminalUUId)
        return mysqlConn().updateData(sql2)

    @classmethod
    def updateTerminalDeviceOfflineStatus(cls):
        now = datetime.now()
        timStr = now.strftime('%Y-%m-%d %H:%M:%S')
        sql2 = "update bus_equip_status set status=(CASE status WHEN '1' THEN '3' WHEN '2' THEN '4' ELSE status END), last_date='{0}' where equip_id in (select c.id from (select a.id from bus_equip a, bus_equip_status b where b.status='2' and a.parent_equip_id = b.equip_id) c )".format(
            timStr)
        return mysqlConn().updateData(sql2)

    def addUploadRecord(self,uploadTim,cardNo,infoType,content):
        '''
        添加上传报文
        :param uploadTim: 
        :param cardNo: 
        :param infoType: 
        :param content: 
        :return: 
        '''
        if self.hasUploadRecord(uploadTim, infoType):
            return
        recordId = uuid.uuid1()
        cardId = None if not cardNo else self.getCardIdByCardNo(cardNo)
        cardId = 'NULL' if cardId is None else "'{}'".format(cardId)
        sql = "insert into bus_upload_info_record (id,upload_date,card_id,equip1_id,equip2_id,infoType,infoContent,deleted,odr) " + \
                "values('{0}','{1}',{2},'{3}','{4}','{5}','{6}',b'0',0)".format(recordId, uploadTim, cardId, self.terminalUUID,self.terminalUUID,infoType,content)
        if mysqlConn().insertData(sql):
            return recordId

    def hasUploadRecord(self, uploadTim, infoType):
        sql = "select * from bus_upload_info_record where upload_date='{0}' and infoType='{1}'".format(uploadTim, infoType)
        data = mysqlConn().selectData(sql)
        if data and len(data) > 0:
            return True
        return False

    @classmethod
    def getDistributeData(cls, recordId):
        '''
        根据下发参数表id获取下发参数
        :param recordId: 
        :return: 
        '''
        sql = "select t1.commondType,t1.card_id,t1.code,t1.commondParam,t2.equipCode,'0' from bus_send_commond_record t1,bus_equip t2 where t1.id='{0}' and t1.equip1_id=t2.id".format(
            recordId)
        data = mysqlConn().selectData(sql)
        return data


    @classmethod
    def setAllTerminalOffline(cls):
        now = datetime.now()
        timStr = now.strftime('%Y-%m-%d %H:%M:%S')
        sql2 = "update bus_equip_status set status='2', last_date='{0}' where status<>'2' and equip_id in (select id from bus_equip where equipType = '1')".format(timStr)
        return mysqlConn().updateData(sql2)

    def notifyExcepMessage(self, dataType, uploadRecordId):
        print '异常推送', dataType, uploadRecordId
        if not dataType or not uploadRecordId:
            return

        dataMsg = {
            0x0015:u'断电'
        }
        tags = []
        if dataType != 0x0015:
            return
        users = Device.getCorrelationUsersOfTerminal(uploadRecordId)
        alert = dataMsg.get(dataType, '') + u' 主机编号:' + ('%010x' % int(self.terminalId))
        for user in users:
            tags.append(user['userId'])
        try:
            jPush.tags(tags, alert, {'mtype': '3', 'terminalNo': self.terminalId})
        except Exception,e:
            log.error('极光推送失败:'+str(e))
            pass

    def updateTerminalPowerStatus(self,powerStatus):
        sql = "update bus_equip set powerStatus='{0}' where id='{1}'".format(powerStatus, self.terminalUUID)
        return mysqlConn().updateData(sql)

    def updateTerminalChannel(self,channel):
        if not channel:
            return
        sql = "update bus_equip set channel='{0}' where id='{1}'".format(channel, self.terminalUUID)
        return mysqlConn().updateData(sql)




class Device(object):
    '''
    锁
    '''

    def __init__(self,terminalId,deviceId):
        self.terminalId = terminalId
        self.terminal = Terminal(terminalId)
        self.deviceId = deviceId
        super(Device,self).__init__()
        self.deviceUUID = ''
        self.deviceRecordUUID = ''
        ter = self.queryDevice()
        if ter:
            self.deviceUUID = ter[0][0]
        else:
#            self.deviceUUID = uuid.uuid1()
#            self.addDevice()
            return
        devRd = self.queryDeviceRecord()
        if devRd:
            self.deviceRecordUUID = devRd[0][0]
        else:
            self.deviceRecordUUID = uuid.uuid1()
            self.addDeviceRecord()


    def addDevice(self):
        sql = "insert into bus_equip (id,deleted,odr,equipCode,equipType,status,parent_equip_id) values('{0}',b'0',0,'{1}','2','2','{2}')".format(self.deviceUUID,self.deviceId,self.terminal.terminalUUID)
        return mysqlConn().insertData(sql)

    def addDeviceRecord(self):
        sql = "insert into bus_equip_status (id,deleted,odr,equipType,equip_id)" + \
                " values('{0}',b'0',0,'2','{1}')".format(self.deviceRecordUUID,self.deviceUUID)
        return mysqlConn().insertData(sql)

    def queryDeviceRecord(self):
        sql = "select id from bus_equip_status where equip_id='{0}' and deleted=0".format(self.deviceUUID)
        return mysqlConn().selectData(sql)

    def hasDeviceRecord(self):
        if not self.queryDeviceRecord():
            return False
        return True

    def hasnotAndAddDeviceRecord(self):
        if not self.queryDeviceRecord():
            return self.addDeviceRecord()
        return True

    def updateDeviceStatus(self,state):
        now = datetime.now()
        timStr = now.strftime('%Y-%m-%d %H:%M:%S')
        sta = '1' if state else '2'
        sql = "update bus_equip_status set status='{0}', last_date='{1}' where id='{2}'".format(sta,timStr,self.deviceRecordUUID)
        return mysqlConn().updateData(sql)

    def updateDeviceV(self,v):
        sql = "update bus_equip_status set equipV='{0}' where id='{1}'".format(v,self.deviceRecordUUID)
        return mysqlConn().updateData(sql)

    def updateDeviceVStatus(self,v):
        settingVStr = self.getDeviceSettingV()
        try:
            settingV = float(settingVStr)
        except Exception,e:
            return False
        if settingV <= v:
            status = '1'
        else:
            status = '2'
        sql = "update bus_equip_status set vStatus='{0}' where id='{1}'".format(status,self.deviceRecordUUID)
        return mysqlConn().updateData(sql)

    def getDeviceSettingV(self):
        sql = "select id,commondParam from bus_send_commond_record where equip1_id='{0}' and equip2_id='{1}' and commondType=9 and result=1 order by -send_date".format(self.terminal.terminalUUID,self.deviceUUID)
        data = mysqlConn().selectData(sql)
        if data and len(data) > 0:
            return data[0][-1]
        return '0'

    def updateDeviceKeepalive(self,datetime):
        sql = "update bus_equip_status set last_date='{0}' where id='{1}'".format(datetime,self.deviceRecordUUID)
        return mysqlConn().updateData(sql)

    def queryDevice(self):
        sql = "select id from bus_equip where equipCode='{0}' and deleted=0".format(self.deviceId)
        return mysqlConn().selectData(sql)

    def hasDevice(self):
        if not self.queryDevice():
            return False
        return True

    def hasnotAndAddDevice(self):
        if not self.queryDevice():
            return self.addDevice()
        return True


    def addOpenOrCloseRecord(self,openTim, closeTim, cardNo):
        cardId = None if not cardNo else self.getCardIdByCardNo(cardNo)
        cardId = 'NULL' if cardId is None else cardId
        if openTim:
            sql = "update bus_equip_oc_record set open_date='{0}' where equip_id='{1}'".format(openTim, self.deviceUUID)
            if not mysqlConn().updateData(sql):
                sql1 = "insert into bus_equip_oc_record (id,open_date,card_id,equip_id) " + \
                        " values('{0}','{1}','{2}','{3}')".format(uuid.uuid1(),openTim,cardId,self.deviceUUID)
                mysqlConn().insertData(sql1)
        if closeTim:
            sql = "update bus_equip_oc_record set close_date='{0}' where equip_id='{1}'".format(closeTim, self.deviceUUID)
            if not mysqlConn().updateData(sql):
                sql1 = "insert into bus_equip_oc_record (id,close_date,card_id,equip_id) " + \
                        " values('{0}','{1}','{2}','{3}')".format(uuid.uuid1(),closeTim,cardId,self.deviceUUID)
                mysqlConn().insertData(sql1)


    def addUploadRecord(self,uploadTim,cardNo,infoType,content,otherInfo=None):
        #排除重复的报文
        # if self.hasUploadRecord(uploadTim, infoType):
        #     return
        recordId = uuid.uuid1()
        cardId = None if not cardNo else self.getCardIdByCardNo(cardNo)
        cardId = 'NULL' if cardId is None else "'{}'".format(cardId)
        other_info = 'NULL' if not otherInfo else otherInfo
        sql = "insert into bus_upload_info_record (id,upload_date,card_id,equip1_id,equip2_id,infoType,infoContent,deleted,odr,otherInfo) " + \
                "values('{0}','{1}',{2},'{3}','{4}','{5}','{6}',b'0',0,'{7}')".format(recordId, uploadTim, cardId, self.terminal.terminalUUID,self.deviceUUID,infoType,content,other_info)
        if mysqlConn().insertData(sql):
            return recordId

    def addUploadExceptRecord(self, uploadRecordId):
        '''
        添加异常记录
        :param uploadRecordId: 数据库表里上传的记录id
        :return: 
        '''
        if not uploadRecordId:
            return
        record = uuid.uuid1()
        sql = "INSERT into bus_equip_question(id, f_equip_id, f_upload_info_record_id,status,deleted) VALUES('{0}','{1}','{2}','1',b'0')".format(record,self.deviceUUID,uploadRecordId)
        if mysqlConn().insertData(sql):
            return record

    def hasUploadRecord(self, uploadTim, infoType):
        sql = "select * from bus_upload_info_record where upload_date='{0}' and infoType='{1}'".format(uploadTim, infoType)
        data = mysqlConn().selectData(sql)
        if data and len(data) > 0:
            return True
        return False

    def addSendRecord(self,sendTim,cardId,infoType):
        sql = "insert into bus_send_commond_record (id,send_date,card_id,equip1_id,equip2_id,command_type) " + \
                "values('{0}','{1}','{2}','{3}','{4}','{5}')".format(uuid.uuid1(), sendTim, cardId, self.terminal.terminalUUID,self.deviceUUID,infoType)
        mysqlConn().insertData(sql)

    def updateSendRecordResult(self,result):
        sql = "select id from bus_send_commond_record where equip1_id='{0}' and quip2_id='{1}' order by send_date".format(self.terminal.terminalUUID,self.deviceUUID)
        data = mysqlConn().selectData(sql)
        if data and len(data)>0:
            lastRecordId = data[0][0]
            res = '1' if result else '2'
            sql1 = "update bus_send_commond_record set result='{0}' where id='{1}'".format(res,lastRecordId)
            mysqlConn().updateData(sql1)

    def getSendRecord(self, syncCount):
        sql = "select id from bus_send_commond_record where equip1_id='{0}' and equip2_id='{1}' and code%256={2} order by -code".format(self.terminal.terminalUUID, self.deviceUUID,syncCount)
        return mysqlConn().selectData(sql)


    @classmethod
    def getOnlineDevices(cls):
        sql = "select id,last_date from bus_equip_status where equipType='2' and status='1'"
        return mysqlConn().selectData(sql)

    @classmethod
    def getOnlineDevices2(cls):
        sql = "select t1.id,t1.last_date,t2.HeartBeatTime from bus_equip_status t1, bus_equip t2 where t1.equipType='2' and t1.status='1' and t1.equip_id=t2.id"
        return mysqlConn().selectData(sql)

    @classmethod
    def updateDeviceOfflineStatusById(cls,deviceUUId):
        now = datetime.now()
        timStr = now.strftime('%Y-%m-%d %H:%M:%S')
        sql = "update bus_equip_status set status='2', last_date='{0}' where id='{1}'".format(timStr,deviceUUId)
        mysqlConn().updateData(sql)

    @classmethod
    def getCardPwdByCardId(cls,cardId):
        if not cardId:
            return None
        sql = "select card_pwd, card_code from bus_card where id='{0}'".format(cardId)
        return mysqlConn().selectData(sql)

    def getCardRecordIdByCardPwd(self,cardPwd):
        try:
            card_pwd = "{:x}".format(int(cardPwd))
        except Exception,e:
            return None
        sql = "select id from bus_card where card_pwd={0}".format(card_pwd)
        data = mysqlConn().selectData(sql)
        if data and len(data) > 0:
            return data[0][0]
        return None

    def getCardIdByCardNo(self, cardNo):
        if cardNo:
            sql = "select id from bus_card where card_code='{0}'".format(cardNo)
            data = mysqlConn().selectData(sql)
            if data and len(data) > 0:
                return data[0][0]
            return None

    def notifyExcepMessage(self, dataType, uploadRecordId, exceptRecordId=''):
        print '异常推送', dataType, uploadRecordId
        if not dataType or not uploadRecordId:
            return

        dataMsg = {
            0x0002:u'震动报警',
            0x000a:u'锁没有关好',
            0x0010:u'锁内积水',
            0x0013:u'锁故障报警',
            0x0014:u'锁失联',
            0x0015:u'断电',
            0x0005:u'开锁',
            0x0006:u'关锁'
        }
        tags = []
        if dataType == 0x0005 or dataType == 0x0006:
            users = Device.getCorrelationUsers(uploadRecordId)
            alert = dataMsg.get(dataType, '') + u' %s [%s]' % (Device.getUploadDatetime(uploadRecordId) ,Device.getFacilityInfo(self.deviceId))
        elif dataType != 0x0015:
            users = Device.getCorrelationUsers(uploadRecordId)
            alert = dataMsg.get(dataType, '') + u', 请立即前往处理 [%s]' % Device.getFacilityInfo(self.deviceId)
        else:
            users = Device.getCorrelationUsersOfTerminal(uploadRecordId)
            alert = dataMsg.get(dataType, '') + u' 主机编号:' + ('%010x' % int(self.terminal.terminalId))
        for user in users:
            tags.append(user['userId'])
        exceptRecordId = '%s' % exceptRecordId
        try:
            if dataType == 0x0005 or dataType == 0x0006:
                jPush.tags(tags, alert, {'mtype': '3'})
            elif dataType != 0x0015:
                jPush.tags(tags, alert, {'mtype':'3','lockNO':self.deviceId, 'exceptRecordId':exceptRecordId})
            else:
                jPush.tags(tags, alert, {'mtype': '3', 'terminalNo': self.terminal.terminalId})
        except Exception,e:
            log.error('极光推送失败:'+str(e))
            pass

    @staticmethod
    def getUploadDatetime(uploadRecordId):
        sql = "select upload_date from bus_upload_info_record where id='{0}'".format(uploadRecordId)
        data = mysqlConn().selectData(sql)
        if data and len(data) > 0:
            return data[0][0]
        return ''

    @staticmethod
    def getFacilityInfo(deviceId):
        sql = '''
        SELECT CONCAT('设施编号:',boxNumer,'  供水栋数：',several) as info FROM bus_waterbox WHERE f_equip_id IN ( SELECT id FROM bus_equip WHERE equipCode = '%s' )
        ''' % deviceId
        data = mysqlConn().selectData(sql)
        if data and len(data) > 0:
            return data[0][0]
        return ''


    @staticmethod
    def getCorrelationUsers(uploadRecordId):
        print 'getCorrelationUsers'
        sql1 = '''
        SELECT
	        a.user_id
        FROM
	        bus_waterbox a
        LEFT JOIN bus_equip b ON a.id = b.f_waterbox_id
        LEFT JOIN bus_upload_info_record c ON b.id = c.equip2_id
        WHERE
	        c.id = '%s'
        ''' % uploadRecordId

        sql2 = '''
        SELECT
	        a.f_hous_manager_id
        FROM
	        bus_hous_dictionary a
        LEFT JOIN bus_waterbox b ON a.id = b.hous_id
        LEFT JOIN bus_equip c ON b.id = c.f_waterbox_id
        LEFT JOIN bus_upload_info_record d ON c.id = d.equip2_id
        WHERE
	        d.id = '%s'
        ''' % uploadRecordId

        data = mysqlConn().selectData(sql1)
        if data and len(data) == 0:
            data = mysqlConn().selectData(sql2)
        users = []
        for item in data:
            user = {}
            user['userId'] = item[0]
            users.append(user)
        return users

    @staticmethod
    def getCorrelationUsersOfTerminal(uploadRecordId):
        sql = '''
        SELECT
	        a.f_hous_manager_id
        FROM
	        bus_hous_dictionary a
        LEFT JOIN bus_waterbox b ON a.id = b.hous_id
        LEFT JOIN bus_equip c ON b.id = c.f_waterbox_id
        LEFT JOIN bus_upload_info_record d ON c.id = d.equip1_id
        WHERE
	        d.id = '%s'
        ''' % uploadRecordId
        data = mysqlConn().selectData(sql)
        users = []
        for item in data:
            user = {}
            user['userId'] = item[0]
            users.append(user)
        return users

    @classmethod
    def setAllDeviceOffline(cls):
        now = datetime.now()
        timStr = now.strftime('%Y-%m-%d %H:%M:%S')
        sql2 = "update bus_equip_status set status='2', last_date='{0}' where status<>'2' and equip_id in (select id from bus_equip where equipType = '2')".format(
            timStr)
        return mysqlConn().updateData(sql2)

    def isOffline(self):
        sql = "select * from bus_equip_status where status='2' and id='{0}'".format(self.deviceRecordUUID)
        data = mysqlConn().selectData(sql)
        if data and len(data):
            return True
        return False

    def updateDeviceChannel(self,channel):
        if not channel:
            return
        sql = "update bus_equip set channel='{0}' where id='{1}'".format(channel, self.deviceUUID)
        return mysqlConn().updateData(sql)

    @classmethod
    def getDistributeData(cls, recordId):
        '''
        根据下发参数表id获取下发参数
        :param recordId: 
        :return: 
        '''
        sql = "select t1.commondType,t1.card_id,t1.code,t1.commondParam,t2.equipCode,t3.equipCode from bus_send_commond_record t1,bus_equip t2, bus_equip t3 where t1.id='{0}' and t1.equip1_id=t2.id and t1.equip2_id=t3.id".format(
            recordId)
        data = mysqlConn().selectData(sql)
        return data


    def getCheckUserId(self, cardCode, cardPwd):
        sql = '''
        SELECT
	        user_id
        FROM
	        bus_card
        WHERE
	        deleted = 0
        AND card_code = '%s'
        AND card_pwd = '%s'
        ''' % (cardCode, cardPwd)
        data = mysqlConn().selectData(sql)
        if data and len(data) > 0:
            return data[0][0]
        return None

    def getTeneCompanyId(self, userId):
        '''
        根据用户id获取物管公司id
        :param userId: 
        :return: 
        '''
        sql = '''
        SELECT
	        bean_id
        FROM
	        bus_org_bean_link
        WHERE
	        deleted = 0
        AND org_id IN (
	        SELECT
		        dept_id
	        FROM
		        sys_user
	        WHERE
		        id = '%s'
        )
        ''' % userId
        data = mysqlConn().selectData(sql)
        if data and len(data) > 0:
            return data[0][0]
        return None

    def getWaterBoxId(self, userId):
        '''
        根据用户id获取关联的设施id
        :param userId: 
        :return: 
        '''
        sql = '''
        SELECT
	        id
        FROM
	        bus_waterbox
        WHERE
	        deleted = 0
        AND user_id = '%s';
        ''' % userId
        data = mysqlConn().selectData(sql)
        if data and len(data) > 0:
            return data[0][0]
        return None

    def addDailyCheck(self, timStr, teneCompId, userId, waterBoxId):
        sql = '''
        INSERT INTO bus_daily_check (
	        id,
	        deleted,
	        odr,
	        check_date,
	        content,
	        exceptionFlag,
	        exceptionState,
	        isOpenlock,
	        openLockTime,
	        property_company_id,
	        user_id,
	        waterbox_id,
	        conductor_flag,
	        conductor_state,
	        conductor_user_id
        )
        VALUES
	    (
		    '%s',-- UUID
		    b'0',-- 默认0
		    '0',-- 默认0
		    '%s', -- 报文时间
		    NULL,-- 不用填
		    b'0',-- 默认0
		    NULL,-- 不用填
		    b'0',-- 默认0
		    '0',-- 默认0
		    '%s',-- 物业公司id
		    '%s',-- 巡检人id
		    '%s',-- 巡检设施id
		    b'0',-- 默认0
		    NULL,-- 不用填
		    NULL -- 不用填
	    )
        ''' % (uuid.uuid1(), timStr, teneCompId, userId, waterBoxId)
        mysqlConn().insertData(sql)


    def addDailyCheckReport(self, timStr, cardCode, cardPwd):
        '''
        添加巡检记录
        :param timStr: 
        :param cardCode: 
        :param cardPwd: 
        :return: 
        '''
        userId = self.getCheckUserId(cardCode, cardPwd)
        teneCompId = None
        waterBoxId = None
        if userId:
            teneCompId = self.getTeneCompanyId(userId)

        waterBoxId = self.getWaterBoxIdOfDevice()
        waterBoxId = waterBoxId if waterBoxId is not None else 'NULL'
        if userId and teneCompId and waterBoxId:
            self.addDailyCheck(timStr, teneCompId, userId, waterBoxId)

    def updateDevicePowerStatus(self,powerStatus):
        sql = "update bus_equip set powerStatus='{0}' where id='{1}'".format(powerStatus, self.deviceUUID)
        return mysqlConn().updateData(sql)

    def getWaterBoxIdOfDevice(self):
        '''
        根据用户id获取设施关联的设施id
        :return: 
        '''
        sql = '''select f_waterbox_id from bus_equip where id='%s' ''' % self.deviceUUID
        data = mysqlConn().selectData(sql)
        if data and len(data) > 0:
            return data[0][0]
        return None
