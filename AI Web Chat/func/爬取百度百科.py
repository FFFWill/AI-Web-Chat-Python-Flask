import requests
import urllib
import sys
import re  # 新增正则表达式模块
from bs4 import BeautifulSoup
import os

def MidString(content, startStr, endStr):
    try:
        start = content.index(startStr) + len(startStr)
        end = content.index(endStr, start)
        return content[start:end]
    except ValueError:
        return None

def BaiDu(Name, save_path='.'):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://www.baidu.com/'
    }
    url = f'https://baike.baidu.com/item/{urllib.parse.quote(Name)}'

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f'请求失败: {e}')
        return

    soup = BeautifulSoup(response.text, 'html.parser')

    # 提取并清洗简介
    description_tag = soup.find('meta', attrs={'name': 'description'})
    description = description_tag['content'] if description_tag else "暂无简介"
    # 新增清洗步骤
    description = re.sub(r'\[\d+\]', '', description)
    description = re.sub(r'\s+', ' ', description).strip()

    # 提取并清洗详细信息
    detailed_info = []
    info_div = soup.find('div', class_='basicInfo_tLQSv J-basic-info')
    if info_div:
        for item in info_div.find_all('div', class_='itemWrapper_nAYF7'):
            text = item.get_text(strip=True)
            # 新增清洗步骤
            cleaned_text = re.sub(r'\[\d+\]', '', text)
            cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
            detailed_info.append(cleaned_text)

    # 提取并清洗正文内容
    main_content = []
    content_div = soup.find('div', class_='J-lemma-content')
    if content_div:
        for para in content_div.find_all('div', class_='para_JZWMz content_PFTy6 MARK_MODULE'):
            text = para.get_text(strip=True)
            # 新增清洗步骤
            cleaned_text = re.sub(r'\[\d+\]', '', text)
            cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
            main_content.append(cleaned_text)

    # 生成合法文件名
    safe_name = Name.replace('/', '_').replace('\\', '_')
    filename = f"{safe_name}.txt"
    full_path = os.path.join(save_path, filename)  # 拼接完整保存路径
    os.makedirs(save_path, exist_ok=True)  # 自动创建目录（如果不存在）

    #print(f"【简介】\n{description}\n")
    #print("\n【详细】")
    #print('\n'.join(detailed_info))
    #print("\n【正文内容】")
    #print('\n'.join(main_content))

    try:
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(f"【词条名称】\n{Name}\n\n")
            f.write("【简介】\n" + description + "\n\n")
            f.write("【详细信息】\n" + "\n".join(detailed_info) + "\n\n")
            f.write("【正文内容】\n" + "\n".join(main_content))
        #print(f"已保存至 {filename}，程序即将关闭...")
        print(f"【简介】\n{description}\n")
        print("\n【详细】")
        print('\n'.join(detailed_info))
        print("\n【正文内容】")
        print('\n'.join(main_content))
    except IOError as e:
        print(f"文件保存失败: {e}")
    finally:
        sys.exit()



def main(raw_input):
    # 添加输入处理逻辑
    processed = raw_input.upper() if raw_input else "空输入"
    return processed



if __name__ == "__main__":
    text_user = main(sys.argv[1] if len(sys.argv) > 1 else "")

    # 新增路径输入
    save_path = './listku/processed_listku'
    if not save_path:
        save_path = '.'  # 使用当前目录

    keyword = text_user
    print("搜索词条:{}\n\n搜索到的内容:".format(text_user))
    if not keyword:
        print("输入为空")
        sys.exit()
    BaiDu(keyword,save_path)
