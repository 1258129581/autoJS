import argparse
import requests
import re
import sys
import time

# ================== 正则：提取 API 接口 ==================
PATH_PATTERN = re.compile(
    r'["\'`](\/?[a-zA-Z0-9_-]+(?:\/[a-zA-Z0-9_./?=&%${}-]+)+)["\'`]'
)

# ================== 请求头（按抓包构造） ==================
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/144.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://wyjg.hqu.edu.cn/",
    "Cookie": "insert_cookie=19683875",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
}

# ================== 读取输入文件 ==================
def read_js_names(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            names = [line.strip() for line in f if line.strip()]
            print(f"[INFO] 读取到 {len(names)} 个 JS 名称")
            return names
    except Exception as e:
        print(f"[ERROR] 无法读取输入文件: {e}")
        sys.exit(1)

# ================== 构造 JS 路径（参数化） ==================
def build_js_path(js_prefix, name):
    """
    js_prefix: /static/js
    name: app.663b84e7501c0e02e792

    -> /static/js/app.663b84e7501c0e02e792.js
    """
    js_prefix = js_prefix.rstrip("/")
    if name.endswith(".js"):
        return f"{js_prefix}/{name}"
    return f"{js_prefix}/{name}.js"

# ================== 请求 JS 并提取接口 ==================
def extract_paths_from_js(js_url, timeout=10):
    try:
        resp = requests.get(
            js_url,
            headers=HEADERS,
            timeout=timeout
        )
        resp.raise_for_status()
        print(f"[OK] 请求成功，响应大小 {len(resp.text)} bytes")
    except Exception as e:
        print(f"[FAIL] 请求失败: {e}")
        return set()

    paths = set(PATH_PATTERN.findall(resp.text))
    print(f"[INFO] 提取到 {len(paths)} 个接口")
    return paths

# ================== 主函数 ==================
def main():
    parser = argparse.ArgumentParser(
        description="请求 JS 文件并提取其中的 API 接口（JS 路径通过参数传入）"
    )
    parser.add_argument(
        "-i", "--input",
        required=True,
        help="JS 名称输入文件"
    )
    parser.add_argument(
        "-d", "--domain",
        required=True,
        help="站点域名，如 https://wyjg.hqu.edu.cn"
    )
    parser.add_argument(
        "-p", "--js-path",
        required=True,
        help="JS 路径前缀，如 /static/js"
    )
    parser.add_argument(
        "-o", "--output",
        help="输出文件（不指定则打印到终端）"
    )

    args = parser.parse_args()

    print("\n========== 程序启动 ==========")
    print(f"[INFO] 输入文件: {args.input}")
    print(f"[INFO] 域名: {args.domain}")
    print(f"[INFO] JS 路径前缀: {args.js_path}")
    print(f"[INFO] 输出方式: {'文件 ' + args.output if args.output else '终端打印'}")
    print("================================")

    js_names = read_js_names(args.input)

    all_paths = set()
    success_count = 0

    for index, name in enumerate(js_names, start=1):
        js_path = build_js_path(args.js_path, name)
        js_url = args.domain.rstrip("/") + js_path

        print(f"\n[{index}/{len(js_names)}] 处理 JS")
        print(f"[INFO] 原始名称: {name}")
        print(f"[INFO] 请求地址: {js_url}")

        paths = extract_paths_from_js(js_url)
        if paths:
            success_count += 1
            all_paths.update(paths)

        time.sleep(0.2)

    print("\n========== 处理完成 ==========")
    print(f"[INFO] 成功请求 JS: {success_count}/{len(js_names)}")
    print(f"[INFO] 总接口数量: {len(all_paths)}")

    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                for p in sorted(all_paths):
                    f.write(p + "\n")
            print(f"[INFO] 结果已写入: {args.output}")
        except Exception as e:
            print(f"[ERROR] 写入文件失败: {e}")
    else:
        print("\n======= 提取到的接口 =======")
        for p in sorted(all_paths):
            print(p)

    print("========== 程序结束 ==========\n")

# ================== 入口 ==================
if __name__ == "__main__":
    main()
