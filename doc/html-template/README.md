# HTML Template — Pandoc-driven Markdown → 互動 HTML

這個資料夾包含把 Markdown 轉換成「美化版互動 HTML」所需的全部素材。
如果你是 AI agent，閱讀完本檔就應該知道怎麼把使用者給你的 `.md` 變成跟
`doc/notes_v2.html` 同等級的 HTML 輸出。

## 資料夾內容

| 檔案 | 用途 |
|---|---|
| `template.html` | Pandoc HTML 模板，定義整個頁面的結構、CSS、JS |
| `glossary.js` | 詞彙庫（hover tooltip 用的術語表），`window.GLOSSARY = {...}` |
| `README.md` | 你正在讀這個 |

## 標準轉換指令

```bash
pandoc INPUT.md \
  --from gfm \
  --template=./html-template/template.html \
  --toc --toc-depth=3 \
  --standalone \
  --metadata title="文件標題" \
  -o OUTPUT.html
```

**重點旗標說明**：

- `--from gfm`：必加。使用者的 md 通常是 GitHub-flavored Markdown 風格（list 前不一定有空行、pipe table 容忍寬鬆），不加 pandoc 的 default markdown 解析會跑掉很多 list 和 table
- `--template=...`：指定本模板
- `--toc --toc-depth=3`：產生章節導覽（h1～h3），會自動放到左側 sticky sidebar
- `--standalone`：包含完整 `<html>` 框架
- `--metadata title="..."`：頂端 topbar + browser tab 顯示用，務必傳；省略 pandoc 會警告且 fallback 用檔名

## 模板自帶的功能

模板套上去就有，使用者不用再做任何事：

| 功能 | 說明 |
|---|---|
| **Dark / Light mode** | 頂端右上 toggle 按鈕，localStorage 記憶選擇 |
| **左側 sticky TOC** | 自動從 `--toc` 接收，捲動時 active 章節高亮、平滑滾動 |
| **頂端閱讀進度條** | 3px 細條跟隨捲動 |
| **詞彙懸停提示 (Glossary)** | 正文中第一次出現的術語（PS/PL/AIE/PLIO/...）會自動包成 hover tooltip。資料來自 `glossary.js` |
| **`<details>` / `<summary>`** | md 可直接寫 `<details><summary>...</summary>...</details>`，模板有對應樣式（圓角卡片 + 旋轉小三角） |
| **程式碼語法高亮** | highlight.js + atom-one-light / atom-one-dark 主題（隨 theme 切換）。md 用 ``` ```cpp ```` 標語言即可 |
| **Inline `<code>` 亮橘色** | 配色：light `#d97706`、dark `#ffa657`（GitHub Dark 風） |
| **Code block 一鍵複製** | 滑鼠 hover 才顯示 copy 按鈕，點了會變 copied |
| **Mermaid** | 已掛載 CDN，md 寫 ` ```mermaid ` 區塊即可渲染 |
| **Print / PDF 友善** | 頂端有 Print 按鈕；列印時隱藏 TOC、進度條、按鈕；details 強制展開以免漏內容 |
| **響應式** | 視窗 ≤ 900px 自動收起 TOC 變單欄 |

## 設定詞彙庫 `glossary.js`

格式：
```js
window.GLOSSARY = {
  "PLIO": "AIE 與 PL 之間的串流介面，低延遲、適合連續資料傳輸。",
  "GMIO": "AIE 直接讀寫 DDR 記憶體的介面，頻寬大、適合巨量 Block 存取。",
  // ...
};
```

規則：
- key 是要 highlight 的字面（短語、單字、縮寫皆可）
- value 是 hover 顯示的一句話定義
- 正文中**第一次**出現該 term 才會被包成 tooltip，避免到處都有底線
- 英文 term 會檢查字界（不會把 `AIE` 切到 `AIEarch`）；中文/混合 term 不檢查
- 同時匹配多個 term 時，較長的優先（避免 `AI Engine` 被 `AIE` 切掉）

## 詞彙庫放哪？

模板預設 `<script src="./glossary.js">`，**相對於產出的 HTML 檔位置**，不是相對於 template.html。

三種放法：

**方法 1（推薦）**：產出 HTML 跟 `glossary.js` 放同一層
```
doc/
├── output.html
└── glossary.js  (從 html-template/ 複製過來或直接放)
```

**方法 2**：產出 HTML 在別處，用 pandoc metadata 指定 glossary 路徑
```bash
pandoc INPUT.md \
  --template=./html-template/template.html \
  --metadata glossary=./html-template/glossary.js \
  ...
```

**方法 3**：產出 HTML 放在 `html-template/` 旁邊（一層）並用相對路徑（本專案的 `notes_v2.html` 就是這樣，腳本路徑改成 `./html-template/glossary.js`）

如果 `glossary.js` 找不到，tooltip 功能會被靜默跳過，其他功能照常運作。

## 給 AI agent 的執行流程

當使用者說「把 XX.md 轉成 HTML」或類似請求，請：

1. **確認 pandoc 可用**：`pandoc --version`，要求 ≥ 2.9。沒有就提示 `apt install pandoc` / `brew install pandoc`
2. **看 md 的內容**：若有大量 `<img>`, code block, table → 模板都能處理；若 md 內含領域特定縮寫 → 提醒使用者要不要加進 `glossary.js`
3. **執行轉換**：用「標準轉換指令」那塊的指令；title 從 md 第一個 `#` 抓或詢問使用者
4. **驗證輸出**：在瀏覽器開啟、檢查 dark mode toggle、TOC、code highlighting 都正常
5. **詞彙庫**：若該文件有大量縮寫術語（例如硬體文件、論文摘要），主動列出建議加入 glossary.js 的 term 給使用者確認

## 已知限制 / 陷阱

- **必加 `--from gfm`**：default markdown 對 list/table 空行的要求嚴格，會把 GitHub 風的 md 解析錯亂
- **`<img src="...">` 路徑**：相對於產出 HTML 位置，不是 md 位置。Pandoc 不會自動改寫，所以 md 內手寫的 `<img>` 標籤要寫成最終 HTML 看得到的路徑
- **Mermaid 區塊 class 名稱**：pandoc 把 ` ```mermaid ` 轉成 `<pre><code class="language-mermaid">`，而模板期待的是 `<div class="mermaid">`。若使用者要用 Mermaid 圖，可能需要 pandoc filter 或手寫 `<div class="mermaid">...</div>` 在 md 裡（pandoc 預設允許 raw HTML）
- **內嵌 iframe / 客製化互動元件**：模板只負責通用框架。文件專屬的互動元素（如本專案 `notes_v2.html` 內的 PS/PL/AIE 互動圖、tile 陣列、檔案搜尋框）需要產出 HTML 後手動 inject，模板不會自動帶出來

## 想看完整實例

`doc/notes_v2.html` 是用此模板生出來的成品，再額外手動 inject 了專案特定的互動元件（A5/B2/B3）。可以參考它的結構來幫使用者做類似的 inject。
