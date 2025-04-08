import os
import re
from collections import Counter


def process_file(file_path, priority_words, blocked_chars, output_dir):
    # 打开文件并读取内容
    with open(file_path, 'r', encoding='utf-8') as file:
        text = file.read()

    # 使用正则表达式将文本分词（匹配单词边界）
    words = re.findall(r'\b\w+\b', text)

    # 统计每个单词的频率
    word_counts = Counter(words)

    # 初始化保存选中单词的列表
    selected_words = []

    # 检查是否存在优先级单词
    for word in priority_words:
        if word in text:
            selected_words.append(word)
            break  # 只使用第一个找到的优先级单词

    # 如果优先级单词不足5个，则继续添加高频单词
    if len(selected_words) < 5:
        # 过滤掉包含被阻止字符的单词
        filtered_words = {word: count for word, count in word_counts.items() if
                          not any(char in word for char in blocked_chars)}
        # 按照单词频率从高到低排序
        most_common_words = [word for word, _ in sorted(filtered_words.items(), key=lambda item: item[1], reverse=True)]

        # 添加单词直到总数达到5个，确保不会重复添加
        additional_words = [word for word in most_common_words if word not in selected_words]
        selected_words.extend(additional_words[:5 - len(selected_words)])

    # 创建新的文件名
    base_name = os.path.basename(file_path)
    name_parts = base_name.split('.')
    if len(name_parts) > 1:
        new_file_name = f"{name_parts[0]}_{'_'.join(selected_words)}.txt"
    else:
        new_file_name = f"{base_name}_{'_'.join(selected_words)}.txt"

    # 新的文件路径
    new_file_path = os.path.join(output_dir, new_file_name)

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 将文件复制到新路径
    with open(file_path, 'r', encoding='utf-8') as infile, open(new_file_path, 'w', encoding='utf-8') as outfile:
        outfile.write(infile.read())

    # 打印处理结果
    print(f"已处理 {file_path} -> {new_file_path}")


def main(input_dir, output_dir, priority_words, blocked_chars):
    # 遍历输入目录中的所有文件
    for filename in os.listdir(input_dir):
        file_path = os.path.join(input_dir, filename)

        # 只处理 .txt 文件
        if filename.endswith('.txt'):
            process_file(file_path, priority_words, blocked_chars, output_dir)


if __name__ == "__main__":
    # 输入目录
    input_directory = 'listku'
    # 输出目录
    output_directory = 'processed_listku'
    # 优先级单词列表
    priority_words = ['Python', '中国', '历史', '灭亡']  # 替换为你的优先级单词
    # 被阻止的字符列表
    blocked_chars = ['的','是','不','你','我','他','还','之','再','在','于']  # 替换为你的阻止字符

    # 调用主函数
    main(input_directory, output_directory, priority_words, blocked_chars)