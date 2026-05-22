# Code Map — 開發筆記 + Trace 指南

這份是給自己看的工作手冊：**專案在幹嘛、怎麼讀 code、怎麼開發**。高層次概念與效能數字看 [notes.md](./notes.md)。

---

## 1. 專案在幹嘛

1024×1024 2D FFT on AMD Versal VCK190。資料以 DDR 為中心流動：**PS 指揮 → PL 搬運 (含硬體轉置) → AIE 計算 → PL 搬回 → AIE Row FFT → DDR**。

注意：notes.md 描述的是專案演化過程（README 的 Block 1/2/3 三次 build 結果），**不是任一單一 commit 的程式碼狀態**。讀 code 時要看當下 branch 的 active 配置（見 §3、§4）。

---

## 2. 編譯流程：make targets ↔ Makefile

每個 target 代表一個 build 階段，**階段名稱跟順序在所有 branch 都穩定**；只有「link 哪幾顆 kernel」「host 用哪個 .cpp」會隨 branch 變。

| Target | Makefile 行 | 實際指令 | 產物 |
|---|---|---|---|
| `make aie` | L95-97 | `v++ -c --mode aie ...` | `libadf.a`、`Work/` |
| `make hls` | L109-110 | `$(MAKE) -C hls all` (轉去 [hls/Makefile](../hls/Makefile) 各自呼叫 `v++ -c --mode hls`) | `hls/*/<name>.xo` |
| `make xsa` | L112, 126-127 | `v++ -g -l --platform ...` (link AIE + PL) | `aie_base_graph_hw.xsa` |
| `make host` | L129, 135-136 | `$(MAKE) -C sw/` (cross-compile aarch64) | `host.exe` |
| `make package` | L138, 149-157 | `v++ -p ...` (打包 BOOT.BIN + xclbin + rootfs) | `BOOT.BIN`、`sd_card.img`、`a.xclbin` |
| `make aiesim` | L99-100 | `aiesimulator --pkg-dir=./Work` | x86 模擬 AIE graph |
| `make clean` | L159-163 | `rm -rf` 中間檔 + `$(MAKE) -C sw clean` | — |

**讀 Makefile 抓什麼**：
- 「**XSA link 用哪些 .xo**」→ 看 `${XSA}:` 那行 (L126-127)，前面註解掉的版本是歷史嘗試
- 「**host 用哪個 .cpp**」→ 看 `${HOST_EXE}:` 那行 (L135-136) + [sw/Makefile](../sw/Makefile) 的 `HOST_OBJ`
- 「**PL kernels 怎麼接 AIE**」→ [system.cfg](../system.cfg) 的 `nk=` (宣告) 與 `sc=` (stream connect)

---

## 3. 當下 active 配置 (replica_fft branch)

| 元件 | 當下狀態 |
|---|---|
| XSA link 的 PL kernels | `mm2s` + `s2mm` + `fft_strided_mm2s` (基礎版，無 batch/fan-out) |
| `system.cfg` 連線 | 單一 stream：`mm2s → col_in`、`col_out → s2mm`、`fft_strided_mm2s → row_in` |
| Host 主邏輯 | [sw/host.cpp](../sw/host.cpp) 呼叫 `test_fft_print()` — **debug stub，只印輸入前 10 個元素，不跑 AIE/PL** |
| 完整 pipeline | 目前未啟用，這個 branch 在探索 strided 路線取代 main 的 tile_transpose |

main 上的 active 配置是 `mm2s + s2mm + tile_transpose + tile_s2mm` + host 跑 `fft_acc_mult_twd()`，下面 §4 trace 以 main 為例。

---

## 4. Trace 一筆資料怎麼流 (以 main active config 為例)

跟著一筆 1024×1024 複數矩陣走一遍：

| # | 階段 | 在哪裡 | 在做什麼 |
|---|---|---|---|
| 1 | SD card → DDR | [sw/host.cpp](../sw/host.cpp) L26-29 | `cnpy::npy_load(argv[2])` 讀 `.npy`，取 `complex<float>*` |
| 2 | 載 xclbin | [sw/host.cpp](../sw/host.cpp) L32-33 | `device.load_xclbin()` 把 PL bitstream + AIE binary 燒進去 |
| 3 | 進入 pipeline | [sw/host.cpp](../sw/host.cpp) L38 | 呼叫 `fft_acc_mult_twd(device, uuid, DataInput, ...)` |
| 4 | 配置 buffers | `sw/fft_acc_mult_twd.cpp` (main) | 建 `in_buf` / `row_fft_in_buf` / `out_buf`，`memcpy` 把資料拷進 `in_buf`，`sync(BO_TO_DEVICE)` |
| 5 | 啟動 Col PL | 同上 | `mm2s_0(in_buf, half, 0)` + `mm2s_1(in_buf, half, half)` 兩路餵 DDR→Stream，對應 [hls/mm2s.cpp](../hls/mm2s.cpp) |
| 6 | Col AIE | [aie/graph.cpp](../aie/graph.cpp) L9 → [aie/col_fft_twd_mul_graph.h](../aie/col_fft_twd_mul_graph.h) | `col_fft_twd_mul_rhdl.run(n_iter/(n_paral*n_batch))`：FFT kernel + [aie/twd_mult.cpp](../aie/twd_mult.cpp) 乘旋轉因子 |
| 7 | Col 寫回 DDR | `sw/fft_acc_mult_twd.cpp` | `s2mm_0` / `s2mm_1` 接 AIE Stream 寫回 `row_fft_in_buf`，對應 [hls/s2mm.cpp](../hls/s2mm.cpp) |
| 8 | 等待 + 計時 | 同上 | 各 `.wait()` 後算 Col 階段耗時 |
| 9 | Row 啟動 | 同上 | `sync(BO_TO_DEVICE)` → `tile_transpose_0(row_fft_in_buf, 0)` 做硬體轉置 + 分流成 s0/s1 |
| 10 | Row AIE | [aie/graph.cpp](../aie/graph.cpp) L12 → [aie/row_fft_graph.h](../aie/row_fft_graph.h) | `row_fft_graph_hdl.run(32*16)` 跑 1024-pt FFT |
| 11 | Row 寫回 | `sw/fft_acc_mult_twd.cpp` | `tile_s2mm_0` / `tile_s2mm_1` 接 AIE Stream 寫回 `out_buf` |
| 12 | DDR → host | 同上 | `sync(BO_FROM_DEVICE)` 把結果同步回 PS 端 |
| 13 | host → SD | [sw/host.cpp](../sw/host.cpp) (commented) | `cnpy::npy_save("output.npy", ...)` (test_fft_print 版本沒做這步) |
| 14 | 驗證 | [verify/verify_output.py](../verify/verify_output.py) | 與 `numpy.fft.fft2` 對 MSE，目標 < 1e-7 |

**Stream 連線怎麼對應 `xrt::kernel(...)` 字串**：
- host 呼叫 `xrt::kernel(device, uuid, "mm2s:{mm2s_0}")` 對應 [system.cfg](../system.cfg) 的 `nk = mm2s:2:mm2s_0,mm2s_1`
- AIE graph 的 PLIO port 名稱（如 `col_fft_twd_mul_in_0`）由 graph C++ 宣告，在 system.cfg 用 `sc =` 連到 PL kernel 的 stream port (`mm2s_0.s`)

---

## 5. 自撰原始碼清單

### 5.1 根目錄設定
| 檔案 | 角色 | 在做什麼 |
|---|---|---|
| [Makefile](../Makefile) | 編譯主控 | 階段 target 定義 (見 §2) |
| [system.cfg](../system.cfg) | PL ↔ AIE 接線圖 | V++ Linker 語法，宣告 PL kernel (`nk=`) 與 stream 連線 (`sc=`) |
| [aie_constraints.json](../aie_constraints.json) | AIE Tile 擺放約束 | 手動指定 kernel 映射到的 Tile 座標，避免工具亂擺 |

### 5.2 AIE (`aie/`)
| 檔案 | 角色 | 在做什麼 |
|---|---|---|
| [graph.cpp](../aie/graph.cpp) | 頂層 ADF Graph 進入點 | 實例化 `ColFftTwdMulGraph` + `RowFftGraph` (注意：實例名是 `ReplicaColProcGraphTest` / `ReplicaRowProcGraph`，host 端 `xrt::graph` 字串要對應) |
| [col_fft_twd_mul_graph.h](../aie/col_fft_twd_mul_graph.h) | Col FFT 拓樸 | 1024-pt FFT kernel + twiddle 乘法 kernel 串接 |
| [row_fft_graph.h](../aie/row_fft_graph.h) | Row FFT 拓樸 | 1024-pt FFT kernel，輸出走 GMIO 或 PLIO (視配置) |
| [sub_fft_par.h](../aie/sub_fft_par.h) | 編譯期參數 | `N_PARAL` (空間平行)、`N_BATCH_FFT` (時間批次) |
| [kernel.h](../aie/kernel.h) | Kernel 介面原型 | 函式宣告 + ping-pong window size |
| [twd_mult.cpp](../aie/twd_mult.cpp) | Twiddle 乘法 kernel | SIMD 指令做 Cooley-Tukey 旋轉因子相乘 |
| [twd_factor_table.h](../aie/twd_factor_table.h) | Twiddle LUT | 預算好的 1024 點複數常數表 (由 [verify/gen_init_twd_factor_table.py](../verify/gen_init_twd_factor_table.py) 產生) |
| [widget_distributer.cpp](../aie/widget_distributer.cpp) / [widget_collector.cpp](../aie/widget_collector.cpp) | AIE 內分/合流橋接 | `N_PARAL > 1` 時用 |

### 5.3 PL HLS (`hls/`)
| 檔案 | 角色 | 在 Makefile 狀態 |
|---|---|---|
| [mm2s.cpp](../hls/mm2s.cpp) | DDR → Stream 基礎搬運 | **active** (main + replica_fft 都用) |
| [s2mm.cpp](../hls/s2mm.cpp) | Stream → DDR 基礎搬運 | **active** (兩 branch 都用) |
| [fft_strided_mm2s.cpp](../hls/fft_strided_mm2s.cpp) | 位址跳躍式讀 + 即時轉置 | **active** (replica_fft) |
| [fft_strided_mm2s_bat.cpp](../hls/fft_strided_mm2s_bat.cpp) | + Batching | archived (兩 branch 都註解) |
| [fft_strided_mm2s_bat_fan_out.cpp](../hls/fft_strided_mm2s_bat_fan_out.cpp) | + 4 路 fan-out | archived (從未成功 active 過) |
| [fft_strided_s2mm.cpp](../hls/fft_strided_s2mm.cpp) | 跳躍式寫回 | archived |
| `tile_transpose.cpp` / `tile_s2mm.cpp` | tile-based 轉置與寫回 | **active on main**，replica_fft 上已移除 |
| [uram_controller.cpp](../hls/uram_controller.cpp) / [.h](../hls/uram_controller.h) | UltraRAM 控制器 | 實驗中 |

> 每個 `.cpp` 配一個 `.cfg` 告訴 `v++ -c --mode hls` 頂層函式名稱與輸出格式。

### 5.4 PS Host (`sw/`)
| 檔案 | 角色 | 在做什麼 |
|---|---|---|
| [host.cpp](../sw/host.cpp) | 進入點 | 讀 `.npy` → load xclbin → 呼叫某個 pipeline 函式 (見 sw/Makefile `HOST_OBJ` 決定哪個 active) |
| `fft_acc_mult_twd.cpp` | 完整 2-paral pipeline | **active on main**：Col (mm2s×2 → AIE → s2mm×2) + Row (tile_transpose → AIE → tile_s2mm×2) |
| `fft_dds_twd.cpp` | 早期 DDS 版本 | archived |
| `uram_ctrl.cpp` | UltraRAM 路線實驗 | archived |
| [test_fft_print.cpp](../sw/test_fft_print.cpp) | Debug stub | **active on replica_fft**：只印輸入前 10 個元素 |
| [aie_control_xrt.cpp](../sw/aie_control_xrt.cpp) | AIE 控制橋接 | 工具產生後手工微調，控制 graph 的 run/wait/end |
| [fix_aie_control_xrt.sh](../sw/fix_aie_control_xrt.sh) | 編譯修復腳本 | 修 header 路徑相容性 |

### 5.5 驗證 (`verify/`)
| 檔案 | 角色 | 在做什麼 |
|---|---|---|
| [verify_output.py](../verify/verify_output.py) | Golden Ref 驗證 | 與 `numpy.fft.fft2` 比 MSE (目標 < 1e-7) |
| [gen_init_twd_factor_table.py](../verify/gen_init_twd_factor_table.py) | Twiddle 表產生器 | 編譯前產生 [aie/twd_factor_table.h](../aie/twd_factor_table.h) |

---

## 6. 開發常見場景

| 想做什麼 | 改哪裡 | 注意事項 |
|---|---|---|
| 調 AIE 平行度/批次數 | [aie/sub_fft_par.h](../aie/sub_fft_par.h) 的 `N_PARAL` / `N_BATCH_FFT` | PL 端若有 batch 參數要同步 (例如 `fft_strided_mm2s_bat_fan_out.cpp` 的 `N_BATCH`) |
| 改 Tile 物理位置 | [aie_constraints.json](../aie_constraints.json) | 改完要重 `make aie` |
| 換 link 的 PL kernel 組合 | Makefile L126-127 (XSA 依賴) + [hls/Makefile](../hls/Makefile) (`all:` target) + [system.cfg](../system.cfg) (`nk=` + `sc=`) | 三處要同步，少改一處 link 會出錯 |
| 換 host 主邏輯 | [sw/Makefile](../sw/Makefile) `HOST_OBJ` + [sw/host.cpp](../sw/host.cpp) 末段 `auto output = XXX(...)` | host 端 `xrt::kernel(..., "name:{inst}")` 字串必須對應 system.cfg 的 `nk=` 宣告 |
| 新增 PL kernel | `hls/` 加 `<name>.cpp` + `<name>.cfg` → [hls/Makefile](../hls/Makefile) 加 target → Makefile 加進 `${XSA}` 依賴 → system.cfg 加 `nk=` + `sc=` | |
| 跑 AIE x86 模擬 | `make aiesim`，看 `aie/graph.cpp` 的 `__AIESIM__` main | 不需要硬體，速度快，用於驗 graph 行為 |
| 跑 HW emulation | Makefile 改 `TARGET = hw_emu` (L5) → `make all` → `./launch_hw_emu.sh` | 用 QEMU 模擬完整系統，慢但接近真實 |
| 燒板執行 | `make all` (TARGET=hw) → `sd_card.img` 燒進 SD → 插板 boot → `./host.exe a.xclbin data_rx_1024_complex_64.npy` | |

---

## 7. 一鍵清理
| 想清什麼 | 指令 |
|---|---|
| Makefile 認識的中間檔 | `make clean` |
| 所有 gitignore 列的東西 | `git clean -fdX` |
| 先 dry-run 看會清什麼 | `git clean -ndX` |

> `git clean -fdX` 會殺 `verify/data_rx_1024_complex_64.npy` (8 MB 測試資料)，先備份。
