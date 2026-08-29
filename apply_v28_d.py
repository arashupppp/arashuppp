#!/usr/bin/env python3
"""Final 3D patches - handle escaped template literals."""
import re

path = '/root/hovi/editor_v1.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# ============================================================
# 1. 3D fillet rendering - find the inlined elevs pattern (with \n)
# ============================================================
# Pattern in M3_WORLD_SRC uses \\n literals in JS string
old_3d_elevs = 'for(const ev of (DATA.elevs||[])){\\n    const EW=ev.w||1.6, ED=ev.d||1.7;\\n    addBox(ev.x,H/2,ev.z,ED,H,EW,(ev.rot||0),new THREE.MeshStandardMaterial({color:0x8a8f94,roughness:.6}));\\n  }'

new_3d_elevs = 'for(const ev of (DATA.elevs||[])){\\n    const EW=ev.w||1.6, ED=ev.d||1.7;\\n    addBox(ev.x,H/2,ev.z,ED,H,EW,(ev.rot||0),new THREE.MeshStandardMaterial({color:0x8a8f94,roughness:.6}));\\n  }\\n  // فیلت‌ها\\n  for(const f of (DATA.fillets||[])){\\n    const ax=f.a[0],az=f.a[1],bx=f.b[0],bz=f.b[1];\\n    const fx2=(ax+bx)/2, fz2=(az+bz)/2;\\n    const r=f.r||0.3;\\n    const cyl=new THREE.Mesh(new THREE.CylinderGeometry(r,r,H,16,1,true),new THREE.MeshStandardMaterial({color:0xff66cc,roughness:.5,transparent:true,opacity:.7}));\\n    cyl.position.set(fx2,H/2,fz2);\\n    scene.add(cyl);\\n  }'

if old_3d_elevs in content:
    content = content.replace(old_3d_elevs, new_3d_elevs, 1)
    print("✓ 3D fillet rendering added")
else:
    print("✗ 3D elevs not found (escaped)")

# ============================================================
# 2. 3D free door rendering
# ============================================================
# In M3_WORLD_SRC, the door loop is: for(const o of (DATA.doors||[])){ if(o.wallId!==w.id)continue;
# but inside template literal, newlines are \n
# We need to find: for(const o of (DATA.doors||[])){ if(o.wallId!==w.id)continue;
# But this also exists in drawOpenings 2D. Let me use a more specific pattern.

# In M3_WORLD_SRC, the door loop is inside buildWall. We need to be specific.
old_3d_door_loop = '// \\u062f\\u0631\\u0628\\u200c\\u0647\\u0627\\u06cc \\u0645\\u0648\\u062c\\u0648\\u062f: \\u0642\\u0627\\u0628 + \\u0644\\u0646\\u06af\\u0647\\u0654 \\u0627\\u0646\\u06cc\\u0645\\u06cc\\u0634\\u0646\\u06cc\\n    for(const o of (DATA.doors||[])){ if(o.wallId!==w.id)continue;'

new_3d_door_loop = '// \\u062f\\u0631\\u0628\\u200c\\u0647\\u0627\\u06cc \\u0645\\u0648\\u062c\\u0648\\u062f: \\u0642\\u0627\\u0628 + \\u0644\\u0646\\u06af\\u0647\\u0654 \\u0627\\u0646\\u06cc\\u0645\\u06cc\\u0634\\u0646\\u06cc\\n    // Free doors (standalone)\\n    for(const o of (DATA.doors||[])){ if(o.type!==\\'free\\' || !o.a || !o.b) continue; const ax2=o.a[0],az2=o.a[1],bx2=o.b[0],bz2=o.b[1]; const L2=Math.hypot(bx2-ax2,bz2-az2); if(L2<0.01)continue; const on2=Math.atan2(bx2-ax2,bz2-az2); addBox((ax2+bx2)/2,H/2,(az2+bz2)/2,W,H,L2,on2,wallMat); }\\n    for(const o of (DATA.doors||[])){ if(o.wallId!==w.id)continue;'

if old_3d_door_loop in content:
    content = content.replace(old_3d_door_loop, new_3d_door_loop, 1)
    print("✓ 3D free door rendering added")
else:
    print("✗ 3D door loop not found (escaped)")

# ============================================================
# 3. F key for freeDoor
# ============================================================
# In the main editor, look for the F key handler
# It's probably in a keydown event
m = re.search(r"if\(e\.key===['\"]f['\"]", content)
if m:
    print(f"  F key at offset {m.start()}")
    # Check if Q is already there
    nearby = content[m.start():m.start()+500]
    if "freeDoor" not in nearby:
        # Insert Q key right after the F block
        # find end of that if statement
        rest = content[m.start():m.start()+1000]
        # Find the first ; after the if statement
        end = rest.find(';')
        if end > 0:
            insert_pos = m.start() + end + 1
            insertion = "\n  if(e.key==='q'||e.key==='Q') setTool('freeDoor');"
            content = content[:insert_pos] + insertion + content[insert_pos:]
            print("✓ Q key handler added")
        else:
            print("✗ F key end not found")
    else:
        print("- Q key already present")
else:
    print("✗ F key not found")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f"Final size: {len(content)} bytes")
