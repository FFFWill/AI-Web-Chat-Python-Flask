import datetime
import os
import re
import requests

save_path = os.path.join("./audio", "1.wav")

def clean_text(text):
    # 定义保留的字符集：中文、字母、数字及指定标点
    pattern = re.compile(r'[^\u4e00-\u9fa5a-zA-Z0-9，。！？]')
    # 替换所有非保留字符为''，并删除多余空格换行
    cleaned = re.sub(pattern, '', text)
    # 合并多个空格/换行为单个（如果需要彻底删除所有空格换行则用 .replace(' ', ''))
    cleaned = re.sub(r'\s+', '', cleaned)
    return cleaned

def get_last_ai_response():
    # 获取当日文件路径
    today = datetime.datetime.now().strftime("%Y%m%d")
    file_path = os.path.join("chatlist", f"{today}.txt")

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
    except FileNotFoundError:
        return "当日聊天文件不存在"

    # 分割聊天记录
    records = [r.strip() for r in content.split('###RECORD_SEPARATOR###') if r.strip()]
    if not records:
        return "无有效聊天记录"

    # 获取最后一条记录
    last_record = records[-1].split('\n')

    # 逆向查找最后一段AI回复
    ai_line = None
    for line in reversed(last_record):
        if line.startswith("AI回复:"):
            ai_line = line
            break

    if ai_line:
        # 获取起始索引
        start_index = last_record.index(ai_line)
        # 处理首行前缀并拼接结果
        cleaned_lines = [last_record[start_index].split("AI回复:", 1)[-1].lstrip()]
        cleaned_lines.extend(last_record[start_index+1:])
        return '\n'.join(cleaned_lines)

    return "未找到AI回复"

# 使用示例
text_ai = get_last_ai_response()

# 文本清洗处理
if text_ai not in ["当日聊天文件不存在", "无有效聊天记录", "未找到AI回复"]:
    # 仅当获取到有效AI回复时进行清洗
    cleaned_text = clean_text(text_ai)
else:
    cleaned_text = text_ai  # 保持错误提示原样

# API的基础URL
base_url = "http://127.0.0.1:9880"

# 请求参数（使用清洗后的文本）
params = {
    "refer_wav_path": "audio/1雷电开心.wav",
    "prompt_text": "生日快乐!那今日就—起庆祝吧,使之成为可以铭记一年的美好瞬间！",
    "prompt_language": "zh",
    "text": cleaned_text,  # 使用清洗后的文本
    "text_language": "zh"
}

# 发送GET请求
response = requests.get(base_url, params=params)
print(cleaned_text)
# 检查响应状态码
if response.status_code == 200:
    # 读取音频数据
    audio_data = response.content
    # 保存音频到文件
    with open(save_path, "wb") as f:
        f.write(response.content)

    # 创建目标目录
    # os.makedirs("audio/zhuancun", exist_ok=True)
    # 构建目标路径
    # target_path = os.path.join("audio/zhuancun", "1.wav")
    # 执行文件复制
    # shutil.copy(save_path, target_path)

else:
    print(f"请求失败，状态码: {response.status_code}")
    print(response.json())