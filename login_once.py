# !/usr/bin/env python
# -*- coding:utf-8 -*-
from BitSrunLogin.LoginManager import LoginManager
from config_loader import load_login_options

if __name__ == '__main__':
    login_options = load_login_options()
    user = login_options['user']
    LoginManager(**login_options).login(username=user.user_id, password=user.passwd)
