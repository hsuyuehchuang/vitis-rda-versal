#!/usr/bin/env python3
import re, subprocess

# 1. Run pandoc
print("Running pandoc...")
subprocess.run(['pandoc', 'notes.md', '-f', 'markdown', '-t', 'html5', '--wrap=none', '-o', '/tmp/notes_body.html'], check=True)

HTML_SRC   = "notes_v2.html"
BODY_FILE  = "/tmp/notes_body.html"

with open(HTML_SRC, encoding="utf-8") as f:
    template = f.read()

# 2. Read new body
with open(BODY_FILE, encoding="utf-8") as f:
    new_body = f.read()

# 3. Replace <main>...</main>
new_main = f"  <main>\n{new_body}\n  </main>"
old_main_pat = re.compile(r'<main>.*?</main>', re.DOTALL)
if old_main_pat.search(template):
    template = old_main_pat.sub(new_main, template, count=1)
else:
    print("WARNING: could not find <main>")

with open(HTML_SRC, "w", encoding="utf-8") as f:
    f.write(template)

print("HTML rebuild complete.")
