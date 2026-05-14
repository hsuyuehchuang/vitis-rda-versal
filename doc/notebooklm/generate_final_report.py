import json
import os
import re

with open("notebooklm_output.json", "r") as f:
    content = f.read()

# Find the first '{' and parse from there
start_idx = content.find('{')
if start_idx == -1:
    print("Could not find JSON payload")
    exit(1)

json_content = content[start_idx:]
data = json.loads(json_content)

# Extract raw answer
answer = data["answer"]

# Add (notebooklm) tags to the generated content headers
answer = answer.replace("## 1. 核心架構解析", "## 1. 核心架構解析 (notebooklm)")
answer = answer.replace("## 2. 異質運算架構", "## 2. 異質運算架構 (notebooklm)")
answer = answer.replace("## 3. 應用案例探討", "## 3. 應用案例探討 (notebooklm)")
answer = answer.replace("## 4. 適用場景與限制限制", "## 4. 適用場景與限制 (notebooklm)")
# Since the title is "# AI Engine Survey 重點報告", let's also add a tag there
answer = answer.replace("# AI Engine Survey 重點報告", "# AI Engine Survey 重點報告 (notebooklm 產生)")

# Add my own AI generated expansion section
claude_expansion = """
---

## 5. 架構演進與技術補充 (Claude 自行補充擴充)

此段落為 AI 助理 (Claude) **在完全沒有依賴 NotebookLM** 的情況下，針對其萃取結果所作的進階技術補充，提供更全面、更高階的工程師視角。

### 5.1 AI Engine vs AI Engine-ML (AIE-ML) 的差異
在 NotebookLM 的結論中提到「AIE 不適合 CNN 推理中的卷積與 ReLU 操作」。這個限制主要適用於第一代配置於 **Versal AI Core (如本筆記本提到的 VCK190)** 上的傳統 AIE。
然而，為了適應當代機器學習的需求，AMD 後續推出了 **Versal AI Edge 系列**，其中搭載了改良版的 **AIE-ML** 架構。AIE-ML 引入了對 INT4/INT8 矩陣運算的原生硬體支援，以及更強大的非線性激勵函數（如 ReLU）硬體加速。因此，在評估架構時，需根據晶片家族精確區分：
*   **AIE (AI Core)**：專攻高精度 DSP、雷達、5G 通訊訊號處理（如本專案的 2D FFT）。
*   **AIE-ML (AI Edge)**：專攻邊緣機器學習、CNN 推理與車載 AI 視覺運算。

### 5.2 開發與除錯的實務挑戰 (AIE Toolchain)
異質運算雖然強大，但開發與除錯門檻極高。NotebookLM 雖整理了 Graph 與 Kernel 模型，但在實際工程實踐中，我們通常需要依賴 **Vitis Analyzer** 與 **AIE Emulator (aiesimulator)**。
*   **死鎖 (Deadlock)**：由於 PLIO/GMIO 依賴硬體的串流背壓 (Backpressure) 機制，若 PL 端 `s2mm` 消耗資料的速度跟不上 AIE，或 `mm2s` 餵食速度有誤，極易導致整個 Tile Array 卡死。這是撰寫 `system.cfg` 連線時，硬體工程師最常卡關的地方，必須頻繁使用 Vitis Analyzer 追蹤 Event trace。
"""

final_content = answer + claude_expansion

with open("test-auto-note.md", "w", encoding="utf-8") as f:
    f.write(final_content)

print("Generated test-auto-note.md successfully.")
