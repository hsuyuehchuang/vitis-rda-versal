import subprocess
import json

try:
    result = subprocess.run(
        ["/home/hsuyueh.chuang/.local/bin/notebooklm", "ask", "-n", "935c676c", "請給我一份詳細的 AI Engine Survey 重點報告，包含架構、PS/PL/AIE 分工與應用案例，使用 Markdown 格式輸出。", "--json"],
        capture_output=True,
        text=True,
        check=True
    )
    with open("notebooklm_output.json", "w") as f:
        f.write(result.stdout)
except Exception as e:
    with open("notebooklm_output.json", "w") as f:
        f.write(str(e))
        if hasattr(e, 'stdout'):
            f.write("\nSTDOUT:\n" + e.stdout)
        if hasattr(e, 'stderr'):
            f.write("\nSTDERR:\n" + e.stderr)
