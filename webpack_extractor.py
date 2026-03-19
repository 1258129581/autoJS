#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Webpack 文件名提取工具

流程：
  读取当前目录的 app.js
  步骤一：提取 id → hash 映射（支持多种格式）
  步骤二：拼接为完整文件名，写入 js.txt

支持格式：
  格式A  纯数字id + 长/短hex（单块）
         319: "9badd48c940a4ef5c9c6"
  格式B  字符串id + 短hex（单块）
         "chunk-15d1eba8": "ed145436"
  格式C  数字id→名称 + 数字id→hash（双块，合并）
         {213:"npm.ajv",...}  +  {213:"2d6fde51",...}
"""

import re
import sys
from typing import Dict, List, Optional, Tuple


class WebpackFileExtractor:
    """Webpack 文件名提取器（两步提取）"""

    # 正则：纯十六进制 value（6~20位）
    RE_HASH_VAL  = re.compile(r'"([a-fA-F0-9]{6,20})"')
    # 正则：数字 key: "hex_value"
    RE_NUM_HASH  = re.compile(r'^\s*(\d+)\s*:\s*"([a-fA-F0-9]{6,20})"', re.MULTILINE)
    # 正则：字符串 key: "hex_value"  （key 以字母或 chunk- 开头）
    RE_STR_HASH  = re.compile(r'"([a-zA-Z][a-zA-Z0-9@~_.\-]*)"\s*:\s*"([a-fA-F0-9]{6,20})"')
    # 正则：数字 key: "非hex字符串"（名称映射）
    RE_NUM_NAME  = re.compile(r'^\s*(\d+)\s*:\s*"([^"]+)"', re.MULTILINE)
    # 正则：{...}[  块提取
    RE_BLOCK     = re.compile(r'\{([^{}]+)\}', re.DOTALL)

    def __init__(self, js_code: str):
        self.js_code  = js_code
        self.chunk_map: Dict[str, str] = {}  # id/name → hash
        self.files: List[str] = []

    # ------------------------------------------------------------------ #
    # 工具：判断字符串是否全为十六进制
    # ------------------------------------------------------------------ #
    @staticmethod
    def _is_hex(s: str) -> bool:
        try:
            int(s, 16)
            return True
        except ValueError:
            return False

    # ------------------------------------------------------------------ #
    # 步骤一：提取 id → hash 映射
    # ------------------------------------------------------------------ #
    def step1_extract_fields(self) -> Dict[str, str]:
        """
        步骤一：逐个 {...} 块分析，识别格式后提取 id→hash 映射。

        策略：
          1. 优先匹配「字符串key: hex」单块（格式B）
          2. 其次匹配「数字key: hex」单块（格式A）
          3. 若存在「数字key: 名称」块 + 「数字key: hex」块，
             则合并为「名称: hash」（格式C）
        """
        print("[步骤一] 提取 id → hash 映射...")

        self.chunk_map = {}
        seen = set()

        # 收集所有块
        blocks = []
        for m in self.RE_BLOCK.finditer(self.js_code):
            blocks.append(m.group(1))

        # 先尝试格式B：字符串key: hex
        for block in blocks:
            pairs = self.RE_STR_HASH.findall(block)
            if not pairs:
                continue
            # 验证：块内所有 value 都是 hex
            all_vals = self.RE_HASH_VAL.findall(block)
            if len(all_vals) != len(pairs):
                continue
            for k, v in pairs:
                if k not in seen:
                    seen.add(k)
                    self.chunk_map[k] = v
                    print(f"  [B] id={k!r:35s}  hash={v}")

        # 再尝试格式A/C：数字key: hex 或双块
        # 收集所有「数字→hex」块 和「数字→名称」块
        num_hash_blocks: List[Dict[str, str]] = []
        num_name_blocks: List[Dict[str, str]] = []

        for block in blocks:
            num_hash = dict(self.RE_NUM_HASH.findall(block))
            if num_hash:
                # 验证所有 value 都是 hex
                all_vals = [v for _, v in self.RE_NUM_HASH.findall(block)]
                if all(self._is_hex(v) for v in all_vals):
                    num_hash_blocks.append(num_hash)
                    continue

            num_name = dict(self.RE_NUM_NAME.findall(block))
            if num_name:
                # 过滤掉纯 hex value（避免把 hash 块误识别为名称块）
                filtered = {k: v for k, v in num_name.items()
                            if not self._is_hex(v)}
                if filtered:
                    num_name_blocks.append(filtered)

        # 格式C：名称块 + hash块，按 id 合并
        if num_name_blocks and num_hash_blocks:
            # 取 key 集合交集最大的组合
            best_name = max(num_name_blocks, key=len)
            best_hash = max(num_hash_blocks, key=len)
            common = set(best_name) & set(best_hash)
            if common:
                print(f"  [C] 双块合并，共 {len(best_hash)} 条 hash，名称映射 {len(common)} 条")
                for eid, ehash in best_hash.items():
                    name = best_name.get(eid, eid)  # 无名称则用 id
                    # 去掉 npm. 前缀
                    name = name[4:] if name.startswith('npm.') else name
                    if eid not in seen:
                        seen.add(eid)
                        self.chunk_map[name] = ehash
                        print(f"  [C] id={name!r:35s}  hash={ehash}")
            else:
                # 无交集，直接用最大 hash 块（格式A）
                self._add_num_hash(best_hash, seen)
        elif num_hash_blocks:
            # 格式A：只有 hash 块
            best_hash = max(num_hash_blocks, key=len)
            self._add_num_hash(best_hash, seen)

        print(f"[步骤一] 共配对 {len(self.chunk_map)} 条记录")
        if not self.chunk_map:
            print("[步骤一][警告] 未找到任何映射，请确认 app.js 格式是否正确")

        return self.chunk_map

    def _add_num_hash(self, num_hash: Dict[str, str], seen: set):
        """将数字id→hash 写入 chunk_map"""
        for eid, ehash in num_hash.items():
            if eid not in seen:
                seen.add(eid)
                self.chunk_map[eid] = ehash
                print(f"  [A] id={eid!r:35s}  hash={ehash}")

    # ------------------------------------------------------------------ #
    # 步骤二：拼接文件名
    # ------------------------------------------------------------------ #
    def step2_assemble(self) -> List[str]:
        """步骤二：id.hash（不含 .js 后缀）"""
        if not self.chunk_map:
            print("[步骤二] 无数据可拼接")
            return []
        print("\n[步骤二] 拼接文件名...")
        self.files = sorted(f"{k}.{v}" for k, v in self.chunk_map.items())
        print(f"[步骤二] 共拼接 {len(self.files)} 个文件名")
        return self.files

    # ------------------------------------------------------------------ #
    # 一键运行
    # ------------------------------------------------------------------ #
    def run(self) -> List[str]:
        self.step1_extract_fields()
        return self.step2_assemble()


# ---------------------------------------------------------------------- #
# 入口：固定读取 app.js，输出到 js.txt
# ---------------------------------------------------------------------- #
if __name__ == "__main__":
    import os

    base_dir = os.path.dirname(os.path.abspath(__file__))
    app_js   = os.path.join(base_dir, "app.txt")
    js_txt   = os.path.join(base_dir, "js.txt")

    print("=" * 60)
    print("Webpack 文件名提取工具")
    print("=" * 60)

    try:
        with open(app_js, 'r', encoding='utf-8') as f:
            code = f.read()
        print(f"[*] 读取 app.txt 成功，大小: {len(code)} 字节\n")
    except FileNotFoundError:
        print(f"[错误] 未找到 {app_js}")
        sys.exit(1)

    extractor = WebpackFileExtractor(code)
    files = extractor.run()

    if not files:
        print("[警告] 未提取到任何文件")
        sys.exit(0)

    with open(js_txt, 'w', encoding='utf-8') as fp:
        fp.write('\n'.join(files))

    print(f"\n[完成] 已保存到 js.txt，共 {len(files)} 条")
    print("=" * 60)
    for i, fn in enumerate(files, 1):
        print(f"  {i:3d}. {fn}")
