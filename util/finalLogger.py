#!/usr/bin/env python
#-*-coding:utf-8-*-

import logging
import logging.handlers
from cloghandler import ConcurrentRotatingFileHandler
import os

basedir = os.path.abspath(os.path.join(os.path.dirname(__file__),os.path.pardir))
filepath = os.path.join(basedir,'log/log.log')


"""
"""
class FinalLogger:
    logger = None

    log_level = logging.DEBUG
    log_file = filepath
    log_max_byte = 10 * 1024 * 1024
    log_backup_count = 5

    @staticmethod
    def getLogger():
        if FinalLogger.logger is not None:
            return FinalLogger.logger

        FinalLogger.logger = logging.Logger("oggingmodule.FinalLogger")
        # log_handler = logging.handlers.RotatingFileHandler(filename=FinalLogger.log_file,\
        #         maxBytes = FinalLogger.log_max_byte,\
        #         backupCount = FinalLogger.log_backup_count)
        log_handler = ConcurrentRotatingFileHandler(filename=FinalLogger.log_file,
                                                    maxBytes=FinalLogger.log_max_byte,
                                                    backupCount=FinalLogger.log_backup_count)
        #log_fmt = logging.Formatter("[%(levelname)s] [%(funcName)s] [%(asctime)s] %(message)s")
        log_fmt = logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')
        log_handler.setFormatter(log_fmt)
        FinalLogger.logger.addHandler(log_handler)
        FinalLogger.logger.setLevel(FinalLogger.log_level)

        console = logging.StreamHandler()
        console.setLevel(FinalLogger.log_level)
        #formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
        formatter = logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s\n')
        console.setFormatter(formatter)
        FinalLogger.logger.addHandler(console)
        return FinalLogger.logger


"""
logger.debug("this is a debug msg!")
logger.info("this is a info msg!")
logger.warn("this is a warn msg!")
logger.error("this is a error msg!")
logger.critical("this is a critical msg!")
"""
