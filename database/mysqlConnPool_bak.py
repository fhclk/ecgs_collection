#!/usr/bin/env python
#-*-coding:utf-8-*-

import MySQLdb
from DBUtils.PooledDB import PooledDB
from util.util import log, readconf
import multiprocessing

class MysqlConn(object):
    """
    """

    _pool = None
    _lock = None

    def __init__(self,conf):
        self._serverAddr = conf.get('mysqlServerAddr'.lower(),'127.0.0.1')
        self._serverPort = int(conf.get('mysqlServerPort'.lower(),'3306'))
        self._serverUser = conf.get('mysqlServerUser'.lower(),'root')
        self._serverPwd = conf.get('mysqlServerPassword'.lower(),'root')
        self._database = conf.get('mysqlDatabaseName'.lower(),'ecgs')
        # self._lock = multiprocessing.Lock()
        self.initDb()


    def initDb(self):
        # self._lock.acquire()
        try:
            if MysqlConn._pool is None:
                MysqlConn._pool = PooledDB(creator=MySQLdb, mincached=1, maxcached=20,
                                      host=self._serverAddr, port=self._serverPort, user=self._serverUser,
                                      passwd=self._serverPwd,
                                      db=self._database, use_unicode=False, charset='utf8')
        except Exception,e:
            log.error('初始化数据库失败，请检查，并重试')
        # self._lock.release()

    def connectDb(self):
        result = False
        # self._lock.acquire()
        try:
            self._conn = MysqlConn._pool.connection(False)
            self._cursor = self._conn.cursor()
            result = True
        except MySQLdb.MySQLError,e:
            log.error('连接mysql数据库失败，请检查，并重试')
            result = False
        # self._lock.release()
        return result

    def testConnection(self):
        return self.connectDb()

    def insertData(self,sql):
        result = True
        # self._lock.acquire()
        try:
            self._cursor.execute(sql)
            self._conn.commit()
        except MySQLdb.OperationalError,e:
            log.error('向数据库写数据失败:' + sql + ".error:" + str(e))
            self.reconnectDB()
            pass
        except MySQLdb.MySQLError,e:
            log.error('向数据库写数据失败:' + sql + ".error:" + str(e))
            result = False
        # self._lock.release()
        if result:
            log.debug('向数据库写数据成功:' + sql )
        return result

    def updateData(self,sql):
        result = True
        # self._lock.acquire()
        # print 'updateData - self._lock.acquire()'
        try:
            self._cursor.execute(sql)
            self._conn.commit()
        except MySQLdb.OperationalError,e:
            log.error('向数据库更新数据失败:' + sql + ".error:" + str(e))
            self.reconnectDB()
            pass
        except MySQLdb.MySQLError,e:
            log.error('向数据库更新数据失败:' + sql + ".error:" + str(e))
            result = False
        except Exception,e:
            log.error('向数据库更新数据失败:' + sql + ".error:" + str(e))
            result = False
        # self._lock.release()
        # print 'updateData - self._lock.release()'
        if result:
            log.debug('向数据库更新数据成功:' + sql )
        return result

    def deleteData(self,sql):
        result = True
        # self._lock.acquire()
        # print 'self._lock.acquire()'
        try:
            self._cursor.execute(sql)
            self._conn.commit()
        except MySQLdb.OperationalError,e:
            log.error('向数据库删除数据失败:' + sql + ".error:" + str(e))
            self.reconnectDB()
            pass
        except MySQLdb.MySQLError,e:
            log.error('向数据库删除数据失败:' + sql + ".error:" + str(e))
            result = False
        # self._lock.release()
        # print 'self._lock.release()'
        if result:
            log.debug('向数据库删除数据成功:' + sql )
        return result

    def selectData(self,sql):
        # self._lock.acquire()
        # print 'self._lock.acquire()', multiprocessing.current_process().name, self
        try:
            num = self._cursor.execute(sql)
            data = self._cursor.fetchmany(num)
        except MySQLdb.OperationalError,e:
            log.error('查询数据失败:' + sql + ".error:" + str(e))
            self.reconnectDB()
            pass
        except MySQLdb.MySQLError,e:
            log.error('查询数据失败:' + sql + ".error:" + str(e))
            data = []
        except Exception,e:
            log.error('查询数据失败:' + sql + ".error:" + str(e))
            data = []
        # self._lock.release()
        # print 'self._lock.release()', multiprocessing.current_process().name, self._conn
        log.debug('查询数据:' + sql + '>>>' + str(data))
        return data[:]


    def reconnectDB(self):
        if self.conn:
            try:
                self._cursor.close()
                self._conn.close()
            except Exception, e:
                log.error('关闭数据库连接失败' + str(e))
        try:
            self._conn = self._pool.connection(False)
            self._cursor = self._conn.cursor()
            log.info('重连mysql数据库成功')
        except MySQLdb.MySQLError,e:
            log.error('重连mysql数据库失败')


    def __del__(self):
        # self._lock.acquire()
        self._cursor.close()
        self._conn.close()
        # self._lock.release()

    @staticmethod
    def getMysqlConn():
        mysqlConner = MysqlConn(readconf('config.conf','mysql'))
        mysqlConner.connectDb()
        return mysqlConner


mysqlConn = MysqlConn.getMysqlConn()

