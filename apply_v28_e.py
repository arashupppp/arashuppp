#!/usr/bin/env python3
"""Final 3D patches."""
import re

path = '/root/hovi/editor_v1.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"Size before: {len(content)}")

# 1. 3D fillet rendering - escape newlines
old_3d_elevs = 'for(const ev of (DATA.elevs||[])){\\n    const EW=ev.w||1.6, ED=ev.d||1.7;\\n    addBox(ev.x,H/2,ev.z,ED,H,EW,(ev.rot||0),new THREE.MeshStandardMaterial({color:0x8a8f94,roughness:.6}));\\n  }'

new_3d_elevs = 'for(const ev of (DATA.elevs||[])){\\n    const EW=ev.w||1.6, ED=ev.d||1.7;\\n    addBox(ev.x,H/2,ev.z,ED,H,EW,(ev.rot||0),new THREE.MeshStandardMaterial({color:0x8a8f94,roughness:.6}));\\n  }\\n  for(const f of (DATA.fillets||[])){\\n    const ax=f.a[0],az=f.a[1],bx=f.b[0],bz=f.b[1];\\n    const fx2=(ax+bx)/2, fz2=(az+bz)/2;\\n    const r=f.r||0.3;\\n    const cyl=new THREE.Mesh(new THREE.CylinderGeometry(r,r,H,16,1,true),new THREE.MeshStandardMaterial({color:0xff66cc,roughness:.5,transparent:true,opacity:.7}));\\n    cyl.position.set(fx2,H/2,fz2);\\n    scene.add(cyl);\\n  }'

if old_3d_elevs in content:
    content = content.replace(old_3d_elevs, new_3d_elevs, 1)
    print("OK 3D fillet")
else:
    print("X 3D elevs not found")

# 2. Skip free doors in the existing door loop (3D)
# The pattern in M3_WORLD_SRC template uses escape
old_3d_door = 'for(const o of (DATA.doors||[])){ if(o.wallId!==w.id)continue;\\n      const c=o.t/L, cx=ax+(bx-ax)*c, cz=az+(bz-az)*c, ow=o.w;\\n      if(o.type===\'open\'){ continue; }'
new_3d_door = 'for(const o of (DATA.doors||[])){ if(o.wallId!==w.id)continue;\\n      if(o.type===\'free\'){ continue; }\\n      const c=o.t/L, cx=ax+(bx-ax)*c, cz=az+(bz-az)*c, ow=o.w;\\n      if(o.type===\'open\'){ continue; }'

if old_3d_door in content:
    content = content.replace(old_3d_door, new_3d_door, 1)
    print("OK 3D skip free doors")
else:
    print("X 3D door skip not found")

# 3. Free door rendering pass
old_build = 'for(const w of DATA.walls)buildWall(w);'
new_build = 'for(const w of DATA.walls)buildWall(w);\\n  // Free doors (standalone walls)\\n  for(const o of (DATA.doors||[])){\\n    if(o.type!==\'free\' || !o.a || !o.b) continue;\\n    const ax2=o.a[0],az2=o.a[1],bx2=o.b[0],bz2=o.b[1];\\n    const L2=Math.hypot(bx2-ax2,bz2-az2); if(L2<0.01)continue;\\n    const on2=Math.atan2(bx2-ax2,bz2-az2);\\n    addBox((ax2+bx2)/2,H/2,(az2+bz2)/2,W,H,L2,on2,wallMat);\\n  }'

if old_build in content:
    content = content.replace(old_build, new_build, 1)
    print("OK Free door pass")
else:
    print("X buildWall not found")

# 4. F key handler - find F key in main editor (not M3_WORLD_SRC)
# The main editor has a keydown event. Find F key
# Look for setTool('door') with F key
import re

# Find the F key event in main editor (not in M3_WORLD_SRC which has pointer lock)
# In main editor, it's likely: if(e.key==='f'||...) setTool('door');
# But this also exists in M3_WORLD_SRC (spray). Let's just add Q key handler safely.

# Search for the F key handler before the inlined M3_WORLD_SRC (which starts at "var TPL=")
# The main editor F key is before var TPL
fkey_pattern = "if(e.key==='f'||e.key==='F') setTool('door');"
# Check if it exists in main editor area
tpl_pos = content.find('var TPL="<!DOCTYPE html>')
if tpl_pos > 0:
    main_area = content[:tpl_pos]
    if fkey_pattern in main_area and "freeDoor" not in main_area:
        # Add Q key after
        idx = main_area.find(fkey_pattern)
        insert_pos = idx + len(fkey_pattern)
        insertion = "\n  if(e.key==='q'||e.key==='Q') setTool('freeDoor');"
        content = content[:insert_pos] + insertion + content[insert_pos:]
        print("OK Q key for freeDoor added")
    else:
        print("- F key already has freeDoor or not in main area")
else:
    print("X var TPL not found")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f"Size after: {len(content)}")
