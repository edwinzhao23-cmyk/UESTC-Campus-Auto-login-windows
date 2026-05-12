#!/usr/bin/env python
# -*- coding:utf-8 -*-
import importlib.util

from app_paths import app_dir


def load_login_options():
    config_path = app_dir() / "config.py"
    if not config_path.exists():
        raise FileNotFoundError(f"未找到配置文件：{config_path}。请先运行 UESTC_Setup_Wizard.exe 生成配置。")

    spec = importlib.util.spec_from_file_location("uestc_user_config", str(config_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.login_options
