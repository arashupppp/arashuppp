#!/usr/bin/env python3
"""Apply v28 editor changes."""
import re

path = '/root/hovi/editor_v1.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"Original size: {len(content)} bytes")

# 1. Update version badge
content = content.replace('editor-v23', 'editor-v28')

# 2. Add fillet tool button to topbar
old_btn = '<button class="tool-btn" id="btnRail">⌒ نرده</button>'
new_btn = '<button class="tool-btn" id="btnFillet">⌓ فیلت</button>\n  <button class="tool-btn" id="btnRail">⌒ نرده</button>'
if old_btn in content:
    content = content.replace(old_btn, new_btn, 1)
    print("✓ Fillet button added")
else:
    print("✗ btnRail not found")

# 3. Add fillets array to proj
old_proj = "walls:[], doors:[], columns:[], stairs:[], elevs:[], wells:[], balcs:[], rails:[], zones:[], nextId:1"
new_proj = "walls:[], doors:[], columns:[], stairs:[], elevs:[], wells:[], balcs:[], rails:[], zones:[], fillets:[], nextId:1"
if old_proj in content:
    content = content.replace(old_proj, new_proj, 1)
    print("✓ fillets array added to proj")
else:
    print("✗ proj array not found")

# 4. Change lineCap from 'round' to 'butt' in drawWalls
count = content.count("ctx.lineCap='round';")
content = content.replace("ctx.lineCap='round';", "ctx.lineCap='butt';")
print(f"✓ Replaced {count} occurrences of lineCap='round' with 'butt'")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f"Final size: {len(content)} bytes")
