import time


def get_time(fmt: str = '%Y年%m月%d日%H时%M分%S秒') -> str:#'%Y-%m-%d_%H-%M-%S'
    '''
    获取当前时间（文件名安全格式）
    '''
    ts = time.time()
    ta = time.localtime(ts)
    t = time.strftime(fmt, ta)
    return t


def main():
    now = get_time()
    text = f"【现在时间为: {now}】\n"
    print(text)


if __name__ == "__main__":
    main()
