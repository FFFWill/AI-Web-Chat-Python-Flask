# -*- coding: utf-8 -*-
# @Author: FWill
# @Time: 2025-04-08 19:00
# @File: AI web chat.py
# @Description: This code uses the flask library to implement a multifunctional AI conversation on a web page.

"""
Flask服务端程序，集成ollama大模型、知识库查询、函数执行、文件上传等功能
流式响应、对话历史记录、生成中断、首文本拼接（用于设定）、文本转语音。
"""

# 导入必要库
from flask import Flask, request, jsonify, Response, render_template,send_file  # Web框架相关
import ollama  # 大模型客户端库
import os, re, time, datetime, codecs, logging  # 系统/工具库
from threading import Lock  # 线程锁
import subprocess  # 子进程管理
from datetime import datetime
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple

# 全局配置
generation_stop_flag = False  # 生成中断标志位
generation_lock = Lock()  # 用于保护共享资源的线程锁


# 自定义UTF-8编码日志处理器
class UTF8Handler(logging.FileHandler):
    """强制使用UTF-8编码写入日志文件，解决中文乱码问题"""
    def __init__(self, filename, mode='a', encoding=None, delay=False):
        super().__init__(filename, mode, encoding=encoding, delay=delay)
        self.stream = codecs.open(filename, mode, encoding='utf-8')  # 重写文件流编码


# 初始化Flask应用
app = Flask(__name__, template_folder='.')  # 设置模板目录为当前目录


# 获取本机IPv6地址
def get_ipv6_address():
    """通过执行系统命令获取IPv6地址"""
    output = os.popen("ipconfig /all").read()  # Windows系统命令
    result = re.findall(r"(([a-f0-9]{1,4}:){7}[a-f0-9]{1,4})", output, re.I)
    return result[0][0] if result else None  # 返回第一个匹配结果或None


# 生成格式化时间字符串
def get_time(fmt: str = '%Y年%m月%d日_%H时%M分%S秒') -> str:
    """生成指定格式的时间字符串"""
    ts = time.time()  # 获取时间戳
    ta = time.localtime(ts)  # 转换为本地时间元组
    return time.strftime(fmt, ta)  # 格式化为字符串


# 自定义日志过滤器函数
def custom_log_filter(record):
    """过滤掉特定API端点的访问日志"""
    # 仅处理请求日志（如access logs）
    if record.name == 'werkzeug':
        # 解析日志消息，提取请求路径和方法
        message = record.getMessage()
        if "GET /api/get_audio_timestamp" in message:
            return False  # 跳过记录
    return True  # 其他日志正常记录

# 配置日志系统
logging.basicConfig(
    level=logging.WARNING,  # 设置最低日志级别level=logging.WARNING
    format='%(asctime)s - %(levelname)s - %(message)s',  # 日志格式
    handlers=[  # 多处理器配置
        #UTF8Handler('chat.log'),  # 写入chat.log文件
        logging.StreamHandler()  # 同时输出到控制台
    ]
)

# 为Werkzeug日志添加自定义过滤器
for handler in logging.root.handlers:
    handler.addFilter(custom_log_filter)


# 核心AI交互函数
def chat_ollama(user_message, stream):
    """与ollama服务进行交互"""
    host = 'http://localhost:11434'  # ollama默认服务地址
    cli = ollama.Client(host=host)  # 创建客户端实例

    # 发送聊天请求(启用流式响应)
    response = cli.chat(
        model=modname,  # 使用全局配置的模型名称
        messages=[{'role': 'user', 'content': user_message}],  # 用户消息列表
        stream=stream,  # 启用流式模式(逐步返回生成内容)
        options=options
    )
    return response


# 对话记录存储相关函数
def save_chat_record(user_message, ai_response):
    """保存完整对话记录到文件（增加标记清理）"""
    os.makedirs('chatlist', exist_ok=True)  # 确保存储目录存在
    date_str = datetime.now().strftime("%Y%m%d")  # 生成日期字符串
    filename = os.path.join('chatlist', f"{date_str}.txt")  # 构建文件路径

    # 新增：清理用户消息中的特殊标记及其内容
    cleaned_user_message = re.sub(
        r'<#<#<.*?>#>#>',  # 非贪婪匹配特殊标记对
        '',
        user_message,
        flags=re.DOTALL  # 使.匹配换行符
    ).strip()

    # 清理AI响应中的思考标记(保留正式回复)
    cleaned_response = re.sub(
        r'###正在思考###.*?###总结部分###',  # 非贪婪匹配思考部分
        '',
        ai_response,
        flags=re.DOTALL  # 使.匹配换行符
    ).strip()

    # 追加写入文件(UTF-8编码)
    with codecs.open(filename, 'a', encoding='utf-8') as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record = f"[{timestamp}] 用户的问题: {cleaned_user_message}\nAI回复: {cleaned_response}###RECORD_SEPARATOR###\n"
        f.write(record)

def get_chat_records(date_str, num_records=5):
    """获取指定日期的最近N条对话记录"""
    filename = os.path.join('chatlist', f"{date_str}.txt")

    if not os.path.exists(filename):
        app.logger.warning(f"历史记录文件 {filename} 不存在")
        return []

    try:
        with codecs.open(filename, 'r', encoding='utf-8') as f:
            lines = f.read()

        # 使用正则表达式匹配完整对话记录
        pattern = r'\[.*?\]\s*用户的问题:[\s\S]*?AI回复:[\s\S]*?(?=###RECORD_SEPARATOR###|\Z)'
        records = re.findall(pattern, lines, re.DOTALL)

        if records:
            processed_records = []
            # 对返回记录进行长度截断处理
            for record in records[-num_records:]:
                if len(record) > max_history_length:
                    trimmed_record = record[:max_history_length] + '...'
                    app.logger.debug(f"截断历史记录: 原长度{len(record)} → 新长度{len(trimmed_record)}")
                    processed_records.append(trimmed_record)
                else:
                    processed_records.append(record)
            return processed_records
        else:
            app.logger.warning("未找到匹配的历史记录")
            return []
    except Exception as e:
        app.logger.error(f"读取历史记录失败: {str(e)}")
        return []


# 知识库查询函数
def find_best_matches(user_query):
    """从知识库目录查找最相关的文件内容"""
    folder_path = 'listku/processed_listku'
    if not os.path.exists(folder_path):
        app.logger.warning("知识库文件夹不存在")
        return []

    files = os.listdir(folder_path)
    if not files:
        app.logger.warning("知识库文件夹为空")
        return []

    matches = []
    query_chars = set(user_query.lower())  # 将查询词转为小写集合

    for filename in files:
        if not filename.endswith('.txt'):
            continue

        base_filename = os.path.splitext(filename)[0].lower()
        score = 0

        # 计算字符匹配得分(每个字符出现次数*2)
        for char in query_chars:
            score += base_filename.count(char) * 2

        # 计算单词匹配得分(每个单词长度*3)
        for word in user_query.lower().split():
            if word in base_filename:
                score += len(word) * 3

        if score > threshold:  # 超过阈值则记录
            try:
                with codecs.open(os.path.join(folder_path, filename), 'r', encoding='utf-8') as f:
                    content = re.sub(r'\s+', ' ', f.read().strip())  # 合并多余空白
                    content = content.replace('\n', ' ')  # 移除换行符
                    if not content.strip():
                        continue
                    matches.append((filename, content, score))
            except Exception as e:
                app.logger.error(f"读取知识库文件失败: {str(e)}")

    matches.sort(key=lambda x: x[2], reverse=True)  # 按得分降序排列
    return matches[:max_results]  # 返回前N个结果


# API路由：获取可用函数列表
@app.route('/api/list_funcs', methods=['GET'])
def list_funcs():
    """返回func目录下可用的Python函数列表"""
    try:
        func_dir = 'func'
        actual_files = [f for f in os.listdir(func_dir) if
                        f.endswith('.py') and os.path.isfile(os.path.join(func_dir, f))]
        app.logger.info(f"检测到函数目录文件: {actual_files}")
        return {'funcs': actual_files}
    except Exception as e:
        app.logger.error(f"获取函数列表异常: {str(e)}")
        return {'funcs': []}, 500


# API路由：执行指定函数
@app.route('/api/run_func', methods=['GET'])
def run_func():
    """执行func目录下的指定Python函数"""
    func_name = request.args.get('func')
    raw_input = request.args.get('raw_input', '')

    # 新增：清理输入中的角色设定标记及其内容
    cleaned_input = re.sub(
        r'<#<#<.*?>#>#>',  # 非贪婪匹配特殊标记对
        '',
        raw_input,
        flags=re.DOTALL  # 使.匹配换行符
    ).strip()
    app.logger.debug(f"清理前参数: {raw_input[:50]}...")  # 仅记录前50字符
    app.logger.debug(f"清理后参数: {cleaned_input}")
    if not func_name or not func_name.endswith('.py'):
        return "无效的函数请求", 400

    func_path = os.path.join('func', func_name)
    if not os.path.exists(func_path):
        return f"函数文件不存在: {func_path}", 404

    try:
        # 执行子进程并捕获输出（使用清理后的输入）
        result = subprocess.run(
            ['python', '-u', func_path, cleaned_input],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            timeout=60
        )
        output = result.stdout.strip()
        error = result.stderr.strip()

        # 对输出结果进行长度截断处理
        max_func_length = request.args.get('max_func_length', 150, type=int)
        if len(output) > max_func_length:
            output = output[:max_func_length] + '...'
            app.logger.debug(f"函数返回截断: 原长度{len(result.stdout)} → 新长度{len(output)}")

        if error:
            app.logger.error(f"子进程错误: {error}")
            return f"执行错误: {error}", 500
        return output
    except Exception as e:
        return f"执行错误: {str(e)}", 500


# 文件上传路由
@app.route('/api/upload', methods=['POST'])
def upload_image():
    """处理图片上传请求"""
    if 'image' not in request.files:
        return {'error': '未选择文件'}, 400

    file = request.files['image']
    if file.filename == '':
        return {'error': '未选择文件'}, 400

    if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        return {'error': '仅支持PNG/JPG格式'}, 400

    upload_folder = 'image'
    os.makedirs(upload_folder, exist_ok=True)

    # 生成唯一文件名(避免覆盖)
    timestamp = get_time()
    original_extension = os.path.splitext(file.filename)[1]
    filename_base = f"{timestamp}{original_extension}"
    counter = 1
    while os.path.exists(os.path.join(upload_folder, filename_base)):
        filename_base = f"{timestamp}_{counter}{original_extension}"
        counter += 1

    save_path = os.path.join(upload_folder, filename_base)

    try:
        file.save(save_path)
        app.logger.info(f"图片上传成功: {filename_base}")
        return {'filename': filename_base}
    except Exception as e:
        app.logger.error(f"图片保存失败: {str(e)}")
        return {'error': '文件保存失败'}, 500

# setting文件夹,读取设定文件夹中一个设定文件的内容后拼接用户问题
@app.route('/api/list_settings', methods=['GET'])
def list_settings():
    """返回setting目录下的.txt文件列表"""
    try:
        folder_path = 'setting'
        files = [f for f in os.listdir(folder_path) if f.endswith('.txt')]
        return {'files': files}
    except Exception as e:
        app.logger.error(f"获取设置文件列表异常: {str(e)}")
        return {'files': []}, 500

@app.route('/api/get_setting_content', methods=['GET'])
def get_setting_content():
    """获取指定设置文件的内容"""
    filename = request.args.get('file')
    if not filename or not filename.endswith('.txt'):
        return {'error': '无效的文件请求'}, 400

    file_path = os.path.join('setting', filename)
    if not os.path.exists(file_path):
        return {'error': '文件不存在'}, 404

    try:
        with codecs.open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        return {'content': content}
    except Exception as e:
        app.logger.error(f"读取设置文件失败: {str(e)}")
        return {'error': '读取文件失败'}, 500

@app.route('/audio/<filename>')
def serve_audio(filename):
    """提供音频文件下载"""
    audio_folder = 'audio'
    file_path = os.path.join(audio_folder, filename)
    if not os.path.exists(file_path):
        return f"音频文件 {filename} 不存在", 404
    try:
        return send_file(
            file_path,
            mimetype='audio/wav',
            as_attachment=False
        )
    except Exception as e:
        app.logger.error(f"提供音频文件失败: {str(e)}")
        return str(e), 500


@app.route('/api/get_audio_timestamp', methods=['GET'])
def get_audio_timestamp():
    """获取音频更新时间戳"""
    if not os.path.exists('audio_timestamp.txt'):
        return {'timestamp': 0}, 404

    try:
        with open('audio_timestamp.txt', 'r') as f:
            return {'timestamp': float(f.read().strip())}
    except Exception as e:
        app.logger.error(f"读取时间戳失败: {str(e)}")
        return {'timestamp': 0}, 500

# 主页路由
@app.route('/')
def index():
    """返回主页面HTML模板"""
    return render_template('index.html', ipv6_address=get_ipv6_address())


# 生成中断路由
@app.route('/api/stop_generation', methods=['POST'])
def stop_generation():
    """设置生成中断标志位"""
    global generation_stop_flag
    with generation_lock:
        generation_stop_flag = True
    return jsonify({'status': 'stopping'}), 200


# 核心对话路由
@app.route('/api/chat', methods=['POST'])
def chat():
    """处理用户对话请求"""
    use_memory = request.json.get('useMemory', False)  # 是否使用对话记忆
    use_database = request.json.get('useDatabase', False)  # 是否查询知识库
    user_message = request.json['message']  # 用户原始消息

    settings = request.json.get('settings', {})

    # 从请求中提取配置参数
    global re_chatlist, max_history_length, max_results, re_max_listku, modname, max_func_length
    re_chatlist = settings.get('re_chatlist', 2)  # 历史记录返回数量
    max_history_length = settings.get('max_history_length', 200)  # 单条历史最大长度
    max_results = settings.get('max_results', 2)  # 知识库返回数量
    re_max_listku = settings.get('re_max_listku', 150)  # 知识库内容截断长度
    max_func_length = settings.get('max_func_length', 150)  # 函数返回截断长度
    modname = settings.get('modname', 'deepseek-r1:8b')  # AI模型名称
    use_tts = request.json.get('useTTS', False)  # 是否启用文本转语音

    # 构建历史记录上下文
    history_parts = []
    if use_memory:
        today_str = datetime.now().strftime("%Y%m%d")
        matched_records = get_chat_records(today_str, re_chatlist)
        for i, record in enumerate(matched_records, start=1):
            history_parts.append(f"[历史对话 {i}]:\n{record}")

    if use_database:
        matched_files = find_best_matches(user_message)
        matched_files = matched_files[:max_results]
        for i, (filename, content, match_ratio) in enumerate(matched_files, start=1):
            trimmed_content = content[:re_max_listku]
            if len(content) > re_max_listku:
                trimmed_content += '...'
                app.logger.debug(f"数据库内容截断: 原长度{len(content)} → 新长度{len(trimmed_content)}")
            if not trimmed_content.strip():
                continue
            history_parts.append(f"[数据库资料 {i} - {filename} (关联性: {match_ratio:.2f})]:\n{trimmed_content}")

    full_history = "\n\n".join(history_parts) if history_parts else ""

    # 添加函数执行结果(如果存在)
    if 'currentFunc' in request.json and request.json['currentFunc']:
        func_result = request.json['currentFunc']
        full_content = f"{user_message}\n\n[函数执行结果]:\n{func_result}\n\n{full_history}"
    else:
        full_content = f"{user_message}\n\n{full_history}" if full_history else user_message

    # 定义生成器函数(流式响应)
    def generate(content):
        global generation_stop_flag  # 声明使用全局变量
        try:
            app.logger.info(f"流式处理开始: {content[:50]}...")
            stream = chat_ollama(content, True)  # 获取流式响应
            full_response = ""

            # 发送历史记录信息
            yield "\n\n📌 正在参考以下信息：\n\n"
            for part in history_parts:
                yield f"{part.replace('###RECORD_SEPARATOR###', '')}\n\n"
            yield "💡 AI思考过程：\n"

            # 逐步处理流式响应
            for chunk in stream:
                with generation_lock:
                    if generation_stop_flag:
                        generation_stop_flag = False
                        raise GeneratorExit("用户请求停止生成")

                content = chunk['message']['content']
                # 处理思考标记
                if content.startswith('<think>'):
                    content = content.replace('<think>', '\n###正在思考###\n', 1)
                elif content.startswith('</think>'):
                    content = content.replace('</think>', '\n###总结部分###\n', 1)

                app.logger.debug(f"发送数据块: {content}")
                yield f"{content}"
                full_response += content

            app.logger.info("流式处理完成")
            # 保存完整对话记录(包含思考过程)
            save_chat_record(user_message, full_response.strip())

            # 修改后的文本转语音执行逻辑
            if use_tts:
                app.logger.info("执行文本转语音脚本")
                subprocess.run(
                    ['python', "文本转语音.py"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8'
                )
                app.logger.info("文本转语音脚本执行完成")

                # 更新音频时间戳
                timestamp = time.time()
                with open('audio_timestamp.txt', 'w') as f:
                    f.write(f"{timestamp}")
        except GeneratorExit as e:
            app.logger.warning(f"流式处理中止: {str(e)}")
        except Exception as e:
            app.logger.error(f"流式错误: {str(e)}")
            yield f"[ERROR] {str(e)}\n\n"

    # 返回流式响应
    return Response(generate(full_content), mimetype='text/event-stream')


# 程序入口
if __name__ == '__main__':
    threshold = 15  # 知识库匹配最低得分阈值

    options = {
        "temperature": 0.95,             # 控制生成文本的随机性,值越低越保守.更多地控制着模型输出的"冷静度"或"热情度",即输出的随机性程度.
        #"max_tokens": 512,              # 限制生成文本的最大长度(token).
        "top_p": 0.9,                   # top_p采样,模型会生成一组候选 token 然后从累积概率达到或超过'p'的 token 中随机选择一个作为输出.随机性,创造性.
        "top_k": 10,                   # 从模型认为最可能的"k"个词中选择下一个词."k"值越大,选择范围越广,生成的文本越多样;"k"值越小,选择范围越窄,生成的文本越趋向于高概率的词.
        # "presence penalty": 0,        # 0-1.5轻惩罚,2强惩罚,一种固定的惩罚,如果一个token已经在文本中出现过,就会受到惩罚.这会导致模型引入更多新的token/单词/短语,不会明显抑制常用词的重复.
        # "frequency penalty": 0,       # 频率惩罚,让token每次在文本中出现都受到惩罚.这可以阻止重复使用相同的token/单词/短语,同时也会使模型讨论的主题更加多样化,更频繁地更换主题.
    }

    # 获取IPv6地址并启动服务
    ipv6_address = get_ipv6_address()
    if ipv6_address:
        app.run(host=ipv6_address, port=91, debug=True, threaded=True)
    else:
        print("No valid IPv6 address found. Falling back to localhost.")
        app.run(host='localhost', port=91, debug=True, threaded=True)
