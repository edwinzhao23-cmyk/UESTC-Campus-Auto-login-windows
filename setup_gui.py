#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os
import locale
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk


PROJECT_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent

AUTH_URLS = [
    ("寝室公寓：http://aaa.uestc.edu.cn", "http://aaa.uestc.edu.cn"),
    ("寝室公寓：http://10.253.0.235", "http://10.253.0.235"),
    ("主楼教学楼：http://10.253.0.237", "http://10.253.0.237"),
    ("自定义", ""),
]

AC_IDS = [
    ("主楼/教学楼：ac_id=1", "1"),
    ("寝室/公寓：ac_id=3", "3"),
    ("自定义", ""),
]

DOMAINS = [
    ("校园网：@dx-uestc", "@dx-uestc"),
    ("电信：@dx", "@dx"),
    ("移动：@cmcc", "@cmcc"),
    ("自定义", ""),
]


def app_path(exe_name, py_name):
    exe_path = PROJECT_DIR / exe_name
    if exe_path.exists():
        return exe_path
    return PROJECT_DIR / py_name


def quote_for_schtasks(path):
    return f'"{path}"'


def run_hidden(args, timeout=120):
    startupinfo = None
    creationflags = 0
    if os.name == "nt":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        creationflags = subprocess.CREATE_NO_WINDOW
    return subprocess.run(
        args,
        cwd=str(PROJECT_DIR),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding=locale.getpreferredencoding(False),
        errors="replace",
        startupinfo=startupinfo,
        creationflags=creationflags,
        timeout=timeout,
    )


def python_command_for(py_file):
    pythonw = shutil.which("pythonw.exe")
    python = shutil.which("python.exe") or shutil.which("python")
    if py_file.name == "background_runner.py" and pythonw:
        return f'"{pythonw}" "{py_file}"'
    if python:
        return f'"{python}" "{py_file}"'
    return None


def task_command(exe_name, py_name):
    target = app_path(exe_name, py_name)
    if target.suffix.lower() == ".exe":
        return quote_for_schtasks(target)
    return python_command_for(target)


def create_startup_task():
    command = task_command("background_runner.exe", "background_runner.py")
    if not command:
        raise RuntimeError("没有找到可用的 background_runner.exe，也没有找到 Python 环境。")
    run_hidden(["schtasks", "/End", "/TN", "UESTC Campus Auto Login"], timeout=30)
    result = run_hidden([
        "schtasks",
        "/Create",
        "/TN",
        "UESTC Campus Auto Login",
        "/SC",
        "ONLOGON",
        "/TR",
        command,
        "/F",
    ])
    if result.returncode != 0:
        raise RuntimeError(result.stdout.strip() or "创建开机自启动任务失败。")
    run_hidden(["schtasks", "/Run", "/TN", "UESTC Campus Auto Login"], timeout=30)


def create_cleanup_task():
    command = task_command("log_cleanup.exe", "log_cleanup.py")
    if not command:
        raise RuntimeError("没有找到可用的 log_cleanup.exe，也没有找到 Python 环境。")
    run_hidden(["schtasks", "/End", "/TN", "UESTC Campus Auto Login Log Cleanup"], timeout=30)
    result = run_hidden([
        "schtasks",
        "/Create",
        "/TN",
        "UESTC Campus Auto Login Log Cleanup",
        "/SC",
        "DAILY",
        "/ST",
        "03:20",
        "/TR",
        command,
        "/F",
    ])
    if result.returncode != 0:
        raise RuntimeError(result.stdout.strip() or "创建日志清理任务失败。")


def escape_python_string(value):
    return str(value).replace("\\", "\\\\").replace("'", "\\'")


def write_config(values):
    config = f"""#!/usr/bin/env python
# -*- coding:utf-8 -*-
from collections import namedtuple

User = namedtuple('User', ['user_id', 'passwd', 'wechat_openid'])

login_options = {{
    'user': User('{escape_python_string(values["username"])}', '{escape_python_string(values["password"])}', None),
    'url': '{escape_python_string(values["url"])}',
    'ac_id': '{escape_python_string(values["ac_id"])}',
    'domain': '{escape_python_string(values["domain"])}',
    'test_ip': '{escape_python_string(values["test_ip"])}',
    'delay': {int(values["delay"])},
    'max_failed': {int(values["max_failed"])},
}}
"""
    (PROJECT_DIR / "config.py").write_text(config, encoding="utf-8")


def update_retention_days(retention_days):
    cleanup_path = PROJECT_DIR / "log_cleanup.py"
    if not cleanup_path.exists():
        return
    text = cleanup_path.read_text(encoding="utf-8")
    import re

    text = re.sub(r"RETENTION_DAYS = \d+", f"RETENTION_DAYS = {int(retention_days)}", text)
    cleanup_path.write_text(text, encoding="utf-8")


def check_runtime():
    mode = "独立 EXE 模式" if getattr(sys, "frozen", False) else "源码模式"
    lines = [f"当前运行模式：{mode}"]

    for exe_name, py_name, desc in [
        ("background_runner.exe", "background_runner.py", "后台自动登录程序"),
        ("login_once.exe", "login_once.py", "一次性登录测试程序"),
        ("log_cleanup.exe", "log_cleanup.py", "日志清理程序"),
    ]:
        exe_path = PROJECT_DIR / exe_name
        py_path = PROJECT_DIR / py_name
        if exe_path.exists():
            lines.append(f"已找到 {desc}：{exe_name}")
        elif py_path.exists() and shutil.which("python.exe"):
            lines.append(f"已找到 {desc} 源码：{py_name}，将使用本机 Python 运行")
        else:
            lines.append(f"缺少 {desc}：{exe_name}")

    if not getattr(sys, "frozen", False):
        python = shutil.which("python.exe") or shutil.which("python")
        lines.append(f"Python：{python or '未找到'}")
        if python:
            try:
                result = run_hidden([python, "-c", "import requests; print('requests ok')"], timeout=20)
                if result.returncode == 0:
                    lines.append("requests：已安装")
                else:
                    lines.append("requests：未安装，可用清华源执行：python -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple requests")
            except Exception as exc:
                lines.append(f"requests 检测失败：{exc}")
    else:
        lines.append("Python 环境：无需用户安装，EXE 已内置运行环境。")

    return "\n".join(lines)


class Wizard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("电子科技大学校园网自动登录配置向导")
        self.geometry("760x690")
        self.minsize(700, 640)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.frame = ttk.Frame(self, padding=18)
        self.frame.grid(row=0, column=0, sticky="nsew")
        self.frame.columnconfigure(1, weight=1)

        self.vars = {}
        self.build_form()
        self.log(check_runtime())

    def build_form(self):
        title = ttk.Label(self.frame, text="电子科技大学校园网自动登录配置向导", font=("Microsoft YaHei UI", 16, "bold"))
        title.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 12))

        tip = ttk.Label(
            self.frame,
            text="配置会写入本机 config.py。密码会明文保存在本机，请不要把配置后的文件夹发给别人。",
            foreground="#9a3412",
        )
        tip.grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 14))

        row = 2
        self.vars["username"] = tk.StringVar()
        self.add_entry(row, "账号/学号", self.vars["username"])
        row += 1

        self.vars["password"] = tk.StringVar()
        self.add_entry(row, "密码", self.vars["password"], show="*")
        row += 1

        self.vars["url_choice"] = tk.StringVar(value=AUTH_URLS[0][0])
        self.add_combo(row, "认证页面地址", self.vars["url_choice"], [x[0] for x in AUTH_URLS], self.on_url_change)
        row += 1

        self.vars["custom_url"] = tk.StringVar()
        self.add_entry(row, "自定义认证地址", self.vars["custom_url"])
        row += 1

        self.vars["ac_choice"] = tk.StringVar(value=AC_IDS[0][0])
        self.add_combo(row, "ac_id", self.vars["ac_choice"], [x[0] for x in AC_IDS], self.on_ac_change)
        row += 1

        self.vars["custom_ac"] = tk.StringVar()
        self.add_entry(row, "自定义 ac_id", self.vars["custom_ac"])
        row += 1

        self.vars["domain_choice"] = tk.StringVar(value=DOMAINS[0][0])
        self.add_combo(row, "运营商后缀", self.vars["domain_choice"], [x[0] for x in DOMAINS], self.on_domain_change)
        row += 1

        self.vars["custom_domain"] = tk.StringVar()
        self.add_entry(row, "自定义运营商后缀", self.vars["custom_domain"])
        row += 1

        self.vars["test_ip"] = tk.StringVar(value="1.1.1.1")
        self.add_entry(row, "联网检测 IP", self.vars["test_ip"])
        row += 1

        self.vars["delay"] = tk.StringVar(value="16")
        self.add_entry(row, "检测间隔（秒）", self.vars["delay"])
        row += 1

        self.vars["max_failed"] = tk.StringVar(value="3")
        self.add_entry(row, "连续失败次数", self.vars["max_failed"])
        row += 1

        self.vars["retention_days"] = tk.StringVar(value="14")
        self.add_entry(row, "日志保留天数", self.vars["retention_days"])
        row += 1

        self.vars["test_login"] = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.frame, text="保存配置后立即测试登录", variable=self.vars["test_login"]).grid(
            row=row, column=1, sticky="w", pady=(8, 4)
        )
        row += 1

        buttons = ttk.Frame(self.frame)
        buttons.grid(row=row, column=0, columnspan=3, sticky="ew", pady=(10, 8))
        ttk.Button(buttons, text="保存配置并安装后台任务", command=self.start_install).pack(side="left")
        ttk.Button(buttons, text="只保存配置", command=self.save_only).pack(side="left", padx=8)
        ttk.Button(buttons, text="退出", command=self.destroy).pack(side="right")
        row += 1

        self.output = tk.Text(self.frame, height=12, wrap="word")
        self.output.grid(row=row, column=0, columnspan=3, sticky="nsew", pady=(8, 0))
        self.frame.rowconfigure(row, weight=1)

        self.on_url_change()
        self.on_ac_change()
        self.on_domain_change()

    def add_entry(self, row, label, var, show=None):
        ttk.Label(self.frame, text=label).grid(row=row, column=0, sticky="w", pady=4)
        entry = ttk.Entry(self.frame, textvariable=var, show=show)
        entry.grid(row=row, column=1, columnspan=2, sticky="ew", pady=4)
        return entry

    def add_combo(self, row, label, var, values, command):
        ttk.Label(self.frame, text=label).grid(row=row, column=0, sticky="w", pady=4)
        combo = ttk.Combobox(self.frame, textvariable=var, values=values, state="readonly")
        combo.grid(row=row, column=1, columnspan=2, sticky="ew", pady=4)
        combo.bind("<<ComboboxSelected>>", lambda _event: command())
        return combo

    def on_url_change(self):
        is_custom = self.vars["url_choice"].get() == "自定义"
        self.set_entry_state("custom_url", is_custom)

    def on_ac_change(self):
        is_custom = self.vars["ac_choice"].get() == "自定义"
        self.set_entry_state("custom_ac", is_custom)

    def on_domain_change(self):
        is_custom = self.vars["domain_choice"].get() == "自定义"
        self.set_entry_state("custom_domain", is_custom)

    def set_entry_state(self, key, enabled):
        # Entry widgets are small enough here that lookup by variable is simpler than storing every widget.
        for child in self.frame.winfo_children():
            if isinstance(child, ttk.Entry) and str(child.cget("textvariable")) == str(self.vars[key]):
                child.configure(state="normal" if enabled else "disabled")

    def resolve_choice(self, key, custom_key, options):
        choice = self.vars[key].get()
        if choice == "自定义":
            return self.vars[custom_key].get().strip()
        for label, value in options:
            if label == choice:
                return value
        return ""

    def collect_values(self):
        values = {
            "username": self.vars["username"].get().strip(),
            "password": self.vars["password"].get(),
            "url": self.resolve_choice("url_choice", "custom_url", AUTH_URLS).strip(),
            "ac_id": self.resolve_choice("ac_choice", "custom_ac", AC_IDS).strip(),
            "domain": self.resolve_choice("domain_choice", "custom_domain", DOMAINS).strip(),
            "test_ip": self.vars["test_ip"].get().strip(),
            "delay": self.vars["delay"].get().strip(),
            "max_failed": self.vars["max_failed"].get().strip(),
            "retention_days": self.vars["retention_days"].get().strip(),
        }
        missing = [name for name, value in values.items() if not value]
        if missing:
            raise ValueError("以下配置不能为空：" + "、".join(missing))
        for key in ["delay", "max_failed", "retention_days"]:
            number = int(values[key])
            if number <= 0:
                raise ValueError(f"{key} 必须大于 0。")
            values[key] = number
        return values

    def log(self, message):
        self.output.insert("end", str(message).rstrip() + "\n")
        self.output.see("end")
        self.update_idletasks()

    def save_only(self):
        try:
            values = self.collect_values()
            write_config(values)
            update_retention_days(values["retention_days"])
            self.log("已保存 config.py。")
            messagebox.showinfo("完成", "配置已保存。")
        except Exception as exc:
            messagebox.showerror("错误", str(exc))

    def start_install(self):
        thread = threading.Thread(target=self.install_flow, daemon=True)
        thread.start()

    def install_flow(self):
        try:
            values = self.collect_values()
            write_config(values)
            update_retention_days(values["retention_days"])
            self.log("已保存 config.py。")

            if self.vars["test_login"].get():
                self.log("正在测试登录...")
                try:
                    login_target = app_path("login_once.exe", "login_once.py")
                    if login_target.suffix.lower() == ".exe":
                        result = run_hidden([str(login_target)], timeout=60)
                    else:
                        python = shutil.which("python.exe") or shutil.which("python")
                        if not python:
                            raise RuntimeError("未找到 Python，无法运行源码版登录测试。请使用 EXE 发布包。")
                        result = run_hidden([python, str(login_target)], timeout=60)
                    self.log(result.stdout.strip() or "登录测试命令已执行。")
                    if result.returncode != 0:
                        self.log("登录测试返回非 0 状态，请根据上方输出检查配置。后台任务仍会继续安装。")
                except Exception as exc:
                    self.log(f"登录测试启动失败，但会继续安装后台任务。原因：{exc}")

            self.log("正在创建并启动后台开机自启动任务...")
            create_startup_task()
            self.log("后台开机自启动任务已创建并启动。")

            self.log("正在创建日志自动清理任务...")
            create_cleanup_task()
            self.log("日志自动清理任务已创建。")

            self.log("安装完成。")
            messagebox.showinfo("完成", "配置和后台任务已安装完成。")
        except Exception as exc:
            self.log(f"安装失败：{exc}")
            messagebox.showerror("安装失败", str(exc))


if __name__ == "__main__":
    app = Wizard()
    app.mainloop()
