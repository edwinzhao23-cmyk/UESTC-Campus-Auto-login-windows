#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os
import sys
import time
import traceback
from pathlib import Path
import ctypes

os.environ["UESTC_BACKGROUND"] = "1"
from app_paths import app_dir  # noqa: E402


def _exit_if_already_running():
    if os.name != "nt":
        return
    kernel32 = ctypes.windll.kernel32
    global _mutex_handle
    _mutex_handle = kernel32.CreateMutexW(None, False, "Global\\UESTC_Campus_Auto_Login_Background")
    if kernel32.GetLastError() == 183:
        sys.exit(0)


_exit_if_already_running()


def _redirect_stdio():
    log_dir = app_dir() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_name = time.strftime("%Y-%m-%d.log", time.localtime())
    stream = open(log_dir / log_name, "a", encoding="utf-8", buffering=1)
    sys.stdout = stream
    sys.stderr = stream


_redirect_stdio()

from always_online import always_login  # noqa: E402
from config_loader import load_login_options  # noqa: E402
from logger import logger  # noqa: E402
from notifier import describe_error, notify_error  # noqa: E402


def main():
    logger.info("电子科技大学校园网自动登录后台程序已启动。")
    while True:
        try:
            always_login(**load_login_options())
        except Exception:
            error = traceback.format_exc()
            logger.error("后台程序捕获到异常，15 秒后将自动重试。异常原因：%s\n完整异常信息：\n%s", describe_error(error), error)
            notify_error("校园网自动登录异常", error)
            time.sleep(15)


if __name__ == "__main__":
    main()
