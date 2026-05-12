#!/usr/bin/env python
# -*- coding:utf-8 -*-
import base64
import html
import os
import platform
import subprocess
import time
from pathlib import Path
from app_paths import app_dir


def _run_hidden(args):
    startupinfo = None
    creationflags = 0
    if platform.system().lower().startswith("windows"):
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        creationflags = subprocess.CREATE_NO_WINDOW
    return subprocess.run(
        args,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        startupinfo=startupinfo,
        creationflags=creationflags,
        timeout=10,
    )


def _extract_reason(message):
    lines = [line.strip() for line in str(message).splitlines() if line.strip()]
    for line in reversed(lines):
        if not line.startswith(("Traceback ", "File ")):
            return line
    return "Unknown error"


def describe_error(message):
    reason = _extract_reason(message)
    lower_reason = reason.lower()
    known_reasons = [
        ("cannot resolve ip from login page", "无法从校园网认证页面解析当前设备 IP，可能是认证页面格式变化或当前网络环境不在校园网认证范围内。"),
        ("cannot resolve token from challenge response", "无法从校园网认证接口响应中解析登录令牌，可能是认证接口返回格式发生变化。"),
        ("failed to establish a new connection", "无法连接校园网认证服务器，可能是网络未接入、认证服务器不可达或地址配置不正确。"),
        ("max retries exceeded", "多次连接校园网认证服务器失败，可能是网络不稳定或认证服务器暂时不可达。"),
        ("read timed out", "访问校园网认证服务器超时，可能是网络拥塞或认证服务器响应过慢。"),
        ("timed out", "网络请求超时，可能是当前网络不稳定或认证服务器响应过慢。"),
        ("connection refused", "认证服务器拒绝连接，可能是认证接口地址或端口不正确。"),
        ("no route to host", "当前网络无法到达认证服务器，请检查是否已连接校园网。"),
        ("name resolution", "域名解析失败，请检查网络连接或认证服务器地址配置。"),
    ]
    for marker, description in known_reasons:
        if marker in lower_reason:
            return description
    return reason


def _today_log_path():
    return app_dir() / "logs" / time.strftime("%Y-%m-%d.log")


def notify_message(title, message, timeout_seconds=15):
    """Show a short Windows notification and a reliable system message."""
    if not platform.system().lower().startswith("windows"):
        return False

    display_title = str(title) or "校园网自动登录异常"
    text = str(message)
    if len(text) > 500:
        text = text[:497] + "..."

    safe_title = html.escape(display_title, quote=False)
    safe_text = html.escape(text, quote=False)
    script = f"""
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml('<toast><visual><binding template="ToastGeneric"><text>{safe_title}</text><text>{safe_text}</text></binding></visual></toast>')
$toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('UESTC Auto Login').Show($toast)
"""
    encoded = base64.b64encode(script.encode("utf-16le")).decode("ascii")
    toast_ok = False
    try:
        completed = _run_hidden([
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-EncodedCommand",
            encoded,
        ])
        toast_ok = completed.returncode == 0
    except Exception:
        pass

    try:
        system_message = " - ".join(f"{display_title}：{text}".splitlines())
        completed = _run_hidden([
            "msg",
            "*",
            f"/TIME:{timeout_seconds}",
            system_message,
        ])
        return toast_ok or completed.returncode == 0
    except Exception:
        return toast_ok


def notify_error(title, message):
    """Show a Windows notification for background failures."""
    reason = describe_error(message)
    log_path = _today_log_path()
    text = f"原因: {reason}。详情日志: {log_path}"
    return notify_message(title or "校园网自动登录异常", text, timeout_seconds=30)
