# JS API 提取工具套件

从 Webpack 打包的前端项目中自动提取 JS 文件列表，并批量请求 JS 文件提取其中的 API 接口路径。

## 工具组成

| 文件 | 说明 |
|---|---|
| `extract.py` | 主入口，串联完整工作流 |
| `webpack_extractor.py` | 从 `app.txt` 提取 JS 文件名，输出到 `js.txt` |
| `js_tiqu.py` | 读取 `js.txt`，逐一请求 JS 文件并提取 API 路径 |
| `filter_delete_api.py` | 过滤 `result.txt` 中包含 delete/del 关键字的接口 |

## 工作流程

```
准备 app.txt（Webpack 入口 JS 代码）
准备 name.txt（可选，额外的文件名列表）
          ↓
[步骤 0]  name.txt → 预写入 js.txt
          ↓
[步骤 1]  webpack_extractor.py
          读取 app.txt → 提取 chunk_id.hash → 写入 js.txt
          ↓
[步骤 2]  js_tiqu.py
          读取 js.txt → 拼接 URL → 请求 JS → 提取 API → 写入 result.txt
          ↓
[步骤 3]  filter_delete_api.py
          读取 result.txt → 过滤删除接口 → 覆盖 result.txt
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 准备工作

1. 打开目标站点，找到 Webpack 入口 JS 文件（通常为 `app.js` 或 `chunk-vendors.js`）
2. 将其中包含 chunk 映射表的代码片段复制到 `app.txt`，格式如下：

```javascript
// 格式一：字符串 key + hash（Vue CLI 常见）
{
    "chunk-15d1eba8": "ed145436",
    "chunk-2802b56e": "3d72e33b"
}[t]

// 格式二：数字 id + hash
{
    0: "ed8a43a",
    1: "bdc373c"
}[e]

// 格式三：数字 id → 模块名 + 数字 id → hash（双块）
({213: "npm.ajv", ...}[e] || e) + "." + {213: "2d6fde51", ...}[e]
```

3. （可选）将额外的 JS 文件名写入 `name.txt`，每行一条，格式为 `名称.hash`：

```
app.663b84e7
chunk-vendors.a1b2c3d4
```

### 执行

```bash
python extract.py -u http://example.com -p /static/js
```

**参数说明：**

| 参数 | 说明 | 示例 |
|---|---|---|
| `-u` | 站点域名 | `http://example.com` |
| `-p` | JS 文件路径前缀 | `/static/js` |

> 程序会将 `-u` 和 `-p` 拼接为完整 JS 地址：`http://example.com/static/js/<名称>.js`

## 单独使用各工具

### webpack_extractor.py

```bash
# 直接运行，读取当前目录的 app.txt，输出到 js.txt
python webpack_extractor.py
```

### js_tiqu.py

```bash
python js_tiqu.py -i js.txt -d http://example.com -p /static/js -o result.txt
```

| 参数 | 说明 |
|---|---|
| `-i` | 输入文件（JS 文件名列表）|
| `-d` | 站点域名 |
| `-p` | JS 路径前缀 |
| `-o` | 输出文件（不指定则打印到终端）|

### filter_delete_api.py

```bash
python filter_delete_api.py -i result.txt
```

## 输入输出文件说明

| 文件 | 说明 |
|---|---|
| `app.txt` | Webpack chunk 映射代码（手动准备）|
| `name.txt` | 额外 JS 文件名列表（可选）|
| `js.txt` | 提取的 JS 文件名列表（自动生成）|
| `result.txt` | 提取并过滤后的 API 路径列表（自动生成）|
| `result.txt.bak` | 过滤前的 API 路径备份（自动生成）|

## 支持的 app.txt 格式

`webpack_extractor.py` 支持以下所有常见格式：

| 格式 | id 类型 | hash 长度 | 典型框架 |
|---|---|---|---|
| 字符串key + hex | `chunk-15d1eba8` | 8位 | Vue CLI |
| 数字key + 短hex | `0`, `1`, `2`... | 7~8位 | React CRA |
| 数字key + 长hex | `319`, `409`... | 20位 | Vite |
| 双块（名称+hash）| `npm.ajv`, `atom-sdk` | 8位 | 百度系框架 |

