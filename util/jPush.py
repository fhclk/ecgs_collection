#!/usr/bin/env python
#-*-coding:utf-8-*-


import jpush
from jpush import common
from util import readconf,log
import multiprocessing


app_key = readconf('config.conf', 'jpush').get('appKey'.lower(), '')
master_secret = readconf('config.conf', 'jpush').get('masterSecret'.lower(), '')

_jpush = jpush.JPush(app_key, master_secret)
_jpush.set_logging("DEBUG")

lock = multiprocessing.Lock()

def tags(tags, alert, params=None):
    lock.acquire()
    try:
        push = _jpush.create_push()
        push.audience = jpush.audience(
            {"tag": tags}
        )

        push.notification = jpush.notification(alert=alert,
                                               ios=jpush.ios(alert, extras=params),
                                               android=jpush.android(alert, extras=params))
        push.platform = jpush.all_
        print (push.payload)
        push.send()
        print '推送消息：', alert, params
    except Exception,e:
        log.error('极光推送失败:' + str(e))
    finally:
        lock.release()

def alias(alias, alert, params=None):
    lock.acquire()
    try:
        push = _jpush.create_push()
        alias1 = {"alias": alias}
        print(alias1)
        push.audience = jpush.audience(
            alias1
        )

        push.notification = jpush.notification(alert=alert,
                                               ios=jpush.ios(extras=params),
                                               android=jpush.android(alert, extras=params))
        push.platform = jpush.all_
        print (push.payload)
        push.send()
    except Exception,e:
        log.error('极光推送失败:' + str(e))
    finally:
        lock.release()

def all(alert):
    lock.acquire()
    push = _jpush.create_push()
    push.audience = jpush.all_
    push.notification = jpush.notification(alert=alert)
    push.platform = jpush.all_
    try:
        response=push.send()
    except common.Unauthorized:
        raise common.Unauthorized("Unauthorized")
    except common.APIConnectionException:
        raise common.APIConnectionException("conn")
    except common.JPushFailure:
        print ("JPushFailure")
    except:
        print ("Exception")
    finally:
        lock.release()


def audience(alert, tags, alias):
    lock.acquire()
    try:
        push = _jpush.create_push()

        push.audience = jpush.audience(
            jpush.tag(tuple(tags)),
            jpush.alias(tuple(alias))
        )

        push.notification = jpush.notification(alert=alert)
        push.platform = jpush.all_
        print (push.payload)
        push.send()
    finally:
        lock.release()



def notification(alert, params, bigText=''):
    lock.acquire()
    try:
        push = _jpush.create_push()

        push.audience = jpush.all_
        push.platform = jpush.all_

        ios = jpush.ios(alert=alert, sound="a.caf", extras=dict(params))
        android = jpush.android(alert=alert, priority=1, style=1, alert_type=1, big_text=bigText, extras=dict(params))

        push.notification = jpush.notification(alert=alert, android=android, ios=ios)

        # pprint (push.payload)
        result = push.send()
    finally:
        lock.release()


def options(alert):
    lock.acquire()
    try:
        push = _jpush.create_push()
        push.audience = jpush.all_
        push.notification = jpush.notification(alert=alert)
        push.platform = jpush.all_
        push.options = {"time_to_live": 86400, "sendno": 12345, "apns_production": True}
        push.send()
    finally:
        lock.release()
        pass

def platfrom_msg(alert,message='', params=None):
    lock.acquire()
    try:
        push = _jpush.create_push()
        push.audience = jpush.all_
        ios_msg = jpush.ios(alert=alert, badge="+1", sound="a.caf", extras=params)
        android_msg = jpush.android(alert=alert)
        push.notification = jpush.notification(alert=alert, android=android_msg, ios=ios_msg)
        push.message = jpush.message(message, extras=params)
        push.platform = jpush.all_
        push.send()
    finally:
        lock.release()



def sms(alert, message):
    lock.acquire()
    try:
        push = _jpush.create_push()
        push.audience = jpush.all_
        push.notification = jpush.notification(alert=alert)
        push.platform = jpush.all_
        push.smsmessage = jpush.smsmessage(message, 0)
        print (push.payload)
        push.send()
    finally:
        lock.release()

def validate(alert):
    lock.acquire()
    try:
        push = _jpush.create_push()
        push.audience = jpush.all_
        push.notification = jpush.notification(alert=alert)
        push.platform = jpush.all_
        push.send_validate()
    finally:
        lock.release()

if __name__ == '__main__':
    app_key = readconf('../config.conf', 'jpush').get('appKey'.lower(), '')
    master_secret = readconf('../config.conf', 'jpush').get('masterSecret'.lower(), '')
    tags(['40288132506fc09201506fc2a5360007'], 'test alias', {'abc':'zhangsan', 'ssss':'1'})
    # alias(['40288132506fc09201506fc2a5360007'], 'test alias', {'abc':'zhangsan', 'ssss':'1'})
    # all()
    # audience()
    # notification()
    options()
    # platfrom_msg()
    # silent()
    # sms()
    # validate()