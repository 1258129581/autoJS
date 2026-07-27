# AutoJS

Automatically extract a list of JS files from a Webpack-bundled frontend project and batch request those JS files to extract API endpoint paths.

## Tool Composition

| File | Description |
|---|---|
| `extract.py` | Main entry point; coordinates the complete workflow |
| `webpack_extractor.py` | Extracts JS filenames from `app.txt` and outputs them to `js.txt` |
| `js_tiqu.py` | Reads `js.txt`, requests each JS file, and extracts API paths |
| `filter_delete_api.py` | Filters out interfaces containing `delete`/`del` keywords from `result.txt` |

## Workflow

```
Prepare app.txt (Webpack entry JS code)
Prepare name.txt (Optional, additional filename list)
          ↓
[Step 0]  name.txt → Pre-write to js.txt
          ↓
[Step 1]  webpack_extractor.py
          Read app.txt → Extract chunk_id.hash → Write to js.txt
          ↓
[Step 2]  js_tiqu.py
          Read js.txt → Construct URL → Request JS → Extract API → Write to result.txt
          ↓
[Step 3]  filter_delete_api.py
          Read result.txt → Filter delete interfaces → Overwrite result.txt
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Usage

### Step 1: Prepare `app.txt`

1. Open the target site in a browser, press `F12` to open Developer Tools, and switch to the **Sources** panel.
2. Find the Webpack entry JS file (usually named `app.xxxxxxxx.js` or `chunk-vendors.xxxxxxxx.js`).
3. Search the JS source code for the code segment containing the chunk mapping table (usually an object shaped like `{0:"xxxxx", 1:"xxxxx"}[e]`) and copy it into the `app.txt` file in the project root directory.

`app.txt` supports the following three common formats:

```javascript
// Format 1: String key + hash (Common in Vue CLI)
{
    "chunk-15d1eba8": "ed145436",
    "chunk-2802b56e": "3d72e33b"
}[t]

// Format 2: Numeric id + hash
{
    0: "ed8a43a",
    1: "bdc373c"
}[e]

// Format 3: Numeric id → Module Name + Numeric id → hash (Dual block)
({213: "npm.ajv", ...}[e] || e) + "." + {213: "2d6fde51", ...}[e]
```

### Step 2: Prepare `name.txt` (Optional)

If some JS files on the target site are not in the chunk mapping table (e.g., `app.js`, `chunk-vendors.js`), you can manually enter their filenames into `name.txt`, one per line, in the format `name.hash` (without the `.js` extension):

```
app.663b84e7
chunk-vendors.a1b2c3d4
```

### Step 3: Configure Request Headers (As Needed)

If the target site requires authentication or specific request headers, open `js_tiqu.py` and modify the `HEADERS` dictionary at the top:

```python
HEADERS = {
    "User-Agent": "Mozilla/5.0 ...",
    "Cookie": "your_cookie_here",       # Replace with actual Cookie
    "Referer": "https://target.com/",   # Replace with target site address
    ...
}
```

### Step 4: Execute Full Workflow

```bash
python extract.py -u http://example.com -p /static/js
```

**Parameter Description:**

| Parameter | Description | Example |
|---|---|---|
| `-u` | Target site domain (including protocol) | `http://example.com` |
| `-p` | Path prefix of JS files on the server | `/static/js` |

> The program will concatenate `-u` and `-p` into a complete JS request URL: `http://example.com/static/js/<name>.js`

After execution, the final results are output to `result.txt`, and a full backup before filtering is stored in `result.txt.bak`.

---

## Individual Tool Usage

### `webpack_extractor.py` — Extract JS Filenames

```bash
# Reads app.txt from current directory and outputs to js.txt
python webpack_extractor.py
```

### `js_tiqu.py` — Request JS and Extract APIs

```bash
python js_tiqu.py -i js.txt -d http://example.com -p /static/js -o result.txt
```

| Parameter | Required | Description |
|---|---|---|
| `-i` | Yes | Input file (List of JS filenames, e.g., `js.txt`) |
| `-d` | Yes | Site domain (Including protocol, e.g., `http://example.com`) |
| `-p` | Yes | JS path prefix (e.g., `/static/js`) |
| `-o` | No | Output file (If not specified, it prints to terminal) |

## Input/Output File Descriptions

| File | Source | Description |
|---|---|---|
| `app.txt` | Manual | Webpack chunk mapping code |
| `name.txt` | Manual (Optional) | Additional JS filename list |
| `js.txt` | Auto-generated | List of extracted JS filenames |
| `result.txt` | Auto-generated | List of extracted and filtered API paths |
| `result.txt.bak` | Auto-generated | Backup of API paths before filtering |

---

## Supported `app.txt` Formats

`webpack_extractor.py` supports all the following common formats:

| Format | ID Type | Hash Length | Typical Framework |
|---|---|---|---|
| String key + hex | `chunk-15d1eba8` | 8 chars | Vue CLI |
| Numeric key + short hex | `0`, `1`, `2`... | 7-8 chars | React CRA |
| Numeric key + long hex | `319`, `409`... | 20 chars | Vite |
| Dual block (Name + Hash) | `npm.ajv`, `atom-sdk` | 8 chars | Baidu-ecosystem frameworks |

---

## FAQ

**Q: The extracted JS filename list is empty (`js.txt` is empty)?**

Check if the code format in `app.txt` matches one of the three formats described above. Ensure you copied the complete code segment containing the `{key: "hash"}` mapping object, not just ordinary JS logic.

**Q: All JS file requests fail (`[FAIL] request failed`)?**

- Confirm if the full path concatenated from `-u` and `-p` can be accessed normally in a browser.
- If the target site requires authentication, modify `HEADERS` in `js_tiqu.py` and enter a valid `Cookie`.
- Check for IP blocking or rate limits; you can increase the `time.sleep(0.2)` delay value in `js_tiqu.py`.

**Q: There are many false positives in `result.txt` (non-API paths)?**

The current `PATH_PATTERN` regex matches all strings in the `"/xxx/xxx"` format. Some static resource paths or irrelevant strings may be mixed into the results; these require manual filtering or adjustments to the regex rules based on the actual business logic.

**Q: How do I run only specific steps?**

You can call the corresponding scripts individually (see the "Individual Tool Usage" section). Data is passed between scripts via files (`js.txt` / `result.txt`), making them independent.
