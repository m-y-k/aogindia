import os
import re

folder = r"d:\Drone Projects\AOG India"
log_lines = []

html_files = [f for f in os.listdir(folder) if f.endswith('.html')]
log_lines.append(f"Files: {len(html_files)}")

for fname in sorted(html_files):
    fpath = os.path.join(folder, fname)
    with open(fpath, 'r', encoding='utf-8', errors='replace') as fh:
        content = fh.read()
    
    orig = content
    # Replace "AOG India Esports" -> "AOG India eSports" everywhere
    content = content.replace("AOG India Esports", "AOG India eSports")
    
    if content != orig:
        with open(fpath, 'w', encoding='utf-8', newline='') as fh:
            fh.write(content)
        count = orig.count("AOG India Esports")
        log_lines.append(f"UPDATED ({count}x): {fname}")
    else:
        log_lines.append(f"unchanged: {fname}")

log_path = os.path.join(folder, "update_log.txt")
with open(log_path, 'w', encoding='utf-8') as fh:
    fh.write('\n'.join(log_lines))

print("Done. Check update_log.txt")
