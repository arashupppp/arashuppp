#!/usr/bin/env python3
"""Apply remaining v28 patches - round 3."""
import re

path = '/root/hovi/editor_v1.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# ============================================================
# 1. 3D fillet rendering in M3_WORLD_SRC
#    Find the elevs loop inside the inlined template
# ============================================================
# Pattern inside template (escaped): for(const ev of (DATA.elevs||[])){\n    const EW=ev.w||1.6, ED=ev.d||1.7;\n    addBox(...)\n  }
old_3d_elevs = '''for(const ev of (DATA.elevs||[])){
    const EW=ev.w||1.6, ED=ev.d||1.7;
    addBox(ev.x,H/2,ev.z,ED,H,EW,(ev.rot||0),new THREE.MeshStandardMaterial({color:0x8a8f94,roughness:.6}));
  }'''

new_3d_elevs = '''for(const ev of (DATA.elevs||[])){
    const EW=ev.w||1.6, ED=ev.d||1.7;
    addBox(ev.x,H/2,ev.z,ED,H,EW,(ev.rot||0),new THREE.MeshStandardMaterial({color:0x8a8f94,roughness:.6}));
  }
  // فیلت‌ها
  for(const f of (DATA.fillets||[])){
    const ax=f.a[0],az=f.a[1],bx=f.b[0],bz=f.b[1];
    const fx2=(ax+bx)/2, fz2=(az+bz)/2;
    const r=f.r||0.3;
    const cyl=new THREE.Mesh(new THREE.CylinderGeometry(r,r,H,16,1,true),new THREE.MeshStandardMaterial({color:0xff66cc,roughness:.5,transparent:true,opacity:.7}));
    cyl.position.set(fx2,H/2,fz2);
    scene.add(cyl);
  }'''

if old_3d_elevs in content:
    content = content.replace(old_3d_elevs, new_3d_elevs, 1)
    print("✓ 3D fillet rendering added")
else:
    print("✗ 3D elevs not found")

# ============================================================
# 2. 3D free door rendering
#    We need to find the door rendering loop
# ============================================================
old_3d_door_loop = '''for(const o of (DATA.doors||[])){ if(o.wallId!==w.id)continue;'''
new_3d_door_loop = '''// Free doors: separate pass
    for(const o of (DATA.doors||[])){
      if(o.type!=='free' || !o.a || !o.b) continue;
      const ax2=o.a[0],az2=o.a[1],bx2=o.b[0],bz2=o.b[1];
      const L2=Math.hypot(bx2-ax2,bz2-az2); if(L2<0.01)continue;
      const on2=Math.atan2(bx2-ax2,bz2-az2);
      addBox((ax2+bx2)/2,H/2,(az2+bz2)/2,W,H,L2,on2,wallMat);
    }
    for(const o of (DATA.doors||[])){ if(o.wallId!==w.id)continue;'''

if old_3d_door_loop in content:
    content = content.replace(old_3d_door_loop, new_3d_door_loop, 1)
    print("✓ 3D free door rendering added")
else:
    print("✗ 3D door loop not found")

# ============================================================
# 3. Find and update export - look at the data export
# ============================================================
# Find current export pattern
m = re.search(r'JSON\.stringify\(\{[^}]*walls:proj\.walls[^}]*\}\);', content)
if m:
    old = m.group(0)
    new = old
    if 'fillets' not in new:
        new = new.replace('zones:proj.zones', 'zones:proj.zones,fillets:proj.fillets')
    if new != old:
        content = content.replace(old, new, 1)
        print("✓ Export includes fillets")
    else:
        print("- Export already has fillets")
else:
    print("✗ Export pattern not found")

# ============================================================
# 4. F key for freeDoor - find keyboard handler
# ============================================================
# Find setTool('door') and add setTool('freeDoor')
# Look for keyboard event
m = re.search(r"setTool\('door'\)", content)
if m:
    # add a line right after the first occurrence (if not in M3_WORLD_SRC)
    # we need to be careful - check context
    pos = m.end()
    # Don't modify if it's inside M3_WORLD_SRC (it's the one we want)
    pass  # Already handled via Q key

# Find keydown handler in main editor
old_key = "if(e.key==='f'||e.key==='F')"
if old_key in content:
    new_key = "if(e.key==='f'||e.key==='F') setTool('door');\n  if(e.key==='q'||e.key==='Q') setTool('freeDoor');"
    # Be careful - only add once
    count = content.count(old_key)
    if count == 1:
        content = content.replace(old_key + " setTool('door');", old_key + " setTool('door');\n  if(e.key==='q'||e.key==='Q') setTool('freeDoor');", 1)
        print("✓ Q key for freeDoor added")
    else:
        print(f"- {count} F key handlers found, skipping auto-add")
else:
    print("✗ F key handler not found")

# ============================================================
# 5. Find tool hints - look for tool==='stair'
# ============================================================
m = re.search(r"if\(tool==='stair'\)", content)
if m:
    pos = m.end()
    # find the showHint line right after
    rest = content[pos:pos+500]
    sh = re.search(r"showHint\('[^']*'\);", rest)
    if sh:
        # Insert hints after
        insert_pos = pos + sh.end()
        new_hints = """\n  if(tool==='freeDoor') showHint('درگذاری آزاد: Q · ۲ کلیک ابتدا و انتهای دهانه · راست‌کلیک = لغو');
  if(tool==='fillet') showHint('فیلت: ۲ کلیک دو گوشه · شعاع پیش‌فرض '+filletRadius.toFixed(2)+'m');"""
        if 'freeDoor' not in content[pos:insert_pos+500]:
            content = content[:insert_pos] + new_hints + content[insert_pos:]
            print("✓ Tool hints added")
        else:
            print("- Tool hints already present")
    else:
        print("✗ Stair showHint not found")
else:
    print("✗ tool==='stair' not found")

# ============================================================
# 6. Ensure wall drawing shows butt caps with end squares (visual)
# ============================================================
# Add end-point squares to drawWalls
old_wall_loop = '''function drawWalls(){
  for(const wl of proj.walls){
    const [ax,ay]=W2S({x:wl.a[0],z:wl.a[1]}), [bx,by]=W2S({x:wl.b[0],z:wl.b[1]});
    ctx.strokeStyle=lockedIds.has(wl.id)?'#ff9f43':(wl.id===selId?'#00ffcc':'#ddd');
    ctx.globalAlpha=ghostMode&&wl.id!==selId?0.28:1;
    ctx.lineWidth=Math.max(3,WALL_T*view.zoom);
    ctx.lineCap='butt';
    ctx.beginPath(); ctx.moveTo(ax,ay); ctx.lineTo(bx,by); ctx.stroke();'''

# Update the existing lineCap to also draw end squares
new_wall_loop = '''function drawWalls(){
  for(const wl of proj.walls){
    const [ax,ay]=W2S({x:wl.a[0],z:wl.a[1]}), [bx,by]=W2S({x:wl.b[0],z:wl.b[1]});
    ctx.strokeStyle=lockedIds.has(wl.id)?'#ff9f43':(wl.id===selId?'#00ffcc':'#ddd');
    ctx.globalAlpha=ghostMode&&wl.id!==selId?0.28:1;
    ctx.lineWidth=Math.max(3,WALL_T*view.zoom);
    ctx.lineCap='butt';
    ctx.beginPath(); ctx.moveTo(ax,ay); ctx.lineTo(bx,by); ctx.stroke();
    // سر دیوار: مربع اتصال (v28 wall caps)
    if(view.zoom>15){
      ctx.fillStyle=lockedIds.has(wl.id)?'#ff9f43':(wl.id===selId?'#00ffcc':'#666');
      const cap=Math.max(2,WALL_T*view.zoom*0.3);
      ctx.fillRect(ax-cap,ay-cap,cap*2,cap*2);
      ctx.fillRect(bx-cap,by-cap,cap*2,cap*2);
    }'''

if old_wall_loop in content:
    content = content.replace(old_wall_loop, new_wall_loop, 1)
    print("✓ Wall end caps added")
else:
    print("✗ drawWalls not found")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f"Final size: {len(content)} bytes")
