#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 过滤工具 - 删除与 delete 功能相关的接口
功能：
1. 读取 result.txt 文件
2. 过滤掉包含 delete 关键字的接口
3. 输出到新文件或覆盖原文件
"""

import argparse
import re
import os


def filter_delete_apis(input_file, output_file=None, keywords=None, case_sensitive=False, backup=True):
    """
    过滤删除相关的 API 接口
    
    Args:
        input_file: 输入文件路径
        output_file: 输出文件路径（如果为 None，则覆盖原文件）
        keywords: 要过滤的关键字列表（默认为 ['delete', 'del']）
        case_sensitive: 是否区分大小写（默认不区分）
        backup: 是否备份原文件（默认备份）
    """
    # 默认关键字
    if keywords is None:
        keywords = ['delete', 'del']
    
    # 检查输入文件是否存在
    if not os.path.exists(input_file):
        print(f"[错误] 输入文件不存在: {input_file}")
        return False
    
    # 读取文件内容
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"[错误] 读取文件失败: {e}")
        return False
    
    print(f"[信息] 读取到 {len(lines)} 行数据")
    
    # 过滤接口
    filtered_lines = []
    deleted_lines = []
    
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:  # 跳过空行
            continue
        
        # 检查是否包含关键字
        should_delete = False
        matched_keyword = None
        
        for keyword in keywords:
            if case_sensitive:
                if keyword in line_stripped:
                    should_delete = True
                    matched_keyword = keyword
                    break
            else:
                if keyword.lower() in line_stripped.lower():
                    should_delete = True
                    matched_keyword = keyword
                    break
        
        if should_delete:
            deleted_lines.append((line_stripped, matched_keyword))
        else:
            filtered_lines.append(line_stripped)
    
    # 显示统计信息
    print("\n" + "=" * 70)
    print("过滤结果统计:")
    print("=" * 70)
    print(f"  原始接口数量: {len(lines)}")
    print(f"  删除接口数量: {len(deleted_lines)}")
    print(f"  保留接口数量: {len(filtered_lines)}")
    
    if deleted_lines:
        print(f"\n被删除的接口列表 (共 {len(deleted_lines)} 个):")
        for i, (api, keyword) in enumerate(deleted_lines, 1):
            print(f"  {i:3d}. {api} (匹配关键字: {keyword})")
    
    # 确定输出文件
    if output_file is None:
        output_file = input_file
        
        # 备份原文件
        if backup:
            backup_file = input_file + '.bak'
            try:
                with open(backup_file, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                print(f"\n[信息] 原文件已备份到: {backup_file}")
            except Exception as e:
                print(f"\n[警告] 备份文件失败: {e}")
    
    # 写入过滤后的内容
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for line in filtered_lines:
                f.write(line + '\n')
        print(f"\n[成功] 过滤后的结果已保存到: {output_file}")
        return True
    except Exception as e:
        print(f"\n[错误] 写入文件失败: {e}")
        return False


def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(
        description='API 过滤工具 - 删除与 delete 功能相关的接口',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 过滤 result.txt 中的 delete 相关接口（覆盖原文件）
  python filter_delete_api.py -i result.txt
  
  # 过滤并输出到新文件
  python filter_delete_api.py -i result.txt -o filtered_result.txt
  
  # 自定义过滤关键字
  python filter_delete_api.py -i result.txt -k delete del remove
  
  # 区分大小写过滤
  python filter_delete_api.py -i result.txt --case-sensitive
  
  # 不备份原文件
  python filter_delete_api.py -i result.txt --no-backup
        """
    )
    
    parser.add_argument(
        '-i', '--input',
        required=True,
        help='输入文件路径（默认: result.txt）'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='输出文件路径（不指定则覆盖原文件）'
    )
    
    parser.add_argument(
        '-k', '--keywords',
        nargs='+',
        default=['delete', 'del'],
        help='要过滤的关键字列表（默认: delete del）'
    )
    
    parser.add_argument(
        '--case-sensitive',
        action='store_true',
        help='区分大小写（默认不区分）'
    )
    
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='不备份原文件（默认会备份）'
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("API 过滤工具 - 删除与 delete 功能相关的接口")
    print("=" * 70)
    print(f"\n输入参数:")
    print(f"  输入文件: {args.input}")
    print(f"  输出文件: {args.output if args.output else '覆盖原文件'}")
    print(f"  过滤关键字: {', '.join(args.keywords)}")
    print(f"  区分大小写: {'是' if args.case_sensitive else '否'}")
    print(f"  备份原文件: {'否' if args.no_backup else '是'}")
    print()
    
    # 执行过滤
    success = filter_delete_apis(
        input_file=args.input,
        output_file=args.output,
        keywords=args.keywords,
        case_sensitive=args.case_sensitive,
        backup=not args.no_backup
    )
    
    if success:
        print("\n" + "=" * 70)
        print("过滤完成！")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("过滤失败！")
        print("=" * 70)
        exit(1)


if __name__ == "__main__":
    main()

