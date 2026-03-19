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

---

## 使用方法

### 第一步：准备 `app.txt`

1. 用浏览器打开目标站点，按 `F12` 打开开发者工具，切换到 **Sources（源代码）** 面板
2. 找到 Webpack 入口 JS 文件（通常命名为 `app.xxxxxxxx.js` 或 `chunk-vendors.xxxxxxxx.js`）
3. 在 JS 源码中搜索包含 chunk 映射表的代码段（通常是一段形如 `{0:"xxxxx", 1:"xxxxx"}[e]` 的对象），将其复制到项目根目录的 `app.txt` 文件中

`app.txt` 支持以下三种常见格式：

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

### 第二步：准备 `name.txt`（可选）

如果目标站点有部分 JS 文件不在 chunk 映射表中（如 `app.js`、`chunk-vendors.js`），可手动将其文件名写入 `name.txt`，每行一条，格式为 `名称.hash`（不含 `.js` 后缀）：

```
app.663b84e7
chunk-vendors.a1b2c3d4
```

### 第三步：配置请求头（按需）

如果目标站点需要登录态或特定请求头，打开 `js_tiqu.py`，修改顶部的 `HEADERS` 字典：

```python
HEADERS = {
    "User-Agent": "Mozilla/5.0 ...",
    "Cookie": "your_cookie_here",       # 替换为实际 Cookie
    "Referer": "https://target.com/",   # 替换为目标站点地址
    ...
}
```

### 第四步：执行完整工作流

```bash
python extract.py -u http://example.com -p /static/js
```

**参数说明：**

| 参数 | 说明 | 示例 |
|---|---|---|
| `-u` | 目标站点域名（含协议） | `http://example.com` |
| `-p` | JS 文件在服务器上的路径前缀 | `/static/js` |

> 程序会将 `-u` 和 `-p` 拼接为完整 JS 请求地址：`http://example.com/static/js/<名称>.js`

执行完毕后，最终结果输出到 `result.txt`，过滤前的完整结果备份在 `result.txt.bak`。

---

## 单独使用各工具

### `webpack_extractor.py` — 提取 JS 文件名

```bash
# 读取当前目录的 app.txt，输出到 js.txt
python webpack_extractor.py
```

### `js_tiqu.py` — 请求 JS 并提取 API

```bash
python js_tiqu.py -i js.txt -d http://example.com -p /static/js -o result.txt
```

| 参数 | 必填 | 说明 |
|---|---|---|
| `-i` | 是 | 输入文件（JS 文件名列表，如 `js.txt`）|
| `-d` | 是 | 站点域名（含协议，如 `http://example.com`）|
| `-p` | 是 | JS 路径前缀（如 `/static/js`）|
| `-o` | 否 | 输出文件（不指定则打印到终端）|


```bash
# 基本用法：过滤 result.txt 中含 delete/del 的接口，覆盖原文件并备份
python filter_delete_api.py -i result.txt

# 输出到新文件，不覆盖原文件
python filter_delete_api.py -i result.txt -o filtered_result.txt

# 自定义过滤关键字
python filter_delete_api.py -i result.txt -k delete del remove

# 区分大小写
python filter_delete_api.py -i result.txt --case-sensitive

# 不备份原文件
python filter_delete_api.py -i result.txt --no-backup
```

| 参数 | 说明 |
|---|---|
| `-i` | 输入文件路径 |
| `-o` | 输出文件路径（不指定则覆盖原文件）|
| `-k` | 过滤关键字列表（默认：`delete del`）|
| `--case-sensitive` | 区分大小写（默认不区分）|
| `--no-backup` | 不备份原文件（默认会备份为 `.bak`）|

---

## 输入输出文件说明

| 文件 | 来源 | 说明 |
|---|---|---|
| `app.txt` | 手动准备 | Webpack chunk 映射代码 |
| `name.txt` | 手动准备（可选）| 额外 JS 文件名列表 |
| `js.txt` | 自动生成 | 提取的 JS 文件名列表 |
| `result.txt` | 自动生成 | 提取并过滤后的 API 路径列表 |
| `result.txt.bak` | 自动生成 | 过滤前的 API 路径备份 |

---

## 支持的 `app.txt` 格式

`webpack_extractor.py` 支持以下所有常见格式：

| 格式 | id 类型 | hash 长度 | 典型框架 |
|---|---|---|---|
| 字符串key + hex | `chunk-15d1eba8` | 8位 | Vue CLI |
| 数字key + 短hex | `0`, `1`, `2`... | 7~8位 | React CRA |
| 数字key + 长hex | `319`, `409`... | 20位 | Vite |
| 双块（名称+hash）| `npm.ajv`, `atom-sdk` | 8位 | 百度系框架 |

---

## 常见问题

**Q: 提取到的 JS 文件名列表为空（`js.txt` 无内容）？**

检查 `app.txt` 中的代码格式是否符合上述三种格式之一，确保复制的是包含 `{key: "hash"}` 映射对象的完整代码段，而非普通 JS 逻辑代码。

**Q: 请求 JS 文件时全部失败（`[FAIL] 请求失败`）？**

- 确认 `-u` 和 `-p` 参数拼接的完整路径是否可以在浏览器中正常访问
- 如果目标站点需要登录态，修改 `js_tiqu.py` 中的 `HEADERS`，填入有效的 `Cookie`
- 检查是否存在 IP 封锁或频率限制，可适当调大 `js_tiqu.py` 中的 `time.sleep(0.2)` 延迟值

**Q: `result.txt` 中有大量误报路径（非 API 路径）？**

当前正则 `PATH_PATTERN` 会匹配所有 `"/xxx/xxx"` 形式的字符串，部分静态资源路径或无关字符串可能混入结果，需人工筛选或根据实际业务调整正则规则。

**Q: 如何只运行部分步骤？**

直接单独调用对应脚本即可（参见上方「单独使用各工具」章节），各脚本之间通过文件（`js.txt` / `result.txt`）传递数据，彼此独立。
