#!/usr/bin/env python
# -*- coding:utf-8 -*-
from collections import namedtuple

User = namedtuple('User', ['user_id', 'passwd', 'wechat_openid'])


login_options = {
    # 首次使用请运行 UESTC_Setup_Wizard.exe，向导会自动生成 config.py。
    'user': User('请填写学号', '请填写密码', None),

    # 认证页面地址和 ac_id 会因接入位置不同而变化。
    # 寝室公寓常见地址：http://aaa.uestc.edu.cn 或 http://10.253.0.235
    # 主楼教学楼常见地址：http://10.253.0.237
    'url': "http://10.253.0.237",
    'ac_id': '1',

    # 常见运营商后缀：
    # 校园网：@dx-uestc
    # 电信：@dx
    # 移动：@cmcc
    'domain': '@dx-uestc',

    # 网络状态检测配置。
    'test_ip': "1.1.1.1",
    'delay': 16,
    'max_failed': 3,
}
