# vitis-rda-versal 專案 High-level 筆記

> 目標：~10 分鐘 high-level 講解 — AI Engine 是什麼、這個專案在幹麻、PS/PL/AIE 三層怎麼協作。
> 報告對象：對 Versal 不熟的同學/同事。
> 範圍：以 AI Engine 為主軸，PS 跟 PL 當輔助角色講。

---

## 1. Quick summary

<img src="./Xilinx-Versal-VCK190.png" alt="Xilinx Versal VCK190 Evaluation Board" width="500" />

> **這個專案是「在 Xilinx Versal VCK190 上用 AI Engine 加速 1024 × 1024 二維 FFT」的範例設計**，搭配 PL (FPGA) 端的 HLS data movers 跟 PS (ARM CPU) 端的 host 程式做完整的 end-to-end pipeline。

**講者話術**：
> 簡單講，這個專案就是把一張 1024×1024 的複數矩陣丟到 Versal 板子上做 2D FFT，AI Engine 負責算、FPGA 負責搬資料、ARM CPU 負責指揮。

---

## 2. 什麼是 Versal？ 什麼是 AI Engine？

### 「Versal」是什麼

**Versal 是 AMD/Xilinx 的一個產品線品牌名稱**，不是技術或架構本身。階層拆解：

| 層級 | 名稱 | 是什麼 |
|---|---|---|
| 公司 | **AMD**（2022 併購前是 **Xilinx**） | 廠商 |
| 技術類別 | **ACAP** (Adaptive Compute Acceleration Platform) | 「CPU + FPGA + AIE 混合 SoC」這種類別的統稱 |
| 產品線品牌 | **Versal** | AMD 把這類 ACAP 晶片包裝成的商品系列名稱 |
| 子系列 | Versal **AI Core** / AI Edge / Prime / Premium / HBM | 同系列下針對不同應用的版本 |
| 具體晶片 | **XCVC1902** | 屬於 AI Core 子系列的一顆型號 |
| 評估板 | **VCK190** | 把 XCVC1902 焊在板子上、加 DDR/PCIe/USB 等周邊的開發板 |

> **VCK190 開發板**，上面有一顆 **XCVC1902** 晶片，這顆晶片屬於 **Versal AI Core** 子系列，整個 **Versal** 系列底下都是 **ACAP** 架構的產品，由 **AMD/Xilinx** 推出。

> **類比**：就像 Apple → Mac → MacBook Pro → M3 Max 晶片這種層級關係。**Versal** 就是「Mac」這一層的品牌名。

### Versal ACAP 三合一架構

**Versal** 不是傳統 FPGA，是 AMD/Xilinx 的 **ACAP (Adaptive Compute Acceleration Platform)**，一顆 SoC 裡同時塞了三種運算資源：

| 層 | 縮寫 | 內容 | 適合做的事 |
|---|---|---|---|
| Processing System | **PS** | ARM Cortex-A72 (Linux runs here) | 控制流程、I/O、調度 |
| Programmable Logic | **PL** | 傳統 FPGA fabric | 自定義 datapath、I/O 介面、bit-level operation |
| AI Engine | **AIE** | VLIW SIMD vector processor array | 高吞吐、規律性、可向量化的運算 |

### AI Engine 到底是什麼？

**AIE = 一個 array of VLIW SIMD vector processors**。在 VCK190 上有大約 **400 個 tiles**，物理上排成 2D 陣列。先把上面這些專有名詞攤開：

| 名詞 | 是什麼 | 比喻 / 備註 |
|---|---|---|
| **CPU** | Central Processing Unit，通用處理器 | 像家裡的管家，什麼都做但一次一件 |
| **ARM Cortex-A72** | ARM 公司設計的 64-bit 應用級 CPU 核心。Versal **PS** 那層跑 Linux 用的就是這顆 | 跟手機 / Raspberry Pi 4 同等級的 CPU |
| **SIMD** | Single Instruction, Multiple Data — 一條指令同時對多筆資料運算 | 「一聲令下，全班同時做伏地挺身」 |
| **VLIW** | Very Long Instruction Word — 一條指令封裝多個運算 slot 同時下發，靠 compiler 排併行 | 「一張菜單同時點好幾道菜」 |
| **Vector processor** | 把 VLIW + SIMD 結合成的小型處理器，一個 cycle 做大量平行 MAC | 一顆超專業 DSP |
| **Vector processor array** | 上述 vector processor 複製幾百顆排成 2D grid，相鄰可直接串流通訊 | 一整個工廠流水線 |
| **AIE tile** | array 裡的「一格」= 一顆 vector processor + 周邊（往下展開） | 工廠裡的一個工位 |
| ├ **Vector unit** | tile 內做 SIMD 平行運算的部分，1 cycle 可做多個 MAC（e.g. 32× int16 / cycle） | 工位的雙手，一次抓很多顆 |
| ├ **Scalar unit** | tile 內處理 control flow（if / loop / 分支）的部分 | 工位的腦袋，做判斷 |
| ├ **Local memory** | tile 內 32 KB SRAM，極低延遲（單 cycle 存取） | 工位旁邊的小櫃子 |
| ├ **DMA engine** | tile 內負責搬資料到鄰居 tile / PL / DDR 的硬體 | 工位的機械搬運手臂 |
| └ **Cascade interface** | 直接把運算結果送隔壁 tile，不經 memory | 工位之間的傳送帶 |

> **記憶點**：AIE 不是 GPU、也不是 NPU，它比較像「一群可程式化的 DSP，用 dataflow 方式串起來」。

### AIE 適合 vs 不適合做什麼

| 適合 ✅ | 不適合 ❌ |
|---|---|
| FFT / FIR / 矩陣乘法 | 高度 control-flow 的程式 |
| CNN inference (卷積、ReLU) | 不規則記憶體存取 |
| Beamforming、雷達 baseband | 需要 OS、syscall |
| 任何 streaming + 向量化的 DSP | 極低延遲 single-shot 任務 |

### AIE 的程式模型

兩層概念：

1. **Kernel (C++)** — 一個 tile 上跑的計算函式，例如「做一次 1024-pt FFT」
2. **Graph (ADF API)** — 把多個 kernel 用 stream 連起來的 dataflow 圖

寫完之後 **AIE compiler (aiecompiler)** 會：把 kernel 映射到實體 tile、規劃 routing、產 ELF、跟 PL/PS 介面對接。

---

## 3. 這個專案的三層 Hierarchy （主軸）

### 資料流程圖

```
                ┌─────────────────────────────────────────┐
                │  PS (ARM A72, Linux)                    │
                │  sw/host.cpp                            │
                │  - load .xclbin                         │
                │  - 透過 XRT 控 AIE graph & PL kernels    │
                │  - 用 cnpy 讀 .npy 輸入                  │
                └────────────────┬────────────────────────┘
                                 │ (control via XRT)
                                 ▼
   ┌─────────────────────────────────────────────────────────────┐
   │                    PL (FPGA fabric)                         │
   │                                                             │
   │   ┌──────┐   AXI-Stream   ┌──────────────────┐  AXI-Stream  │
   │   │ mm2s ├────────────────┤   AIE: Col FFT   ├──────────────┤
   │   └──────┘    (PLIO)      │  + Twd Mult      │   (PLIO)     │
   │      ▲                    └──────────────────┘      │       │
   │      │                                              ▼       │
   │      │                                          ┌──────┐    │
   │      │                                          │ s2mm │    │
   │      │                                          └───┬──┘    │
   │      │                                              │       │
   │   ┌──┴──┐  AXI-MM                                   │       │
   │   │ DDR │◄────────────────────────────────────────────      │
   │   └──┬──┘  (intermediate after col FFT)                     │
   │      │                                                      │
   │      │ AXI-MM (transpose access)                            │
   │      ▼                                                      │
   │   ┌───────────────────┐   PLIO    ┌──────────────────┐      │
   │   │ fft_strided_mm2s  ├───────────┤   AIE: Row FFT   │      │
   │   └───────────────────┘           └─────────┬────────┘      │
   │                                             │ GMIO          │
   │                                             ▼               │
   │                                          ┌─────┐            │
   │                                          │ DDR │  (final)   │
   │                                          └─────┘            │
   └─────────────────────────────────────────────────────────────┘
```

### 三層各司其職

| 層 | 主要檔案 | 在做的事 |
|---|---|---|
| **PS** | [sw/host.cpp](../sw/host.cpp), [sw/aie_control_xrt.cpp](../sw/aie_control_xrt.cpp) | 載入 `.xclbin`、用 `cnpy` 讀 `.npy` 輸入、靠 XRT API 控 AIE graph 跟 PL kernel；本質是個指揮者 |
| **PL** | [hls/mm2s.cpp](../hls/mm2s.cpp), [hls/s2mm.cpp](../hls/s2mm.cpp), [hls/fft_strided_mm2s.cpp](../hls/fft_strided_mm2s.cpp) | DDR ↔ AIE 之間的搬運工。`mm2s` = 從 DDR 流到 AIE；`s2mm` = 從 AIE 流回 DDR；`fft_strided_mm2s` 多了一個 trick：用 strided 地址做「邊搬邊轉置」 |
| **AIE** | [aie/graph.cpp](../aie/graph.cpp), [aie/col_fft_twd_mul_graph.h](../aie/col_fft_twd_mul_graph.h), [aie/row_fft_graph.h](../aie/row_fft_graph.h) | 真正算 FFT 的地方 |
| **黏合層** | [system.cfg](../system.cfg) | 宣告「PL kernel 的哪個 port 接到 AIE graph 的哪個 port」，是整個系統的接線圖 |

### `mm2s` / `s2mm` 縮寫解釋

這兩個術語在 Xilinx 生態圈很常見，但對新人很容易卡住：

| 縮寫 | 全名 | 方向 |
|---|---|---|
| **mm2s** | **Memory-Mapped → Stream** | DDR (AXI-MM) 讀資料 → 轉成 AXI-Stream 餵給 AIE |
| **s2mm** | **Stream → Memory-Mapped** | 從 AIE 收 AXI-Stream → 寫回 DDR (AXI-MM) |

背後是兩種 AXI 介面：

- **AXI-MM (Memory-Mapped)** = 有位址的隨機存取介面，用來接 DDR
- **AXI-Stream** = 無位址、純資料流，用來接 AIE 或 PL 內部 pipeline

> 一句話：這兩個 PL kernel 的本質就是「**AXI 介面轉接器**」 — 一邊接 DDR、一邊接 AIE，中間做格式轉換跟流量控制。

### 以「1024 × 1024 complex matrix 2D FFT」為例，三層具體動作

| 層 | 角色 | 具體任務（按執行順序） |
|---|---|---|
| **PS** (ARM A72) | **指揮中心** | 1. Linux boot 起來後，跑 `host.exe`<br>2. 用 cnpy 從 SD card 讀進 1024 × 1024 個 cfloat（共 8 MB）→ DDR<br>3. 配置 DDR buffer：input / column FFT 中間結果 / 最終 output<br>4. 透過 XRT 載入 `.xclbin`（內含 PL bitstream + AIE binary）<br>5. `xrt::graph::run()` 啟動 AIE graph<br>6. 迴圈 1024 次：每次觸發一個 column FFT pipeline<br>7. 再迴圈 1024 次：每次觸發一個 row FFT pipeline<br>8. 等所有 kernel 完成 → 把 output 寫回 SD card 給 Python 驗證 |
| **PL** (FPGA fabric) | **搬運專員** | 1. `mm2s`：從 DDR 抓一個 column（1024 cfloat = 8 KB）→ 透過 PLIO 串流給 AIE<br>2. `s2mm`：接住 AIE 算完的 column FFT × twiddle 結果 → 寫回 DDR 暫存<br>3. `fft_strided_mm2s`：用 stride = 1024 的位址模式「跳著讀」DDR，等於邊讀邊把中間矩陣轉置 → 串流給 AIE 做 row FFT<br>4. （Row 階段 AIE 直接用 GMIO 寫 DDR，跳過 PL） |
| **AIE** | **計算引擎** | 1. **Column 階段** ([ColFftTwdMulGraph](../aie/col_fft_twd_mul_graph.h))：收 1024 cfloat → 跑 1024-pt FFT → 乘 twiddle factor W^(kn) → 輸出（重複 1024 次）<br>2. **Row 階段** ([RowFftGraph](../aie/row_fft_graph.h))：收 1024 cfloat → 跑 1024-pt FFT → 輸出（重複 1024 次）<br>3. Column 跟 row 階段各佔自己的一塊 tile region（[aie_constraints.json](../aie_constraints.json)），有條件時可以 pipeline 重疊 |

> **一句話速記**：**PS 下命令、PL 搬資料、AIE 算數學**。資料一進一出走 PS→PL→AIE→PL→DDR→PL→AIE→DDR 這條路。

---

## 4. AI Engine 內部架構（深入）

### 演算法：Cooley-Tukey 2D FFT 分解

二維 FFT 可以拆成「先做 column 1D FFT → 乘 twiddle factor → 再做 row 1D FFT」。這個專案就是直接照這個結構切兩個 AIE graph：

```
原始 1024×1024 矩陣
   │
   ▼  for each column:
[ Column 1024-pt FFT ]
   │
   ▼  element-wise multiply
[ Twiddle Factor W^(kn) ]
   │
   ▼  for each row:
[ Row 1024-pt FFT ]
   │
   ▼
最終 2D FFT 結果
```

### ColFftTwdMulGraph — Column 階段

檔案：[aie/col_fft_twd_mul_graph.h](../aie/col_fft_twd_mul_graph.h)

- **輸入**：PLIO 64-bit（從 PL 的 `mm2s` kernel）
- **第一階段**：1024-pt DIT (Decimation-In-Time) FFT — 直接用 Xilinx DSP Library 的 FFT IP
- **第二階段**：Twiddle factor multiplication，由自寫 kernel 完成
  - [aie/twd_mult.cpp](../aie/twd_mult.cpp) — twiddle 相乘
  - [aie/twd_factor_acc.cpp](../aie/twd_factor_acc.cpp) — twiddle 累積（預先算好的 rotation table）
  - [aie/twd_factor_inc.cpp](../aie/twd_factor_inc.cpp) — 增量式 twiddle
- **輸出**：PLIO 64-bit（送到 PL 的 `s2mm` 寫回 DDR）

### RowFftGraph — Row 階段

檔案：[aie/row_fft_graph.h](../aie/row_fft_graph.h)

- **輸入**：PLIO 64-bit（從 `fft_strided_mm2s`，已轉置）
- **計算**：又一次 1024-pt FFT
- **輸出**：**GMIO** 256-bit — 直接寫 DDR，不再經由 PL kernel

> **PLIO vs GMIO**：
> - **PLIO** = AIE 跟 PL fabric 之間的 streaming 介面（窄、低延遲）
> - **GMIO** = AIE 直接讀寫 global memory (DDR) 的介面（寬、適合 burst）

### 編譯期參數

檔案：[aie/sub_fft_par.h](../aie/sub_fft_par.h)

- `FFT_SIZE = 1024`
- 資料型別：`cfloat` (complex float)
- `N_BATCH_FFT` — 一個 kernel 一次處理幾個 FFT（batching）
- `N_PARAL` — 平行幾條 pipeline（parallelism）

> 這條 branch `replica_fft` 主要在調這兩個旋鈕 + 驗硬體模擬。

### Tile Placement — AIE 是物理 array

檔案：[aie_constraints.json](../aie_constraints.json)

- **Column FFT graph** → tile (24, 0) – (27, 2)
- **Row FFT graph** → tile (24, 3) – (27, 4)

> 報告時可以強調：AIE 不是邏輯 thread pool，是物理 grid，**kernel 擺哪個 tile 會直接影響繞線、頻寬、相鄰 tile 的 cascade 是否能用**。所以 placement 是優化重點。

### Widget Kernels — 流量分配/合流

當 `N_PARAL > 1` 時需要把 stream 拆成多份送進多條 pipeline、再合回來：

- [aie/widget_distributer.cpp](../aie/widget_distributer.cpp) — 拆 stream
- [aie/widget_collector.cpp](../aie/widget_collector.cpp) — 合 stream

> 這是 AIE 設計裡很常見的 pattern：「橋接 kernel」，本身不做計算，只搬資料順序。

---

## 5. Build & Run Flow

主控 [Makefile](../Makefile) 的主要 targets：

| 指令 | 在做什麼 | 產物 |
|---|---|---|
| `make aie` | 用 AIE compiler 編 graph | `libadf.a`、`Work/` |
| `make hls` | 把 HLS kernel 編成 `.xo` | `mm2s.xo`、`s2mm.xo` 等 |
| `make xsa` | `v++ --link` 把 AIE + PL 拼起來 | `.xsa` (hardware design archive) |
| `make host` | aarch64 cross-compile | `host.exe` (ARM 執行檔) |
| `make package` | 打包成 SD card image | `BOOT.BIN` + rootfs + xclbin |
| `make aiesim` | 跑 AIE 模擬器 | 驗證 graph 行為 |
| Hardware emulation | QEMU + AIE 模擬 | 驗證整個系統行為 |

最後流程：把 SD card 插到 VCK190 板子 → boot Linux → 跑 `host.exe` → 結果寫回 DDR → 拷回主機用 [verify/verify_output.py](../verify/verify_output.py) 對 ground truth。

---

## 6. 一句話收尾

> **這個專案是「用 AIE 加速 DSP 演算法」的教科書級例子**。看懂它，就能掌握：
> 1. Versal 三層 (PS / PL / AIE) 怎麼分工
> 2. AIE kernel 跟 graph 的寫法
> 3. PLIO vs GMIO 兩種介面什麼時候用哪個
> 4. Tile placement、parallelism、batching 這些優化旋鈕怎麼轉

---

## 附錄：關鍵檔案速查表

| 角色 | 路徑 |
|---|---|
| 專案總入口 | [Makefile](../Makefile), [system.cfg](../system.cfg) |
| AIE 頂層 graph 實例化 | [aie/graph.cpp](../aie/graph.cpp) |
| AIE column graph 定義 | [aie/col_fft_twd_mul_graph.h](../aie/col_fft_twd_mul_graph.h) |
| AIE row graph 定義 | [aie/row_fft_graph.h](../aie/row_fft_graph.h) |
| AIE 編譯期參數 | [aie/sub_fft_par.h](../aie/sub_fft_par.h) |
| AIE tile placement | [aie_constraints.json](../aie_constraints.json) |
| PL data movers | [hls/mm2s.cpp](../hls/mm2s.cpp), [hls/s2mm.cpp](../hls/s2mm.cpp), [hls/fft_strided_mm2s.cpp](../hls/fft_strided_mm2s.cpp) |
| PS host 應用 | [sw/host.cpp](../sw/host.cpp), [sw/aie_control_xrt.cpp](../sw/aie_control_xrt.cpp) |
| 結果驗證腳本 | [verify/verify_output.py](../verify/verify_output.py) |
