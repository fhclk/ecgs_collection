#!/usr/bin/env python
#-*-coding:utf-8-*-

import MySQLdb
from DBUtils.PooledDB import PooledDB
from util.util import log, readconf
import traceback
import multiprocessing

class DbManager():
    _lock = multiprocessing.Lock()
    def __init__(self, conf_args, conn_args):
        DbManager._lock.acquire()
        try:
            self._pool = PooledDB(MySQLdb, *conf_args, **conn_args)
            # self._pool = PooledDB(creator=MySQLdb, mincached=1, maxcached=20, maxconnections=30, **conn_args)
        except Exception,e:
            log.error('初始化数据库失败，请检查，并重试' + str(e))
        finally:
            DbManager._lock.release()

    def _getConn(self):
        conn = None
        DbManager._lock.acquire()
        try:
            conn = self._pool.connection()
        except Exception,e:
            conn = None
            log.error('连接mysql数据库失败，请检查，并重试' + str(e))
        finally:
            DbManager._lock.release()
        return conn

class MysqlConn(object):
    """
    """

    collectionDict = {}

    def __init__(self,conf):
        self._serverAddr = conf.get('mysqlServerAddr'.lower(),'127.0.0.1')
        self._serverPort = int(conf.get('mysqlServerPort'.lower(),'3306'))
        self._serverUser = conf.get('mysqlServerUser'.lower(),'root')
        self._serverPwd = conf.get('mysqlServerPassword'.lower(),'root')
        self._database = conf.get('mysqlDatabaseName'.lower(),'ecgs')
        self.initDb()


    def initDb(self):
        conf_args = (10, 10, 30, 100, True, 0, None)
        conn_args = {
            'host': "%s" % self._serverAddr,
            'port': self._serverPort,
            'db': "%s" % self._database,
            'charset': "%s" % 'utf8',
            'user': "%s" % self._serverUser,
            'passwd': "%s" % self._serverPwd
        }

        self._dbManager = DbManager(conf_args, conn_args)

    def getConn(self):
        return self._dbManager._getConn()

    def testConnection(self):
        conn = self.getConn()
        return False if not conn else True

    def insertData(self,sql):
        result = True
        try:
            conn = self.getConn()
            cur = conn.cursor()
            cur.execute(sql)
            conn.commit()
        except MySQLdb.OperationalError,e:
            log.error('向数据库写数据失败:' + sql + ".error:" + str(e))
            self.reconnectDB()
            pass
        except MySQLdb.MySQLError,e:
            log.error('向数据库写数据失败:' + sql + ".error:" + str(e))
            result = False
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()
        if result:
            log.debug('向数据库写数据成功:' + sql )
        return result

    def updateData(self,sql):
        result = True
        try:
            conn = self.getConn()
            cur = conn.cursor()
            cur.execute(sql)
            conn.commit()
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
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()
        if result:
            log.debug('向数据库更新数据成功:' + sql )
        return result

    def deleteData(self,sql):
        result = True
        try:
            conn = self.getConn()
            cur = conn.cursor()
            cur.execute(sql)
            conn.commit()
        except MySQLdb.OperationalError,e:
            log.error('向数据库删除数据失败:' + sql + ".error:" + str(e))
            self.reconnectDB()
            pass
        except MySQLdb.MySQLError,e:
            log.error('向数据库删除数据失败:' + sql + ".error:" + str(e))
            result = False
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()
        if result:
            log.debug('向数据库删除数据成功:' + sql )
        return result

    def selectData(self,sql):
        data = []
        try:
            conn = self.getConn()
            cur = conn.cursor()
            num = cur.execute(sql)
            data = cur.fetchmany(num)
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
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()
        log.debug('查询数据:' + sql + '>>>' + str(data))
        return data[:]


    def reconnectDB(self):
        re = False
        try:
            self.initDb()
            log.info('重连mysql数据库成功')
            re = True
        except:
            import traceback
            traceback.print_exc()
            log.error('重连mysql数据库失败')
        finally:
            return re


    def __del__(self):
        pass

    @staticmethod
    def getMysqlConn():
        mysqlConner = MysqlConn(readconf('config.conf','mysql'))
        print 'getMysqlConn',mysqlConner
        return mysqlConner

    @staticmethod
    def getProcMysqlConn():
        currentProcId = multiprocessing.current_process().pid
        if currentProcId in MysqlConn.collectionDict:
            return MysqlConn.collectionDict[currentProcId]
        else:
            mysqlConner = MysqlConn(readconf('config.conf', 'mysql'))
            MysqlConn.collectionDict[currentProcId] = mysqlConner
            print 'getMysqlConn', mysqlConner, MysqlConn.collectionDict
            return mysqlConner


# mysqlConn = MysqlConn.getMysqlConn()

