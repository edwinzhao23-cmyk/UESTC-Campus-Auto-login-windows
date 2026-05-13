# 电子科技大学校园网自动认证登录 Windows 一键部署工具

这是一个给 Windows 用户使用的电子科技大学校园网自动登录工具。

你只需要下载压缩包、解压、双击配置向导、按提示填写账号密码，就可以让电脑在后台自动保持校园网在线。正常运行时没有窗口；出错或断网后恢复在线时，会弹 Windows 系统消息提醒。

## 先说最重要的

`config.py` 会保存你的校园网账号和密码，而且是明文保存。

所以请记住：

1. 不要把配置后的 `config.py` 发给别人。
2. 不要把配置后的整个文件夹上传到 GitHub。
3. 如果你要分享本项目，请分享未配置的源码或 Release 压缩包。
4. 本仓库已经用 `.gitignore` 忽略 `config.py`、日志和本地打包目录，避免误传。

## 项目来源与致谢

本项目是在已有校园网登录脚本基础上整理和增强的版本，主要参考：

- [Akashiarcher/UESTC-](https://github.com/Akashiarcher/UESTC-)：电子科技大学校园网自动连接脚本，适配新版登录页面。
- [b71db892/AutoLoginUESTC](https://github.com/b71db892/AutoLoginUESTC)：更早期的 UESTC 自动登录项目。
- [coffeehat/BIT-srun-login-script](https://github.com/coffeehat/BIT-srun-login-script)：深澜/SRUN 登录流程相关实现。

感谢原作者们对校园网认证流程的整理。本仓库主要做的是 Windows 普通用户可直接使用的安装、后台运行、日志和提醒能力。

## 这个版本做了什么改进

- 提供图形化配置向导：双击 `UESTC_Setup_Wizard.exe` 就能配置。
- EXE 发布包内置 Python 运行环境，普通用户不需要自己安装 Python。
- 账号、密码、认证地址、`ac_id`、运营商后缀都在向导里填写或选择。
- 自动生成 `config.py`。
- 自动测试一次登录。
- 自动创建开机自启动计划任务。
- 自动启动后台静默运行程序。
- 自动创建日志清理计划任务。
- 后台运行不弹黑色命令行窗口。
- 断网后恢复在线会弹 Windows 系统消息。
- 程序异常会弹 Windows 系统消息，并在日志中写明原因。
- 日志尽量使用中文说明。
- 日志默认保留 14 天，定期清理。
- 网络检测不会再周期性弹 `cmd` 窗口。

## 下载后怎么用

下面按最慢、最清楚的方式写。第一次用请照着做。

### 第 1 步：下载

进入本项目 GitHub 页面。

找到右侧或页面中的 `Releases`，下载最新版压缩包，文件名通常类似：

```text
UESTC-AutoLogin-EXE-xxxx.zip
```

如果你拿到的是别人发给你的压缩包，也可以直接继续下一步。

### 第 2 步：解压

右键压缩包，选择“全部解压”。

解压后你会看到一个文件夹，里面有这些文件：

```text
UESTC_Setup_Wizard.exe
background_runner.exe
login_once.exe
log_cleanup.exe
config.py
logs
README.md
使用说明.md
```

你只需要记住一个文件：

```text
UESTC_Setup_Wizard.exe
```

### 第 3 步：打开配置向导

双击：

```text
UESTC_Setup_Wizard.exe
```

如果 Windows 提示“未知发布者”或 SmartScreen 提醒，请确认文件来自你信任的仓库后，再选择继续运行。

### 第 4 步：填写账号和密码

在配置向导里填写：

- `账号/学号`：填你的校园网账号或学号
- `密码`：填你的校园网/统一认证密码

密码输入框会显示为星号，这是正常的。

### 第 5 步：选择认证页面地址

向导里有一个“认证页面地址”下拉框。

常见选择：

| 使用场景 | 推荐选择 |
| --- | --- |
| 寝室、公寓 | `http://aaa.uestc.edu.cn` |
| 寝室、公寓 | `http://10.253.0.235` |
| 主楼、教学楼 | `http://10.253.0.237` |

如果你不确定，可以先按自己所在位置选择。登录失败时再回来换另一个。

### 第 6 步：选择 ac_id

向导里有一个 `ac_id` 下拉框。

常见选择：

| 使用场景 | 推荐 ac_id |
| --- | --- |
| 主楼、教学楼 | `1` |
| 寝室、公寓 | `3` |

如果登录失败，可以重新运行向导换一个 `ac_id`。

### 第 7 步：选择运营商后缀

向导里有一个“运营商后缀”下拉框。

常见选择：

| 类型 | 后缀 |
| --- | --- |
| 校园网 | `@dx-uestc` |
| 电信 | `@dx` |
| 移动 | `@cmcc` |

不确定时，可以先选 `校园网：@dx-uestc`。

### 第 8 步：其他选项一般不用改

默认值通常可以直接用：

```text
联网检测 IP：1.1.1.1
检测间隔：16
连续失败次数：3
日志保留天数：14
```

这些含义是：

- 每隔 16 秒检测一次网络。
- 连续 3 次检测失败，就认为可能掉线。
- 掉线后自动尝试登录。
- 日志保留 14 天。

### 第 9 步：点击安装按钮

点击：

```text
保存配置并安装后台任务
```

向导会自动做这些事：

1. 保存配置到 `config.py`。
2. 测试登录一次。
3. 创建后台自动登录任务。
4. 启动后台自动登录任务。
5. 创建日志自动清理任务。

如果窗口下方出现：

```text
校园网登录接口返回结果：ok
后台开机自启动任务已创建并启动。
日志自动清理任务已创建。
安装完成。
```

就说明基本成功了。

## 平时要不要再打开程序

一般不需要。

配置成功后：

- `background_runner.exe` 会在后台运行。
- 下次开机登录 Windows 后，它会自动启动。
- `log_cleanup.exe` 会每天凌晨自动清理旧日志。

你平时不用手动运行 `background_runner.exe`，也不用手动运行 `log_cleanup.exe`。

## 每个 EXE 是干什么的

| 文件 | 是否需要手动运行 | 用途 |
| --- | --- | --- |
| `UESTC_Setup_Wizard.exe` | 需要，首次配置时运行 | 图形化配置向导 |
| `background_runner.exe` | 不需要 | 后台自动登录程序，由计划任务启动 |
| `login_once.exe` | 一般不需要 | 手动测试登录一次 |
| `log_cleanup.exe` | 不需要 | 日志清理程序，由计划任务启动 |

## 日志在哪里

日志在：

```text
logs
```

每天一个文件，例如：

```text
logs\2026-05-12.log
```

如果你遇到问题，可以打开当天日志看原因。

如果用 PowerShell 查看中文日志，请使用：

```powershell
Get-Content .\logs\2026-05-12.log -Encoding UTF8
```

## Windows 计划任务名称

配置向导会创建两个计划任务：

```text
UESTC Campus Auto Login
UESTC Campus Auto Login Log Cleanup
```

第一个负责后台自动登录。

第二个负责每天凌晨清理旧日志。

## 如何确认是否正在运行

打开 Windows 的“任务计划程序”，查看是否有：

```text
UESTC Campus Auto Login
```

如果状态是 `Running`，说明后台程序正在运行。

也可以打开日志目录，看当天日志里是否有：

```text
电子科技大学校园网自动登录后台程序已启动。
网络监控已启动，开始检测校园网连接状态。
```

## 如何重新配置

如果你填错了账号、密码、认证地址、`ac_id` 或运营商：

1. 再次双击 `UESTC_Setup_Wizard.exe`。
2. 重新填写或选择配置。
3. 再次点击“保存配置并安装后台任务”。

新的配置会覆盖旧的 `config.py`。

## 如何卸载

如果你不想继续使用：

1. 打开 Windows“任务计划程序”。
2. 找到并删除：

```text
UESTC Campus Auto Login
UESTC Campus Auto Login Log Cleanup
```

3. 结束正在运行的 `background_runner.exe`。
4. 删除整个工具文件夹。

注意：删除文件夹前，请先停止后台任务，否则 Windows 可能提示文件正在使用。

## 源码运行方式

如果你是开发者，想从源码运行：

```bat
python -m pip install -r requirements.txt
python setup_gui.py
```

手动测试登录：

```bat
python login_once.py
```

手动前台持续监控：

```bat
python always_online.py
```

生成 EXE 发布包：

```bat
python build_exe_release.py
```

构建脚本会优先使用清华源安装 PyInstaller，便于中国境内网络环境使用。

## 常见问题

### 1. 登录测试返回 ok 是什么意思？

说明校园网认证接口返回成功。

### 2. 登录失败怎么办？

重新运行 `UESTC_Setup_Wizard.exe`，优先尝试调整这三项：

1. 认证页面地址
2. `ac_id`
3. 运营商后缀

### 3. 正常开机会弹窗吗？

不会。

正常开机且网络已经在线时，只写日志，不弹窗。

### 4. 什么时候会弹系统消息？

两种情况：

- 程序出现异常
- 连续断网后网络恢复在线

### 5. 为什么文件夹里有 config.py？

`config.py` 是你的本机配置文件。向导会生成它。它包含账号密码，请不要发给别人。

## License

本项目沿用原项目的 MIT License。请在二次发布时保留原始项目和相关实现的致谢链接。
