// Glossary for Versal / AIE / FPGA terms used in hover tooltips.
// Format: { TERM: "白話定義（一句話）" }
// 模板會自動把正文中第一次出現的 term 包成 <span class="term">.
window.GLOSSARY = {
  // 三大區塊
  "PS": "Processing System，Versal 內跑 Linux 的 ARM Cortex-A72 CPU 區塊。",
  "PL": "Programmable Logic，傳統 FPGA fabric，可自訂 datapath 與 I/O 介面。",
  "AIE": "AI Engine，由數百個 VLIW SIMD 微型處理器組成的 2D 計算陣列。",
  "AI Engine": "由數百個 VLIW SIMD 微型處理器組成的 2D 計算陣列，本專案的主角。",

  // 平台 / 晶片 / 板
  "ACAP": "Adaptive Compute Acceleration Platform，自適應運算加速平台，AMD/Xilinx 為強調異質運算特性而創造的名稱。",
  "Versal": "AMD/Xilinx 的 ACAP 晶片家族系列名稱。",
  "VCK190": "Xilinx Versal AI Core 系列評估板，本專案使用的開發板。",
  "XCVC1902": "VCK190 板上的 Versal SoC 晶片型號。",
  "SoC": "System on Chip，把處理器、記憶體、I/O 等整合在單一晶片上的設計。",

  // 介面
  "PLIO": "Programmable Logic I/O，AIE 與 PL 之間的串流介面，低延遲、適合連續資料傳輸。",
  "GMIO": "Global Memory I/O，AIE 直接讀寫 DDR 記憶體的介面，頻寬大、適合巨量 Block 存取。",
  "AXI-MM": "AXI Memory-Mapped，有記憶體位址的隨機存取介面（主要用來接 DDR）。",
  "AXI-Stream": "無位址的純資料流介面（主要用來接 AIE 或 PL 內部流水線）。",

  // 處理器架構
  "VLIW": "Very Long Instruction Word — 一條指令封裝多個運算 slot 同時下發，靠 compiler 安排併行。",
  "SIMD": "Single Instruction, Multiple Data — 一條指令同時對多筆資料運算。",
  "CPU": "Central Processing Unit，通用處理器，什麼都能做但一次一件。",
  "ARM": "ARM 公司設計的 CPU 架構，Versal PS 內整合 ARM Cortex-A72 core。",
  "ARM Cortex-A72": "ARM 設計的 64-bit 應用級 CPU 核心，Versal PS 跑 Linux 的核心。",

  // DSP / 演算法
  "DSP": "Digital Signal Processor / Processing — 數位訊號處理。",
  "FFT": "Fast Fourier Transform — 快速傅立葉轉換，頻譜分析核心演算法。",
  "MAC": "Multiply-Accumulate — 乘加運算，DSP 效能的核心衡量指標。",
  "FIR": "Finite Impulse Response — 有限脈衝響應濾波器。",
  "Twiddle factor": "FFT 演算法中的旋轉因子，用於合併子 FFT 結果。",

  // 軟體 / 工具鏈
  "XRT": "Xilinx Runtime，運行在 PS/Linux 上的軟體 API / runtime，負責載入 xclbin、控制 PL kernel / AIE graph。",
  "HLS": "High-Level Synthesis — 將 C++ 程式碼直接轉譯為 FPGA 硬體電路的技術。",
  "ADF": "Adaptive Data Flow API，用 C++ 描述 AIE graph 拓樸的程式介面。",

  // PL 搬運
  "mm2s": "Memory-Mapped → Stream，PL 從 DDR (AXI-MM) 讀資料轉成 AXI-Stream 餵給 AIE。",
  "s2mm": "Stream → Memory-Mapped，PL 從 AIE 收 AXI-Stream 轉成 AXI-MM 寫回 DDR。",

  // AIE Tile 結構
  "Tile": "AIE 陣列的單一運算格 = 一顆 vector processor + 本地 32KB SRAM + DMA + cascade 介面。",
  "AIE tile": "AIE 陣列的單一運算格 = 一顆 vector processor + 本地 32KB SRAM + DMA + cascade 介面。",
  "Cascade interface": "AIE tile 之間直接傳遞運算結果的硬體連線，不經 memory。",
  "Vector processor": "把 VLIW + SIMD 結合成的小型處理器，一個 cycle 可做大量平行 MAC。",
  "Kernel": "在單一 AIE tile 上執行的計算函式（例如做一次 1024-pt FFT）。",
  "Graph": "用 ADF API 把多個 kernel 用串流連起來的 Dataflow 拓樸。",

  // 編譯產出
  "xclbin": "Xilinx Compute Library Binary，最終要燒到板子上的二進位，包含 PL bitstream + AIE binary + metadata。",
  "BOOT.BIN": "Versal 開機 image，把 firmware + bitstream + Linux + rootfs 通通包進來。",
  "xsa": "eXtensible Shell Archive，v++ --link 把 AIE+PL 拼起來的產物。",
  "libadf.a": "Adaptive Data Flow library，AIE graph 編譯後的靜態 lib。",

  // 板上資源
  "DDR": "Double Data Rate 系統記憶體，本專案資料以 DDR 為中心搬運。",
  "DDR4": "Versal 板上的主要插槽式系統記憶體。",
  "LPDDR4": "Versal 板上焊接式低功耗記憶體。",
  "PCIe": "PCI Express，高速序列介面，可讓 VCK190 作為 PCIe endpoint 加速卡。",
  "FMC": "FPGA Mezzanine Card，PL 端外接 ADC/DAC/感測器的擴充連接器。",
};
