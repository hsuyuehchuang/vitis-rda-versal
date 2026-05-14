import re

def main():
    with open('notes.md', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Replace dataflow.svg with iframe
    dataflow_html = """<noscript>
  <img src="./dataflow.svg" alt="2D FFT dataflow static diagram" width="900" />
</noscript>
<section class="dataflow-embed" aria-label="互動式 2D FFT 資料流圖">
  <iframe src="./dataflow.html" title="互動式 2D FFT 資料流圖" loading="lazy"></iframe>
</section>"""
    content = re.sub(
        r'<img src="\./dataflow\.svg" alt="2D FFT dataflow static diagram" width="900" />',
        dataflow_html,
        content
    )

    # 2. Add Layer Explorer
    layer_html = """
<div class="layer-explorer">
  <div class="layer-blocks">
    <button class="layer-block active" data-layer="ps"><span class="layer-icon">PS</span><div class="layer-meta"><span class="layer-name">Processing System</span><span class="layer-role">指揮中心</span></div></button>
    <button class="layer-block" data-layer="pl"><span class="layer-icon">PL</span><div class="layer-meta"><span class="layer-name">Programmable Logic</span><span class="layer-role">搬運專員</span></div></button>
    <button class="layer-block" data-layer="aie"><span class="layer-icon">AIE</span><div class="layer-meta"><span class="layer-name">AI Engine</span><span class="layer-role">計算引擎</span></div></button>
    <button class="layer-block" data-layer="sys"><span class="layer-icon">SYS</span><div class="layer-meta"><span class="layer-name">System Config</span><span class="layer-role">總接線圖</span></div></button>
  </div>
  <div id="layer-panel" class="layer-panel"></div>
</div>
"""
    if "layer-explorer" not in content:
        content = content.replace(
            "在這個 2D FFT 的案例中，清楚展示了 PS、PL 與 AIE 是如何完美分工的。以下為三層的具體角色與對應的原始碼檔案：\n",
            "在這個 2D FFT 的案例中，清楚展示了 PS、PL 與 AIE 是如何完美分工的。以下為三層的具體角色與對應的原始碼檔案：\n" + layer_html + "\n"
        )

    # 3. Add Tile Array
    tile_html = """
<div class="tile-array">
  <h4>AIE Tile Array (50×8) 資源映射</h4>
  <div class="tile-hint">在此 2D FFT 專案中，Col 與 Row 階段分別佔用哪些 Tile？（游標懸停查看座標） <span id="tile-info" style="font-weight: 600; margin-left: 8px;">&nbsp;</span></div>
  <div class="tile-grid" id="tile-grid"></div>
  <div class="tile-legend">
    <div><span class="swatch col"></span>Col FFT (Tile 24,0 ~ 27,2)</div>
    <div><span class="swatch row"></span>Row FFT (Tile 24,3 ~ 27,4)</div>
    <div><span class="swatch unused"></span>未使用</div>
  </div>
</div>
"""
    if "tile-array" not in content:
        content = content.replace(
            "| **第一階段：Column FFT**<br> `col_fft_twd_mul_graph.h` | 收取 PLIO",
            tile_html + "\n| **第一階段：Column FFT**<br> `col_fft_twd_mul_graph.h` | 收取 PLIO"
        )

    # 4. Add File Search
    search_html = """
<div class="file-search">
  <input type="text" id="file-search-input" placeholder="過濾檔名或副檔名 (例如 .cpp, host)..." />
  <div class="file-count" id="file-search-count"></div>
</div>
"""
    if "file-search" not in content:
        content = content.replace(
            "## 附錄 B：專案檔案與資料夾速查\n",
            "## 附錄 B：專案檔案與資料夾速查\n" + search_html + "\n"
        )

    # 5. Inline versal-acap.svg
    with open('versal-acap.svg', 'r', encoding='utf-8') as f:
        svg_content = f.read()
    
    # Strip <style> tag from svg (since CSS is in html already)
    svg_body = re.sub(r'<style>.*?</style>', '', svg_content, flags=re.DOTALL)
    svg_body = svg_body.replace('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 280" role="img" aria-label="Versal ACAP contains PS, PL, and AIE">',
                                '<svg class="versal-acap-svg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 280" role="img" aria-label="Versal ACAP contains PS, PL, and AIE">')

    content = re.sub(
        r'<img src="\./versal-acap\.svg"[^\>]*>',
        svg_body,
        content
    )

    with open('notes.md', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    main()
