import base64
import requests
import re
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from ._decorators import *

from .encryption.srun_md5 import *
from .encryption.srun_sha1 import *
from .encryption.srun_base64 import *
from .encryption.srun_xencode import *

header = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/63.0.3239.26 Safari/537.36'
}


class LoginManager:

    @staticmethod
    def encode(s):
        return base64.b64encode(s.encode()).decode()

    @staticmethod
    def decode(s):
        return base64.b64decode(s).decode()

    def __init__(self, **kwargs):
        # 所有配置集中在 self.args 里
        self.args = {
            # 基础 URL：主机即可，不带路径
            'url': 'http://10.253.0.235',  # 会被 config.py 里的 url 覆盖

            # 相对路径（后面根据 base url 拼）
            'url_login_page': "/srun_portal_pc",        # 登录页 path
            'url_get_challenge_api': "/cgi-bin/get_challenge",
            'url_login_api': "/cgi-bin/srun_portal",

            # 认证参数
            'n': "200",
            'vtype': "1",
            'ac_id': "3",         # 主楼=1，宿舍=3
            'enc': "srun_bx1",
            'domain': "@dx",      # 会被 config 里的 domain 覆盖

            # 临时参数
            'username': None,
            'password': None,
            'ip': None,
        }

        # 用户名/密码/IP 等直观属性
        self.username = None
        self.password = None
        self.ip = None

        # 覆盖配置（包括 config.py 中的 url / ac_id / domain）
        self.args.update(kwargs)

        # 基础 host（去掉 query 和结尾 /）
        base = self.args['url'].split('?')[0].rstrip('/')
        ac_id = str(self.args.get('ac_id', '3'))

        # 登录页使用和浏览器一致的地址：/srun_portal_pc?ac_id=3&theme=pro
        self.args['url_login_page'] = f"{base}/srun_portal_pc?ac_id={ac_id}&theme=pro"
        self.args['url_get_challenge_api'] = f"{base}{self.args['url_get_challenge_api']}"
        self.args['url_login_api'] = f"{base}{self.args['url_login_api']}"

        # 会话对象：用它来保持 cookie
        self.session = requests.Session()
        # 默认头
        self.session.headers.update(header)

    def login(self, username, password, decode=False):
        if decode:
            username = LoginManager.decode(username)
            password = LoginManager.decode(password)

        # 拼接运营商后缀
        self.username = str(username) + self.args['domain']
        self.password = str(password)

        self.get_ip()
        self.get_token()
        return self.get_login_responce()

    def get_ip(self):
        print("步骤1：从校园网认证页面获取当前设备 IP。")
        self._get_login_page()
        self._resolve_ip_from_login_page()
        print("----------------")

    def get_token(self):
        """
        Step2: 获取 challenge / token
        """
        print("步骤2：向校园网认证接口请求登录令牌。")
        # 用已有的 _get_challenge + _resolve_token_from_challenge_response
        self._get_challenge()
        self._resolve_token_from_challenge_response()

    def get_login_responce(self):
        print("步骤3：提交登录信息并解析认证结果。")
        self._generate_encrypted_login_info()
        self._send_login_info()
        self._resolve_login_responce()
        print("校园网登录接口返回结果：" + self._login_result)
        print("----------------")
        return self._login_result

    def _is_defined(self, varname):
        """
        Check whether variable is defined in the object
        """
        allvars = vars(self)
        return varname in allvars

    @infomanage(
        callinfo="正在获取校园网认证页面。",
        successinfo="已成功获取校园网认证页面。",
        errorinfo="获取校园网认证页面失败，可能是认证页面地址不正确或当前网络无法访问认证服务器。"
    )
    def _get_login_page(self):
        # Step1: Get login page（使用 session，以便保存 cookie）
        self._page_response = self.session.get(
            self.args['url_login_page'],
            # 校园网是 http，这里 verify 无所谓；如果将来换 https 可以用 verify=False
        )

    @checkvars(
        varlist="_page_response",
        errorinfo="缺少校园网认证页面内容，需要先获取认证页面。"
    )
    @infomanage(
        callinfo="正在从认证页面解析当前设备 IP。",
        successinfo="已成功解析当前设备 IP。",
        errorinfo="解析当前设备 IP 失败，可能是学校认证页面格式变化，或当前页面不是正常认证页。"
    )
    def _resolve_ip_from_login_page(self):
        """
        从登录页 HTML / JS 中解析 IP，并顺便解析 ServiceIP（仅打印，不改接口地址）
        """
        text = self._page_response.text
        """
# ===== 临时调试，把登录页 HTML 打出来看看 =====
        print("===== login page raw html (first 1000 chars) =====")
        print(text[:1000])
        print("===================================================")
        # ===============================================
        """
        ip = None

        # 兼容旧版本 hidden input 写法
        patterns = [
            r'id=["\']user_ip["\']\s+value=["\'](.*?)["\']',
            r'id=["\']online_ip["\']\s+value=["\'](.*?)["\']',
            r'id=["\']v46ip["\']\s+value=["\'](.*?)["\']',
        ]
        for pat in patterns:
            m = re.search(pat, text)
            if m:
                ip = m.group(1)
                break

        # 现版本：CONFIG 里  ip     : "10.20.1.141"
        if ip is None:
            m = re.search(r'\bip\s*:\s*"([^"]+)"', text)
            if m:
                ip = m.group(1)

        if ip is None:
            # 解析不到直接报错
            # print(text[:1000])  # 调试时可打开
            raise ValueError("无法从校园网认证页面解析当前设备 IP，可能是认证页面格式变化或当前网络环境不在校园网认证范围内。")

        self.ip = ip
        print("已解析到当前设备 IP：", self.ip)

        # 从 CONFIG 里解析 ServiceIP，仅记录/打印，不再覆盖接口地址
        m_srv = re.search(r'"ServiceIP"\s*:\s*"([^"]+)"', text)
        if m_srv:
            self.service_ip = m_srv.group(1).rstrip('/')
            print("已解析到认证服务地址：", self.service_ip)
        else:
            self.service_ip = None
            print("认证页面中未找到 ServiceIP，将继续使用配置中的认证接口地址。")

    @checkip
    @infomanage(
        callinfo="正在请求校园网登录令牌。",
        successinfo="已收到校园网登录令牌响应。",
        errorinfo="请求校园网登录令牌失败，可能是认证接口地址不正确、网络不通或认证参数不匹配。"
    )
    def _get_challenge(self):
        """
        按 HAR 抓到的方式请求 /cgi-bin/get_challenge
        GET http://10.253.0.235/cgi-bin/get_challenge
            ?callback=jQuery1102...
            &username=<REMOVED>@cmcc
            &ip=10.20.1.141
            &_=timestamp
        """
        import time

        ts = int(time.time() * 1000)
        callback = f"jQuery{ts}"

        params_get_challenge = {
            "callback": callback,
            "username": self.username,  # 已经是 "学号@cmcc"
            "ip": self.ip,
            "_": str(ts),
        }

        # 参考 HAR 设置部分 header（尤其是 Referer / X-Requested-With / Accept）
        ch_headers = header.copy()
        ch_headers.update({
            "Referer": self.args['url_login_page'],
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "text/javascript, application/javascript, application/ecmascript, application/x-ecmascript, */*; q=0.01",
        })

        url = self.args['url_get_challenge_api']

        self._challenge_response = self.session.get(
            url,
            params=params_get_challenge,
            headers=ch_headers,
            # 校园网是 http，verify 不影响；若将来改为 https，有证书问题可加 verify=False
        )

    @checkvars(
        varlist="_challenge_response",
        errorinfo="缺少登录令牌响应，需要先请求校园网登录令牌。"
    )
    @infomanage(
        callinfo="正在解析校园网登录令牌。",
        successinfo="已成功解析校园网登录令牌。",
        errorinfo="解析校园网登录令牌失败，可能是学校认证接口返回格式发生变化。"
    )
    def _resolve_token_from_challenge_response(self):
        text = self._challenge_response.text

        # 一般 srun 返回的 JSON/JSONP 里会有 "challenge":"xxxx"
        m = re.search(r'"challenge"\s*:\s*"([^"]+)"', text)
        if not m:
            raise ValueError("无法从校园网认证接口响应中解析登录令牌，可能是认证接口返回格式发生变化。")

        self.token = m.group(1)

    @checkip
    def _generate_info(self):
        info_params = {
            "username": self.username,
            "password": self.password,
            "ip": self.ip,
            "acid": self.args['ac_id'],
            "enc_ver": self.args['enc']
        }
        info = re.sub("'", '"', str(info_params))
        self.info = re.sub(" ", '', info)

    @checkinfo
    @checktoken
    def _encrypt_info(self):
        self.encrypted_info = "{SRBX1}" + get_base64(get_xencode(self.info, self.token))

    @checktoken
    def _generate_md5(self):
        self.md5 = get_md5(self.password, self.token)

    @checkmd5
    def _encrypt_md5(self):
        self.encrypted_md5 = "{MD5}" + self.md5

    @checktoken
    @checkip
    @checkencryptedinfo
    def _generate_chksum(self):
        self.chkstr = self.token + self.username
        self.chkstr += self.token + self.md5
        self.chkstr += self.token + self.args['ac_id']
        self.chkstr += self.token + self.ip
        self.chkstr += self.token + self.args['n']
        self.chkstr += self.token + self.args['vtype']
        self.chkstr += self.token + self.encrypted_info

    @checkchkstr
    def _encrypt_chksum(self):
        self.encrypted_chkstr = get_sha1(self.chkstr)

    def _generate_encrypted_login_info(self):
        self._generate_info()
        self._encrypt_info()
        self._generate_md5()
        self._encrypt_md5()

        self._generate_chksum()
        self.password = "{MD5}" + self.md5
        self._encrypt_chksum()

    @checkip
    @checkencryptedmd5
    @checkencryptedinfo
    @checkencryptedchkstr
    @infomanage(
        callinfo="正在向校园网认证接口提交登录信息。",
        successinfo="登录信息已成功提交到校园网认证接口。",
        errorinfo="提交校园网登录信息失败，可能是认证接口不可达或登录参数无效。"
    )
    def _send_login_info(self):
        login_info_params = {
            'callback': 'jQuery112407481914773997063_1631531125398',  # 可任意字符串，但不能缺
            'action': 'login',
            'username': self.username,
            'password': self.encrypted_md5,
            'ac_id': self.args['ac_id'],
            'ip': self.ip,
            'chksum': self.encrypted_chkstr,
            'info': self.encrypted_info,
            'n': self.args['n'],
            'type': self.args['vtype'],
            'os': "Windows 10",
            'name': "Windows",
            'double_stack': 0
        }
        self._login_responce = requests.get(
            self.args['url_login_api'],
            params=login_info_params,
            headers=header,
            verify=False,
        )

    @checkvars(
        varlist="_login_responce",
        errorinfo="缺少登录接口响应，需要先提交登录信息。"
    )
    @infomanage(
        callinfo="正在解析校园网登录结果。",
        successinfo="已成功解析校园网登录结果。",
        errorinfo="解析校园网登录结果失败，可能是学校认证接口返回格式发生变化。"
    )
    def _resolve_login_responce(self):
        self._login_result = re.search('"error":"(.*?)"', self._login_responce.text).group(1)


if __name__ == '__mian__':
    m = LoginManager()
