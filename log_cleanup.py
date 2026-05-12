#!/usr/bin/env python
# -*- coding:utf-8 -*-
import time
from pathlib import Path

from app_paths import app_dir
from logger import logger

RETENTION_DAYS = 14
LOG_DIR = app_dir() / "logs"


def cleanup_one_old_log(retention_days=RETENTION_DAYS):
    """Delete at most one old log file per run."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    cutoff = time.time() - retention_days * 24 * 60 * 60
    today = time.strftime("%Y-%m-%d.log", time.localtime())

    candidates = []
    for path in LOG_DIR.glob("*.log"):
        if path.name == today:
            continue
        try:
            stat = path.stat()
        except OSError as exc:
            logger.warning("检查日志文件失败：%s，原因：%s", path, exc)
            continue
        if stat.st_mtime < cutoff:
            candidates.append((stat.st_mtime, path))

    if not candidates:
        logger.info("日志清理完成：没有发现超过 %s 天的旧日志文件。", retention_days)
        return None

    _, old_log = sorted(candidates)[0]
    old_log.unlink()
    logger.info("日志清理完成：已删除一个旧日志文件：%s。", old_log)
    return old_log


if __name__ == "__main__":
    cleanup_one_old_log()
