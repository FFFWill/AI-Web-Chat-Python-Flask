import sys

def main(raw_input):
    # 添加输入处理逻辑
    processed = raw_input.upper() if raw_input else "空输入"
    return f"已处理: {processed}"

if __name__ == "__main__":
    # 直接获取第一个参数（无需判断长度）
    text_user = main(sys.argv[1] if len(sys.argv) > 1 else "")
    text = "已接收并处理！"
    print(text)
