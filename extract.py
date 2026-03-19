#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JS 提取工具 - 完整工作流
用法: python extract.py -u http://example.com/app.js -p /xxx/js

1. webpack_extractor.py 提取文件名 → js.txt
2. js_tiqu.py 读取 js.txt，提取 API → result.txt
3. filter_delete_api.py 过滤删除接口 → result.txt
"""

import os
import sys
import subprocess
import argparse
from urllib.parse import urlparse


def run_command(cmd, description):
    """运行命令"""
    print(f"\n{'='*70}")
    print(f"  {description}")
    print(f"{'='*70}")
    print(f"[*] 命令: {' '.join(cmd)}")
    print()

    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"[错误] 命令执行失败: {e}")
        return False
    except Exception as e:
        print(f"[错误] {e}")
        return False


def step0_prepend_names():
    """
    步骤 0: 将 name.txt 中的文件名预写入 js.txt
    若 name.txt 为空或不存在则跳过
    """
    if not os.path.exists('name.txt'):
        return True

    try:
        with open('name.txt', 'r', encoding='utf-8') as f:
            names = [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"[警告] 读取 name.txt 失败: {e}")
        return True

    if not names:
        return True

    print("\n" + "="*70)
    print("  步骤 0: 将 name.txt 中的文件名预写入 js.txt")
    print("="*70)
    print(f"[*] 读取到 {len(names)} 条文件名")

    # 读取已有 js.txt 内容（若存在）
    existing = []
    if os.path.exists('js.txt'):
        with open('js.txt', 'r', encoding='utf-8') as f:
            existing = [line.strip() for line in f if line.strip()]

    # 合并：name.txt 在前，去重
    seen = set()
    merged = []
    for line in names + existing:
        if line not in seen:
            seen.add(line)
            merged.append(line)

    with open('js.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(merged))

    print(f"[+] 预写入完成，js.txt 共 {len(merged)} 条（name.txt {len(names)} 条 + 原有 {len(existing)} 条）")
    return True


def step1_webpack_extract():
    """
    步骤 1: 调用 webpack_extractor.py 提取 app.txt 中的文件名
    输入: app.txt（已存在）
    输出: js.txt
    """
    print("\n" + "="*70)
    print("  步骤 1: 使用 Webpack Extractor 提取文件名")
    print("="*70)
    print()

    if not os.path.exists('app.txt'):
        print("[错误] app.txt 不存在，请先准备好 app.txt")
        return False

    cmd = ['python', 'webpack_extractor.py']

    if not run_command(cmd, "执行 webpack_extractor.py"):
        print("[错误] webpack_extractor.py 执行失败")
        return False

    if not os.path.exists('js.txt'):
        print("[错误] js.txt 文件未生成")
        return False

    return True


def step2_extract_api(js_domain, js_path_prefix):
    """
    步骤 2: 使用 js_tiqu.py 提取 API
    输入: js.txt
    输出: result.txt

    参数对应关系：
      extract.py -u → 解析出域名 → js_tiqu.py -d
      extract.py -p →             → js_tiqu.py -p
    """
    print("\n" + "="*70)
    print("  步骤 2: 使用 js_tiqu.py 提取 API 接口")
    print("="*70)
    print()
    print(f"[*] 输入文件: js.txt")
    print(f"[*] 域名 (-d): {js_domain}")
    print(f"[*] 路径前缀 (-p): {js_path_prefix}")
    print(f"[*] 输出文件: result.txt")
    print()

    if not os.path.exists('js.txt'):
        print("[错误] 输入文件 js.txt 不存在")
        return False

    cmd = [
        'python', 'js_tiqu.py',
        '-i', 'js.txt',
        '-d', js_domain,
        '-p', js_path_prefix,
        '-o', 'result.txt'
    ]

    if not run_command(cmd, "执行 js_tiqu.py"):
        print("[错误] js_tiqu.py 执行失败")
        return False

    if not os.path.exists('result.txt'):
        print("[错误] result.txt 文件未生成")
        return False

    try:
        with open('result.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        print(f"\n[成功] 提取完成，共 {len(lines)} 个 API")
        print("\n提取结果预览 (前10行):")
        for i, line in enumerate(lines[:10], 1):
            print(f"  {i:3d}. {line.rstrip()}")
        if len(lines) > 10:
            print(f"  ... 还有 {len(lines) - 10} 个 API")
    except Exception as e:
        print(f"[警告] 读取结果失败: {e}")

    return True


def step3_filter_delete_api():
    """
    步骤 3: 使用 filter_delete_api.py 过滤删除接口
    输入/输出: result.txt
    """
    print("\n" + "="*70)
    print("  步骤 3: 使用 filter_delete_api.py 过滤删除接口")
    print("="*70)
    print()
    print(f"[*] 输入文件: result.txt")
    print()

    if not os.path.exists('result.txt'):
        print("[错误] 输入文件 result.txt 不存在")
        return False

    cmd = ['python', 'filter_delete_api.py', '-i', 'result.txt']

    if not run_command(cmd, "执行 filter_delete_api.py"):
        print("[错误] filter_delete_api.py 执行失败")
        return False

    try:
        with open('result.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        print(f"\n[成功] 过滤完成，保留 {len(lines)} 个 API")
        print("\n过滤后结果预览 (前10行):")
        for i, line in enumerate(lines[:10], 1):
            print(f"  {i:3d}. {line.rstrip()}")
        if len(lines) > 10:
            print(f"  ... 还有 {len(lines) - 10} 个 API")
    except Exception as e:
        print(f"[警告] 读取结果失败: {e}")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="JS 提取工具 - 完整工作流",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python extract.py -u http://example.com/app.js -p /static/js
        """
    )
    parser.add_argument('-u', '--url',  required=True, help='站点域名，如 http://example.com')
    parser.add_argument('-p', '--path', required=True, help='JS 文件路径前缀，如 /static/js')

    args = parser.parse_args()

    # 从 URL 中解析域名
    parsed = urlparse(args.url)
    js_domain = f"{parsed.scheme}://{parsed.netloc}"
    js_path_prefix = args.path

    print("="*70)
    print("  JS 提取工具 - 完整工作流")
    print("="*70)
    print()
    print(f"[*] 域名:      {js_domain}")
    print(f"[*] 路径前缀:  {js_path_prefix}")
    print()

    # 步骤 0
    print("[0/3] 步骤 0: 预写入 name.txt")
    step0_prepend_names()

    # 步骤 1
    print("[1/3] 步骤 1: 提取 JS 文件名")
    if not step1_webpack_extract():
        print("\n[错误] 步骤 1 失败")
        return 1

    # 步骤 2
    print("\n[2/3] 步骤 2: 提取 API 接口")
    if not step2_extract_api(js_domain, js_path_prefix):
        print("\n[错误] 步骤 2 失败")
        return 1

    # 步骤 3
    print("\n[3/3] 步骤 3: 过滤删除接口")
    if not step3_filter_delete_api():
        print("\n[错误] 步骤 3 失败")
        return 1

    print("\n" + "="*70)
    print("  所有步骤完成！")
    print("="*70)
    print()
    print("输出文件:")
    print("  - js.txt      (JS 文件名列表)")
    print("  - result.txt  (过滤后的 API 列表)")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
