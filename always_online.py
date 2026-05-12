#!/usr/bin/env python
# -*- coding:utf-8 -*-
import ctypes
import subprocess
import time
import platform

from logger import logger
from BitSrunLogin.LoginManager import LoginManager
from config_loader import load_login_options
from notifier import describe_error, notify_error, notify_message

# 获取计算机名
host_name = platform.node()
try:
    #  disable the QuickEdit and Insert mode for the current console
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-10), 128)
except:
    pass

def is_connect_internet(test_ip):
    if platform.system().lower().startswith('windows'):
        cmd = ["ping", str(test_ip), "-n", "1"]
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        creationflags = subprocess.CREATE_NO_WINDOW
    else:
        cmd = ["ping", str(test_ip), "-c", "1"]
        startupinfo = None
        creationflags = 0

    try:
        status = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            startupinfo=startupinfo,
            creationflags=creationflags,
            timeout=10,
        ).returncode
    except subprocess.TimeoutExpired:
        return False

    return status == 0

def always_login(user=None, test_ip=None, delay=2, max_failed=3, **kwargs):
    time_now = lambda: time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    org_delay = delay
    failed = 0
    logger.info(f'[{time_now()}] [{host_name}] 网络监控已启动，开始检测校园网连接状态。')
    while True:
        if not is_connect_internet(test_ip):
            failed += 1
            delay = max(0., delay / 2)
            logger.warning(
                f'[{time_now()}] [{host_name}] 网络检测失败，第 {failed}/{max_failed} 次，测试地址：{test_ip}。'
            )
            if failed >= max_failed:
                logger.info(f'[{time_now()}] [{host_name}] 已连续检测失败，判断为离线，准备发起校园网登录。')
                result = LoginManager(**kwargs).login(username=user.user_id, password=user.passwd)
                logger.info(f'[{time_now()}] [{host_name}] 登录接口返回结果：{result}。')
        else:
            if failed >= max_failed:
                logger.info(f'[{time_now()}] [{host_name}] 网络已恢复在线。')
                notify_message(
                    "校园网连接已恢复",
                    f"网络已恢复在线，后台自动登录程序正在继续监控。时间：{time_now()}",
                    timeout_seconds=12,
                )
            failed = 0
            delay = org_delay
        time.sleep(delay)


if __name__ == "__main__":

    while True:
        try:
            always_login(**load_login_options())
        except:
            import traceback

            error = traceback.format_exc()
            logger.error("网络监控循环捕获到异常，15 秒后将自动重试。异常原因：%s\n完整异常信息：\n%s", describe_error(error), error)
            notify_error("校园网自动登录异常", error)
            time.sleep(15)
