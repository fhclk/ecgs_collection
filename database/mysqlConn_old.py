#!/usr/bin/env python
#-*-coding:utf-8-*-


import MySQLdb
import os
import sys
from util.util import log, readconf
import multiprocessing

class MysqlConn(object):
    """
    """

    mysqlConner = None

    def __init__(self,conf):
        self.serverAddr = conf.get('mysqlServerAddr'.lower(),'127.0.0.1')
        self.serverPort = int(conf.get('mysqlServerPort'.lower(),'3306'))
        self.serverUser = conf.get('mysqlServerUser'.lower(),'root')
        self.serverPwd = conf.get('mysqlServerPassword'.lower(),'root')
        self.database = conf.get('mysqlDatabaseName'.lower(),'ecgs')
        self.lock = multiprocessing.Lock()


    def initDb(self):
        try:
            self.conn = MySQLdb.connect(host=self.serverAddr,
                    port=self.serverPort,
                    user=self.serverUser,
                    passwd=self.serverPwd,
                    db=self.database)
        except MySQLdb.MySQLError,e:
            log.error('连接mysql数据库失败，请检查，并重试')
            sys.exit(0)

    def insertData(self,sql):
        result = True
        self.lock.acquire()
        try:
            cur = self.conn.cursor()
            cur.execute(sql)
        except MySQLdb.MySQLError,e:
            log.error('向数据库写数据失败:' + sql + ".error:" + str(e))
            result = False
        finally:
            cur.close()
            self.conn.commit()
            self.lock.release()
        if result:
            log.debug('向数据库写数据成功:' + sql )
        return result

    def updateData(self,sql):
        result = True
        self.lock.acquire()
        try:
            cur = self.conn.cursor()
            cur.execute(sql)
        except MySQLdb.MySQLError,e:
            log.error('向数据库更新数据失败:' + sql + ".error:" + str(e))
            result = False
        except Exception,e:
            log.error('向数据库更新数据失败:' + sql + ".error:" + str(e))
            result = False
        finally:
            cur.close()
            self.conn.commit()
            self.lock.release()
        if result:
            log.debug('向数据库更新数据成功:' + sql )
        return result

    def deleteData(self,sql):
        result = True
        self.lock.acquire()
        try:
            cur = self.conn.cursor()
            cur.execute(sql)
        except MySQLdb.MySQLError,e:
            log.error('向数据库删除数据失败:' + sql + ".error:" + str(e))
            result = False
        finally:
            cur.close()
            self.conn.commit()
            self.lock.release()
        if result:
            log.debug('向数据库删除数据成功:' + sql )
        return result

    def selectData(self,sql):
        self.lock.acquire()
        try:
            cur = self.conn.cursor()
            num = cur.execute(sql)
            data = cur.fetchmany(num)
        except MySQLdb.MySQLError,e:
            log.error('查询数据失败:' + sql + ".error:" + str(e))
            data = []
        except Exception,e:
            log.error('查询数据失败:' + sql + ".error:" + str(e))
            data = []
        finally:
            # cur.close()
            # self.conn.commit()
            self.lock.release()
        log.debug('查询数据:' + sql + '>>>' + str(data))
        return data


    def reconnectDB(self):
        if self.conn:
            try:
                self.conn.close()
            except Exception, e:
                log.error('关闭数据库连接失败' + str(e))
        try:
            self.conn = MySQLdb.connect(host=self.serverAddr,
                    port=self.serverPort,
                    user=self.serverUser,
                    passwd=self.serverPwd,
                    db=self.database)
            log.info('重连mysql数据库成功')
        except MySQLdb.MySQLError,e:
            log.error('重连mysql数据库失败')


    def __del__(self):
        self.conn.close()

    @staticmethod
    def getMysqlConn(conf):
        if MysqlConn.mysqlConner is not None:
            return MysqlConn.mysqlConner
        MysqlConn.mysqlConner = MysqlConn(conf)
        MysqlConn.mysqlConner.initDb()
        return MysqlConn.mysqlConner



# mysqlConn = MysqlConn.getMysqlConn(readconf('config.conf','mysql'))

from bak_mysqlConnPool_b import mysqlConn
mysqlConn = mysqlConn
