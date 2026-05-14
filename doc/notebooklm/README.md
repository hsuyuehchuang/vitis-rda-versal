# NotebookLM 內容生成流程

這個資料夾把「呼叫 NotebookLM CLI 取得彙整內容 → 用 Claude 補充自己的觀點 → 產出筆記 md 初稿」整條流程包起來。
如果你是 AI agent，讀完本檔就應該知道怎麼幫使用者跑這條流程。

## 資料夾內容

| 檔案 | 用途 |
|---|---|
| `ask_notebooklm.py` | 呼叫 `notebooklm` CLI 詢問問題，存 raw JSON 到 `notebooklm_output.json` |
| `generate_final_report.py` | 讀 raw JSON、清洗、加上 Claude 自己的擴充章節、產出 `test-auto-note.md` |
| `notebooklm_output.json` | 上一次 NotebookLM 回應的快取（會被 `ask_notebooklm.py` 覆寫，可當參考範例） |
| `README.md` | 你正在讀這個 |

## 執行流程

```bash
cd doc/notebooklm/                  # 兩支腳本都用相對路徑開啟 notebooklm_output.json，務必在此資料夾下執行
python3 ask_notebooklm.py           # → 寫入 notebooklm_output.json
python3 generate_final_report.py    # → 讀 notebooklm_output.json，產出 test-auto-note.md
```

跑完後 `test-auto-note.md` 就是最終初稿，使用者可以再人工編輯。

## 客製化要點

兩支腳本都是純 Python（無 dependency），可直接改：

### `ask_notebooklm.py`

- **Notebook ID**：第 6 行 `"-n", "935c676c"` 是 NotebookLM 筆記本 ID。查不同筆記本要改這個
- **問題 prompt**：同行的中文字串就是要問 NotebookLM 的問題
- **CLI 路徑**：寫死 `/home/hsuyueh.chuang/.local/bin/notebooklm`。換機器或不同使用者要改成 `which notebooklm` 的結果
- 出錯時會把 stdout/stderr 也寫進 json，方便事後 debug

### `generate_final_report.py`

- 從 `notebooklm_output.json` 抓 `data["answer"]` 欄位
- 對特定章節 heading 加 `(notebooklm)` 標記，方便讀者區分 NotebookLM 原始內容 vs Claude 補充
- 第 28-45 行的 `claude_expansion` 是 Claude 自行擴充的補充章節；主題換了要重寫這段
- 輸出檔名寫死 `test-auto-note.md`

## 給 AI agent 的判斷準則

當使用者請你「補充」、「擴充」、「加上你自己的觀點」這類請求時，參考 `generate_final_report.py` 第 28-45 行 `claude_expansion` 的寫法：

- 開頭明確標示「在完全沒有依賴外部資料的情況下」做的擴充，跟 NotebookLM 內容做切割
- 章節編號接在 NotebookLM 原始章節之後（避免跟 NotebookLM 重複）
- 補充內容是進階技術視角、業界實務、踩坑經驗，**不是**重複 NotebookLM 已說過的內容
- 用「對照 NotebookLM 提到的 X，這裡補充 Y」的句式，建立兩段內容的邏輯關聯

## 後續：把 md 變成漂亮 HTML

產出 `test-auto-note.md` 後，如果要再轉成互動 HTML，看 `doc/html-template/README.md`。

完整串接：

```bash
# 第一段：notebooklm 流程產出 md
cd doc/notebooklm/
python3 ask_notebooklm.py
python3 generate_final_report.py

# 第二段：套 html-template 把 md 轉成 HTML
cd ../
pandoc notebooklm/test-auto-note.md \
  --from gfm \
  --template=html-template/template.html \
  --toc --toc-depth=3 \
  --standalone \
  --metadata title="AI Engine Survey 重點報告" \
  --metadata glossary=./html-template/glossary.js \
  -o notebooklm/test-auto-note.html
```

注意第二段加了 `--metadata glossary=./html-template/glossary.js`，因為產出的 HTML 不在 html-template/ 同層，預設路徑 `./glossary.js` 找不到。

## 已知限制

- `notebooklm` CLI 是個人安裝的工具（路徑寫死），其他人要跑 `ask_notebooklm.py` 前先確認 CLI 已裝且 PATH 對得到
- `notebooklm_output.json` 會被覆寫，重要結果記得另存
- 輸出檔名 `test-auto-note.md` 是 placeholder，正式使用建議改成有意義的名字
