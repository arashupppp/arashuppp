#!/usr/bin/env python3
"""Apply remaining v28 patches that didn't match in the first pass."""
import re

path = '/root/hovi/editor_v1.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"Size: {len(content)} bytes")

# ============================================================
# 1. Add stFillet counter update
# ============================================================
old_count = "stOpen.textContent=faNum(proj.doors.length);"
new_count = "stOpen.textContent=faNum(proj.doors.length);\n  const sf=document.getElementById('stFillet'); if(sf) sf.textContent=faNum(proj.fillets.length);"

if old_count in content:
    content = content.replace(old_count, new_count, 1)
    print("✓ stFillet counter added")
else:
    print("✗ stFillet counter not found")

# ============================================================
# 2. Add resize handles to drawElevs (selId check + 4 corner handles)
# ============================================================
old_elev_restore = '''    ctx.restore();
    ctx.save();
    ctx.fillStyle='#00ffcc'; ctx.font='10px Tahoma'; ctx.textAlign='center';
    ctx.fillText('آسانسور', c[0], c[1] - Math.max(w,d)/2 - 6);
    ctx.restore();'''

new_elev_restore = '''    if(selId===ev.id){
      // ۴ دستگیره تغییر سایز
      ctx.fillStyle='#00ffcc';
      const corners=[[-d/2,-w/2],[d/2,-w/2],[d/2,w/2],[-d/2,w/2]];
      for(const [cx,cy] of corners){
        ctx.save();
        ctx.translate(c[0],c[1]); ctx.rotate(rot);
        ctx.beginPath(); ctx.arc(cx,cy,5,0,Math.PI*2); ctx.fill();
        ctx.restore();
      }
    }
    ctx.restore();
    ctx.save();
    ctx.fillStyle=ev.id===selId?'#00ffcc':'#888'; ctx.font='10px Tahoma'; ctx.textAlign='center';
    ctx.fillText('آسانسور', c[0], c[1] - Math.max(w,d)/2 - 6);
    ctx.restore();'''

if old_elev_restore in content:
    content = content.replace(old_elev_restore, new_elev_restore, 1)
    print("✓ Elevator resize handles added")
else:
    print("✗ Elevator restore block not found")

# ============================================================
# 3. Add fillet rendering to M3_WORLD_SRC (the main 3D world template)
#    Find the DATA.elevs section and add fillet rendering after it
# ============================================================
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
# 4. Add free door rendering to M3_WORLD_SRC
#    Update wall cut loop to skip free doors, add free door rendering
# ============================================================
# Update the cuts loop to skip free doors
old_3d_cuts = "    for(const o of (DATA.doors||[])) if(o.wallId===w.id) cuts.push(o.t/L-o.w/2/L, o.t/L+o.w/2/L);"
new_3d_cuts = "    for(const o of (DATA.doors||[])) if(o.wallId===w.id && o.type!=='free') cuts.push(o.t/L-o.w/2/L, o.t/L+o.w/2/L);"

if old_3d_cuts in content:
    content = content.replace(old_3d_cuts, new_3d_cuts, 1)
    print("✓ 3D wall cuts updated for free doors")
else:
    print("✗ 3D wall cuts not found")

# Add free door rendering - find the door rendering loop and add before it
old_3d_door_loop = "    for(const o of (DATA.doors||[])){ if(o.wallId!==w.id)continue;"
new_3d_door_loop = """    // Free doors (standalone, no wall)
    for(const o of (DATA.doors||[])){
      if(o.type!=='free' || !o.a || !o.b) continue;
      const ax2=o.a[0],az2=o.a[1],bx2=o.b[0],bz2=o.b[1];
      const L2=Math.hypot(bx2-ax2,bz2-az2); if(L2<0.01)continue;
      const on2=Math.atan2(bx2-ax2,bz2-az2);
      addBox((ax2+bx2)/2,H/2,(az2+bz2)/2,W,H,L2,on2,wallMat);
    }
    for(const o of (DATA.doors||[])){ if(o.wallId!==w.id)continue;"""

if old_3d_door_loop in content:
    content = content.replace(old_3d_door_loop, new_3d_door_loop, 1)
    print("✓ 3D free door rendering added")
else:
    print("✗ 3D door loop not found")

# ============================================================
# 5. Add fillet export to DATA serialization (for 3D)
#    Make sure fillets are included in the world export
# ============================================================
# The DATA export already uses DATA.fillets - the render loop handles it
# We need to ensure the export function includes fillets
old_export = "  const snap=JSON.stringify({walls:proj.walls,doors:proj.doors,columns:proj.columns,stairs:proj.stairs,elevs:proj.elevs,wells:proj.wells,balcs:proj.balcs,rails:proj.rails,zones:proj.zones,planOff,planScale,name:proj.name});"
new_export = "  const snap=JSON.stringify({walls:proj.walls,doors:proj.doors,columns:proj.columns,stairs:proj.stairs,elevs:proj.elevs,wells:proj.wells,balcs:proj.balcs,rails:proj.rails,zones:proj.zones,fillets:proj.fillets,planOff,planScale,name:proj.name});"

if old_export in content:
    content = content.replace(old_export, new_export, 1)
    print("✓ Export includes fillets")
else:
    print("✗ Export not found")

# ============================================================
# 6. Add wall anchor drag: update openings t when anchor moved
#    We need to scale opening t when wall end is dragged
# ============================================================
# This is handled by the existing logic - when a wall endpoint is moved,
# the openings' t values stay the same (they're world coordinates along the wall)
# The openingPos function uses the wall's current a/b coordinates,
# so t scales automatically. No change needed.

# ============================================================
# 7. Add free door creation: F key shortcut + tool selection
# ============================================================
old_tool_rail = "  else if(tool==='rail'){"
new_tool_rail = """  else if(tool==='freeDoor'){
    // Free door: click point A, then point B on any wall
    const sp=snapPoint(w, e.altKey);
    if(!freeDoorPtA){
      freeDoorPtA=[sp.x,sp.z];
      showHint('نقطه دوم دهانه در را کلیک کنید');
    } else {
      // Find nearest wall to snap direction
      const ptB=freeDoorPtA;
      const wallHit=pickWall(sx,sy);
      let endPt=[sp.x,sp.z];
      if(wallHit){
        const wl=proj.walls.find(x=>x.id===wallHit.id);
        if(wl){
          const [ax,az]=wl.a,[bx,bz]=wl.b;
          const dx=bx-ax,dz=bz-az,L=Math.hypot(dx,dz);
          // Project mouse onto wall
          const t=((sp.x-ax)*dx+(sp.z-az)*dz)/(L*L);
          const cx=Math.max(0,Math.min(1,t));
          endPt=[ax+dx*cx, az+dz*cx];
        }
      }
      pushUndo();
      const nid='d'+(proj.nextId++);
      proj.doors.push({id:nid, type:'free', a:ptB, b:endPt, w:DOOR_W});
      freeDoorPtA=null;
      selId=nid;
      showHint('درگذاری آزاد ایجاد شد');
    }
    refresh();
  }
  else if(tool==='rail'){"""

if old_tool_rail in content:
    content = content.replace(old_tool_rail, new_tool_rail, 1)
    print("✓ freeDoor tool handler added")
else:
    print("✗ tool=rail not found")

# Add freeDoorPtA state
old_state_rail = "let railPts=[];           // نرده: نقاط شکست polyline (≥۲) — راست‌کلیک پایان"
new_state_rail = """let railPts=[];           // نرده: نقاط شکست polyline (≥۲) — راست‌کلیک پایان
let freeDoorPtA=null;   // درگذاری آزاد: نقطه اول"""

if old_state_rail in content:
    content = content.replace(old_state_rail, new_state_rail, 1)
    print("✓ freeDoorPtA state added")
else:
    print("✗ railPts state not found")

# Add setTool('freeDoor') call for F key
old_key_f = "  if(e.key==='f'||e.key==='F') setTool('door');"
new_key_f = "  if(e.key==='f'||e.key==='F') setTool('door');\n  if(e.key==='q'||e.key==='Q') setTool('freeDoor');"

if old_key_f in content:
    content = content.replace(old_key_f, new_key_f, 1)
    print("✓ F/Q key handlers added")
else:
    print("✗ F key not found")

# Add hint text for freeDoor tool
old_hint_stair = "  if(tool==='stair') showHint('پله: ۲ کلیک شروع/پایان · کلید T نوع پله · اسکرول ارتفاع · Shift شکل L/U');"
new_hint_stair = """  if(tool==='stair') showHint('پله: ۲ کلیک شروع/پایان · کلید T نوع پله · اسکرول ارتفاع · Shift شکل L/U');
  if(tool==='freeDoor') showHint('درگذاری آزاد: Q · ۲ کلیک ابتدا و انتهای دهانه · راست‌کلیک = لغو');
  if(tool==='fillet') showHint('فیلت: ۲ کلیک دو گوشه · شعاع پیش‌فرض '+filletRadius.toFixed(2)+'m');"""

if old_hint_stair in content:
    content = content.replace(old_hint_stair, new_hint_stair, 1)
    print("✓ Tool hints added")
else:
    print("✗ stair hint not found")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f"Final size: {len(content)} bytes")
print("Done!")
