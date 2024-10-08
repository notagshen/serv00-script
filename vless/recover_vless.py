import os
import json
import subprocess
import requests
# 从环境变量中获取密钥
accounts_json = os.getenv('ACCOUNTS_JSON')
telegram_token = os.getenv('TELEGRAM_TOKEN')
telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
wecom_bot_token = os.getenv('WECOM_BOT_TOKEN')

def send_telegram_message(message):
    telegram_url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    telegram_payload = {
        "chat_id": telegram_chat_id,
        "text": message,
        "reply_markup": '{"inline_keyboard":[[{"text":"问题反馈❓","url":"https://t.me/yxjsjl"}]]}'
    }

    response = requests.post(telegram_url, json=telegram_payload)
    print(f"Telegram 请求状态码：{response.status_code}")
    print(f"Telegram 请求返回内容：{response.text}")

    if response.status_code != 200:
        print("发送 Telegram 消息失败")
    else:
        print("发送 Telegram 消息成功")
def send_wecom_bot_message(message):
    wx_headers = {
        'Content-Type': 'application/json',
    }

    json_data = {
        'msgtype': 'text',
        'text': {
            'content': f'{message}',
        },
    }

    try:
        response = requests.post(f'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={wecom_bot_token}', headers=wx_headers,
                             json=json_data)
        if response.status_code != 200:
            print(f"发送消息到WeCom_bot失败: {response.text}")
    except Exception as e:
        print(f"发送消息到WeCom_bot时出错: {e}")
def send_message(message):
    if telegram_chat_id:
        # 发送汇总消息到 Telegram
        send_telegram_message(message)
    if wecom_bot_token:
        # 发送汇总消息到 wecom_bot
        send_wecom_bot_message(message)

try:
    servers = json.loads(accounts_json)

except json.JSONDecodeError:
    error_message = "ACCOUNTS_JSON 参数格式错误"
    print(error_message)
    send_message(error_message)
    exit(1)

# 初始化汇总消息
summary_message = "serv00-vless 恢复操作结果：\n"

# 默认恢复命令
default_restore_command = "cd ~/domains/$USER.serv00.net/vless && ./check_vless.sh"

# 遍历服务器列表并执行恢复操作
for server in servers:
    host = server['host']
    port = server['port']
    username = server['username']
    password = server['password']
    cron_command = server.get('cron', default_restore_command)

    print(f"连接到 {host}...")

    # 执行恢复命令（这里假设使用 SSH 连接和密码认证）
    restore_command = f"sshpass -p '{password}' ssh -o StrictHostKeyChecking=no -p {port} {username}@{host} '{cron_command}'"
    try:
        output = subprocess.check_output(restore_command, shell=True, stderr=subprocess.STDOUT)
        output_utf8 =output.decode('utf-8')
        if "开始检查pm2 vless进程...\nvless进程正在运行。" in output_utf8:
            print("vless进程已经运行，无需推送")
        else:
            summary_message += f"\n成功恢复 {host} 上的 vless 服务：\n{output.decode('utf-8')}"
            send_message(summary_message)

    except subprocess.CalledProcessError as e:
        summary_message += f"\n无法恢复 {host} 上的 vless 服务：\n{e.output.decode('utf-8')}"
        send_message(summary_message)



