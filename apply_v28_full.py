#!/usr/bin/env python3
"""Comprehensive v28 changes."""
import re

path = '/root/hovi/editor_v1.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"Original size: {len(content)} bytes")

# ============================================================
# FEATURE 1: Free Door (inter-wall door) - add state, openingPos support, hit test
# ============================================================
# We will:
# - Modify openingPos to support doors without wallId (free doors)
# - Add "free" door logic: type='free' has a/b coordinates directly
# - Add hit testing in pickOpening for free doors
# - Add button to install free door (F key or new tool)
# - Add data structure: { id, type:'free', ax,az, bx,bz, w, swing }

# Extend openingPos function
old_opening = '''function openingPos(op){
  const wl=wallById(op.wallId); if(!wl) return null;
  const [ax,az]=wl.a,[bx,bz]=wl.b;
  const L=Math.hypot(bx-ax,bz-az)||1;
  const uc=Math.min(Math.max(op.t/L,(op.w/2)/L), 1-(op.w/2)/L);
  const px=ax+(bx-ax)*uc, pz=az+(bz-az)*uc;
  return {x:px,z:pz, dx:(bx-ax)/L, dz:(bz-az)/L, nx:-(bz-az)/L, nz:(bx-ax)/L};
}'''

new_opening = '''function openingPos(op){
  // Free door (no wallId) - use direct a/b coords
  if(op.type==='free' || op.wallId==null){
    const [ax,az]=op.ax!=null?op.a:[op.ax,op.az],[bx,bz]=op.b;
    const L=Math.hypot(bx-ax,bz-az)||1;
    const uc=0.5;
    const px=ax+(bx-ax)*uc, pz=az+(bz-az)*uc;
    return {x:px,z:pz, dx:(bx-ax)/L, dz:(bz-az)/L, nx:-(bz-az)/L, nz:(bx-ax)/L};
  }
  const wl=wallById(op.wallId); if(!wl) return null;
  const [ax,az]=wl.a,[bx,bz]=wl.b;
  const L=Math.hypot(bx-ax,bz-az)||1;
  const uc=Math.min(Math.max(op.t/L,(op.w/2)/L), 1-(op.w/2)/L);
  const px=ax+(bx-ax)*uc, pz=az+(bz-az)*uc;
  return {x:px,z:pz, dx:(bx-ax)/L, dz:(bz-az)/L, nx:-(bz-az)/L, nz:(bx-ax)/L};
}'''

if old_opening in content:
    content = content.replace(old_opening, new_opening, 1)
    print("✓ openingPos updated for free doors")
else:
    print("✗ openingPos not found")

# Add free door support to pickOpening
old_pick = '''function pickOpening(sx,sy){
  let best=null,bestD=18;
  for(const op of proj.doors){
    const P=openingPos(op); if(!P) continue;
    const wl=wallById(op.wallId); if(!wl) continue;
    const [ax,ay]=W2S({x:wl.a[0],z:wl.a[1]}), [bx,by]=W2S({x:wl.b[0],z:wl.b[1]});
    const L=Math.hypot(bx-ax,by-ay); if(!L) continue;
    const ux=(bx-ax)/L, uy=(by-ay)/L;
    // قطعهٔ بازشو روی صفحه: از مرکز به دو طرف op.w/2
    const hw=op.w/2*view.zoom;
    const cx=ax+ux*op.t*view.zoom, cy=ay+uy*op.t*view.zoom;
    // فاصلهٔ نقطه از قطعه [c-hw, c+hw]
    const rx=sx-cx, ry=sy-cy;
    let tt=rx*ux+ry*uy; tt=Math.max(-hw,Math.min(hw,tt));
    const d=Math.hypot(rx-ux*tt, ry-uy*tt);
    if(d<bestD){bestD=d;best=op;}
  } return best;
}'''

new_pick = '''function pickOpening(sx,sy){
  let best=null,bestD=18;
  for(const op of proj.doors){
    const P=openingPos(op); if(!P) continue;
    // Free doors: hit test directly on a/b
    if(op.type==='free' || op.wallId==null){
      const [ax,ay]=W2S({x:op.a[0],z:op.a[1]}), [bx,by]=W2S({x:op.b[0],z:op.b[1]});
      const L=Math.hypot(bx-ax,by-ay); if(!L) continue;
      const ux=(bx-ax)/L, uy=(by-ay)/L;
      const hw=op.w/2*view.zoom;
      const cx=(ax+bx)/2, cy=(ay+by)/2;
      const rx=sx-cx, ry=sy-cy;
      let tt=rx*ux+ry*uy; tt=Math.max(-hw,Math.min(hw,tt));
      const d=Math.hypot(rx-ux*tt, ry-uy*tt);
      if(d<bestD){bestD=d;best=op;}
      continue;
    }
    const wl=wallById(op.wallId); if(!wl) continue;
    const [ax,ay]=W2S({x:wl.a[0],z:wl.a[1]}), [bx,by]=W2S({x:wl.b[0],z:wl.b[1]});
    const L=Math.hypot(bx-ax,by-ay); if(!L) continue;
    const ux=(bx-ax)/L, uy=(by-ay)/L;
    // قطعهٔ بازشو روی صفحه: از مرکز به دو طرف op.w/2
    const hw=op.w/2*view.zoom;
    const cx=ax+ux*op.t*view.zoom, cy=ay+uy*op.t*view.zoom;
    // فاصلهٔ نقطه از قطعه [c-hw, c+hw]
    const rx=sx-cx, ry=sy-cy;
    let tt=rx*ux+ry*uy; tt=Math.max(-hw,Math.min(hw,tt));
    const d=Math.hypot(rx-ux*tt, ry-uy*tt);
    if(d<bestD){bestD=d;best=op;}
  } return best;
}'''

if old_pick in content:
    content = content.replace(old_pick, new_pick, 1)
    print("✓ pickOpening updated for free doors")
else:
    print("✗ pickOpening not found")

# ============================================================
# FEATURE 2: Fillet tool - add fillet button handler, fillet drawing
# ============================================================
# Add fillet state
fillet_state_addition = """
let filletPts=[]; // فیلت: ۲ کلیک (گوشه اول، گوشه دوم)
let filletRadius=0.3; // شعاع پیش‌فرض فیلت
"""

# Insert after "let railPts=[];" line
old_rail = "let railPts=[];           // نرده: نقاط شکست polyline (≥۲) — راست‌کلیک پایان"
new_rail = "let railPts=[];           // نرده: نقاط شکست polyline (≥۲) — راست‌کلیک پایان" + fillet_state_addition

if old_rail in content:
    content = content.replace(old_rail, new_rail, 1)
    print("✓ Fillet state added")
else:
    print("✗ railPts not found")

# Add fillet drawing function and integration
# We add it as a new function before drawWalls
old_draw_walls_start = "function drawWalls(){\n  for(const wl of proj.walls){"

new_draw_walls_start = """function drawFillets(){
  for(const f of proj.fillets){
    const [x1,y1]=W2S({x:f.a[0],z:f.a[1]});
    const [x2,y2]=W2S({x:f.b[0],z:f.b[1]});
    const r=f.r*view.zoom;
    const sel=f.id===selId;
    ctx.strokeStyle=sel?'#00ffcc':'#ff66cc';
    ctx.lineWidth=2;
    ctx.beginPath();
    ctx.arc((x1+x2)/2, (y1+y2)/2, r, 0, Math.PI*2);
    ctx.stroke();
  }
  // پیش‌نمایش فیلت
  if(tool==='fillet' && filletPts.length){
    for(const p of filletPts){
      const [sx,sy]=W2S({x:p[0],z:p[1]});
      ctx.fillStyle='#ff66cc';
      ctx.beginPath(); ctx.arc(sx,sy,5,0,Math.PI*2); ctx.fill();
    }
    if(filletPts.length===1){
      const [x1,y1]=W2S({x:filletPts[0][0],z:filletPts[0][1]});
      const [x2,y2]=W2S(mouseWorld);
      ctx.strokeStyle='#ff66cc88';
      ctx.setLineDash([3,3]);
      ctx.beginPath(); ctx.moveTo(x1,y1); ctx.lineTo(x2,y2); ctx.stroke();
      ctx.setLineDash([]);
      ctx.beginPath(); ctx.arc((x1+x2)/2, (y1+y2)/2, filletRadius*view.zoom, 0, Math.PI*2); ctx.stroke();
    }
  }
}

function drawWalls(){
  for(const wl of proj.walls){"""

if old_draw_walls_start in content:
    content = content.replace(old_draw_walls_start, new_draw_walls_start, 1)
    print("✓ drawFillets function added")
else:
    print("✗ drawWalls start not found")

# Add drawFillets() to refresh() function
old_refresh_draws = "  drawPlan(); drawGrid(); drawWalls(); drawWells(); drawZones(); drawBalcs(); drawRails(); drawColumns(); drawStairs(); drawElevs(); drawOpenings(); drawPreview(); drawAnchors();"
new_refresh_draws = "  drawPlan(); drawGrid(); drawWalls(); drawWells(); drawZones(); drawBalcs(); drawRails(); drawColumns(); drawStairs(); drawElevs(); drawOpenings(); drawFillets(); drawPreview(); drawAnchors(); drawWallAnchors();"

if old_refresh_draws in content:
    content = content.replace(old_refresh_draws, new_refresh_draws, 1)
    print("✓ drawFillets added to refresh()")
else:
    print("✗ refresh draws not found")

# ============================================================
# FEATURE 3: Wall anchor points - drawWallAnchors, hit-test, drag
# ============================================================
# We add anchor drawing function
old_anchors_func = "function drawAnchors(){\n  if(tool!=='calib'||!proj.plan.anchorA) return;"
new_anchors_func = """function drawWallAnchors(){
  // نمایش نقاط لنگر ابتدا/انتهای دیوارها (برای درگ دقیق)
  if(!proj.walls.length) return;
  ctx.fillStyle='#00ffcc';
  for(const wl of proj.walls){
    if(lockedIds.has(wl.id)) continue;
    const [ax,ay]=W2S({x:wl.a[0],z:wl.a[1]});
    const [bx,by]=W2S({x:wl.b[0],z:wl.b[1]});
    // نقاط ابتدا و انتها
    ctx.beginPath(); ctx.arc(ax,ay,4,0,Math.PI*2); ctx.fill();
    ctx.beginPath(); ctx.arc(bx,by,4,0,Math.PI*2); ctx.fill();
  }
}

function drawAnchors(){
  if(tool!=='calib'||!proj.plan.anchorA) return;"""

if old_anchors_func in content:
    content = content.replace(old_anchors_func, new_anchors_func, 1)
    print("✓ drawWallAnchors added")
else:
    print("✗ drawAnchors not found")

# Add pickWallAnchor function
old_pick_walls = "function pickWall(sx,sy){"
new_pick_walls = """function pickWallAnchor(sx,sy){
  if(!proj.walls.length) return null;
  for(const wl of proj.walls){
    if(lockedIds.has(wl.id)) continue;
    const [ax,ay]=W2S({x:wl.a[0],z:wl.a[1]});
    const [bx,by]=W2S({x:wl.b[0],z:wl.b[1]});
    if(Math.hypot(sx-ax,sy-ay)<8) return {wall:wl, end:'a'};
    if(Math.hypot(sx-bx,sy-by)<8) return {wall:wl, end:'b'};
  }
  return null;
}

function pickWall(sx,sy){"""

if old_pick_walls in content:
    content = content.replace(old_pick_walls, new_pick_walls, 1)
    print("✓ pickWallAnchor added")
else:
    print("✗ pickWall not found")

# Add anchor drag handling in mousedown - look for the existing wall drag handler
old_drag = '''    else if((hit=pickWall(sx,sy))){ selId=hit.id;
      if(lockedIds.has(hit.id)){ dragInfo=null; }
      else dragInfo={type:'move', start:w, orig:{a:[...hit.a],b:[...hit.b]}, origSnap:mkSnap(), moved:false}; }'''
new_drag = '''    else if((anc=pickWallAnchor(sx,sy))){ selId=anc.wall.id;
      if(lockedIds.has(anc.wall.id)){ dragInfo=null; }
      else dragInfo={type:'anchor', id:anc.wall.id, end:anc.end, orig:{a:[...anc.wall.a],b:[...anc.wall.b]}, origSnap:mkSnap(), moved:false}; }
    else if((hit=pickWall(sx,sy))){ selId=hit.id;
      if(lockedIds.has(hit.id)){ dragInfo=null; }
      else dragInfo={type:'move', start:w, orig:{a:[...hit.a],b:[...hit.b]}, origSnap:mkSnap(), moved:false}; }'''

if old_drag in content:
    content = content.replace(old_drag, new_drag, 1)
    print("✓ Anchor drag handler added")
else:
    print("✗ Drag handler not found")

# Add anchor drag update in mousemove
old_move = '''  else if(dragInfo&&dragInfo.type==='move'&&selId){
    if(lockedIds.has(selId)){ dragInfo=null; return; }
    const wl=proj.walls.find(x=>x.id===selId); if(!wl) return;'''
new_move = '''  else if(dragInfo&&dragInfo.type==='anchor'&&selId){
    if(lockedIds.has(selId)){ dragInfo=null; return; }
    const wl=proj.walls.find(x=>x.id===selId); if(!wl) return;
    const newPt=mouseWorld;
    if(dragInfo.end==='a') wl.a=[newPt.x,newPt.z]; else wl.b=[newPt.x,newPt.z];
    dragInfo.moved=true; refresh();
  }
  else if(dragInfo&&dragInfo.type==='move'&&selId){
    if(lockedIds.has(selId)){ dragInfo=null; return; }
    const wl=proj.walls.find(x=>x.id===selId); if(!wl) return;'''

if old_move in content:
    content = content.replace(old_move, new_move, 1)
    print("✓ Anchor drag update added")
else:
    print("✗ Move handler not found")

# ============================================================
# FEATURE 4: Elevator resize
# ============================================================
# Schema already supports w/d (ELEV_W, ELEV_D constants).
# We add resize handles in drawElevs and resize drag.

# First, update proj.elevs.push to include w/d if not present
old_elev_push = "proj.elevs.push({id, x:sp.x, z:sp.z, rot:elevRot});"
new_elev_push = "proj.elevs.push({id, x:sp.x, z:sp.z, rot:elevRot, w:ELEV_W, d:ELEV_D});"
if old_elev_push in content:
    content = content.replace(old_elev_push, new_elev_push, 1)
    print("✓ Elevator w/d added to push")
else:
    print("✗ Elev push not found")

# Add pickElevEdge function before pickWall
old_pick_elev_func = "function drawElevs(){"
new_pick_elev_func = """function pickElevEdge(sx,sy){
  // بررسی لبه‌های آسانسور برای resize - فقط آسانسور انتخاب‌شده
  const ev=proj.elevs.find(x=>x.id===selId); if(!ev) return null;
  const w=(ev.w||ELEV_W), d=(ev.d||ELEV_D);
  const cos=Math.cos(ev.rot||0), sin=Math.sin(ev.rot||0);
  // ۴ گوشه محلی: (-w/2,-d/2), (w/2,-d/2), (w/2,d/2), (-w/2,d/2)
  const corners=[[-w/2,-d/2],[w/2,-d/2],[w/2,d/2],[-w/2,d/2]];
  const screenCorners=corners.map(([lx,lz])=>{
    const wx=ev.x + lx*cos - lz*sin;
    const wz=ev.z + lx*sin + lz*cos;
    return W2S({x:wx,z:wz});
  });
  // فاصله از هر گوشه
  for(let i=0;i<4;i++){
    const [px,py]=screenCorners[i];
    if(Math.hypot(sx-px,sy-py)<10) return {edge:'corner', corner:i, ev};
  }
  return null;
}

function drawElevs(){"""

if old_pick_elev_func in content:
    content = content.replace(old_pick_elev_func, new_pick_elev_func, 1)
    print("✓ pickElevEdge added")
else:
    print("✗ drawElevs not found")

# Add resize handles drawing in drawElevs
old_elev_draw = '''  for(const ev of proj.elevs){
    const [px,py]=W2S({x:ev.x,z:ev.z});
    const w=ELEV_W*view.zoom, d=ELEV_D*view.zoom;
    ctx.fillStyle=ev.id===selId?'#00ffcc33':'#7a8a9944';
    ctx.fillRect(px-w/2,py-d/2,w,d);
    ctx.strokeStyle=ev.id===selId?'#00ffcc':'#7a8a99';
    ctx.lineWidth=ev.id===selId?2:1.3;'''
new_elev_draw = '''  for(const ev of proj.elevs){
    const w=ev.w||ELEV_W, d=ev.d||ELEV_D;
    const [px,py]=W2S({x:ev.x,z:ev.z});
    const wPx=w*view.zoom, dPx=d*view.zoom;
    ctx.save();
    ctx.translate(px,py); ctx.rotate(-(ev.rot||0));
    ctx.fillStyle=ev.id===selId?'#00ffcc33':'#7a8a9944';
    ctx.fillRect(-wPx/2,-dPx/2,wPx,dPx);
    ctx.strokeStyle=ev.id===selId?'#00ffcc':'#7a8a99';
    ctx.lineWidth=ev.id===selId?2:1.3;
    ctx.strokeRect(-wPx/2,-dPx/2,wPx,dPx);
    if(ev.id===selId){
      // ۴ دستگیره تغییر سایز
      ctx.fillStyle='#00ffcc';
      const corners=[[-wPx/2,-dPx/2],[wPx/2,-dPx/2],[wPx/2,dPx/2],[-wPx/2,dPx/2]];
      for(const [cx,cy] of corners){
        ctx.beginPath(); ctx.arc(cx,cy,5,0,Math.PI*2); ctx.fill();
      }
    }
    ctx.restore();
    ctx.fillStyle=ev.id===selId?'#00ffcc':'#aaa';
    ctx.font='10px Tahoma'; ctx.textAlign='center';
    ctx.fillText('آسانسور', px, py+3);'''

if old_elev_draw in content:
    content = content.replace(old_elev_draw, new_elev_draw, 1)
    print("✓ Elevator resize handles added")
else:
    print("✗ Elevator draw not found")

# Add elevator resize drag in mousedown - look for elev drag
old_elev_drag = '''    else if((hit=pickElevW(w))){ selId=hit.id;
      if(lockedIds.has(hit.id)){ dragInfo=null; }
      else dragInfo={type:'elev', start:w, orig:{x:hit.x,z:hit.z}, origSnap:mkSnap(), moved:false}; }'''
new_elev_drag = '''    else if((edge=pickElevEdge(sx,sy))){ selId=edge.ev.id;
      dragInfo={type:'elev-resize', id:edge.ev.id, corner:edge.corner, orig:{x:edge.ev.x,z:edge.ev.z, w:edge.ev.w||ELEV_W, d:edge.ev.d||ELEV_D, rot:edge.ev.rot||0}, origSnap:mkSnap(), moved:false};
      showHint('درگ گوشه برای تغییر سایز — Alt = از مرکز، Shift = حفظ نسبت'); }
    else if((hit=pickElevW(w))){ selId=hit.id;
      if(lockedIds.has(hit.id)){ dragInfo=null; }
      else dragInfo={type:'elev', start:w, orig:{x:hit.x,z:hit.z}, origSnap:mkSnap(), moved:false}; }'''

if old_elev_drag in content:
    content = content.replace(old_elev_drag, new_elev_drag, 1)
    print("✓ Elevator resize drag added")
else:
    print("✗ Elevator drag not found")

# Add elevator resize update in mousemove
old_elev_move = '''    const nx2=dragInfo.orig.x+(mouseWorld.x-dragInfo.start.x), nz2=dragInfo.orig.z+(mouseWorld.z-dragInfo.start.z);
    const ev=proj.elevs.find(x=>x.id===selId); if(!ev) return;
    ev.x=nx2; ev.z=nz2; dragInfo.moved=true; refresh();
  }'''
new_elev_move = '''    const nx2=dragInfo.orig.x+(mouseWorld.x-dragInfo.start.x), nz2=dragInfo.orig.z+(mouseWorld.z-dragInfo.start.z);
    const ev=proj.elevs.find(x=>x.id===selId); if(!ev) return;
    ev.x=nx2; ev.z=nz2; dragInfo.moved=true; refresh();
  }
  else if(dragInfo&&dragInfo.type==='elev-resize'&&selId){
    const ev=proj.elevs.find(x=>x.id===selId); if(!ev) return;
    const o=dragInfo.orig;
    // گوشه فعلی بر اساس موقعیت ماوس
    const cos=Math.cos(o.rot), sin=Math.sin(o.rot);
    const lx0=(o.corner===0||o.corner===3)?-o.w/2:o.w/2;
    const lz0=(o.corner===0||o.corner===1)?-o.d/2:o.d/2;
    const wx0=o.x + lx0*cos - lz0*sin;
    const wz0=o.z + lx0*sin + lz0*cos;
    // اختلاف در مختصات محلی
    const dx=mouseWorld.x-wx0, dz=mouseWorld.z-wz0;
    const lx=dx*cos + dz*sin;
    const lz=-dx*sin + dz*cos;
    let nW=Math.max(0.6, Math.abs(lx)*2);
    let nD=Math.max(0.6, Math.abs(lz)*2);
    if(lastAlt){ // Alt = از مرکز
      nW=Math.max(0.6, Math.abs(lx));
      nD=Math.max(0.6, Math.abs(lz));
    }
    if(window.event && window.event.shiftKey){ // Shift = حفظ نسبت
      const r=Math.max(o.w, o.d);
      nW=nD=r;
    }
    ev.w=nW; ev.d=nD;
    // جابجایی مرکز اگر Alt نباشد
    if(!lastAlt){
      const lx1=(o.corner===0||o.corner===3)?-nW/2:nW/2;
      const lz1=(o.corner===0||o.corner===1)?-nD/2:nD/2;
      ev.x=wx0 - (lx1*cos - lz1*sin);
      ev.z=wz0 - (lx1*sin + lz1*cos);
    }
    dragInfo.moved=true; refresh();
  }'''

if old_elev_move in content:
    content = content.replace(old_elev_move, new_elev_move, 1)
    print("✓ Elevator resize update added")
else:
    print("✗ Elevator move not found")

# ============================================================
# Add btnFillet handler
# ============================================================
old_btn3d = "btn3D.onclick=()=>enter3D();"
new_btn3d = """btn3D.onclick=()=>enter3D();
btnFillet.onclick=()=>{ setTool('fillet'); showHint('فیلت — ۲ کلیک: گوشه اول/گوشه دوم، شعاع پیش‌فرض '+filletRadius.toFixed(2)+'m'); };"""

if old_btn3d in content:
    content = content.replace(old_btn3d, new_btn3d, 1)
    print("✓ btnFillet handler added")
else:
    print("✗ btn3D handler not found")

# Add fillet tool handling in mousedown - find the tool click handler
# The pattern is:  else if(tool==='elev'){
old_elev_tool = "  else if(tool==='elev'){"
new_elev_tool = """  else if(tool==='fillet'){
    const sp=snapPoint(w, e.altKey);
    filletPts.push([sp.x, sp.z]);
    if(filletPts.length===2){
      pushUndo();
      const nid='f'+(proj.nextId++);
      proj.fillets.push({id:nid, a:filletPts[0], b:filletPts[1], r:filletRadius});
      filletPts=[];
      selId=nid;
      showHint('فیلت ساخته شد — درگ برای جابجایی، دابل‌کلیک برای ویرایش');
    } else showHint('نقطه دوم فیلت؟');
    refresh();
  }
  else if(tool==='elev'){"""

if old_elev_tool in content:
    content = content.replace(old_elev_tool, new_elev_tool, 1)
    print("✓ Fillet tool click handler added")
else:
    print("✗ Tool elev not found")

# Update mkSnap to include fillets
old_snap = "function mkSnap(){ return JSON.stringify({walls:proj.walls,doors:proj.doors,columns:proj.columns,stairs:proj.stairs,elevs:proj.elevs,wells:proj.wells,balcs:proj.balcs,rails:proj.rails,zones:proj.zones,nextId:proj.nextId,planOff}); }"
new_snap = "function mkSnap(){ return JSON.stringify({walls:proj.walls,doors:proj.doors,columns:proj.columns,stairs:proj.stairs,elevs:proj.elevs,wells:proj.wells,balcs:proj.balcs,rails:proj.rails,zones:proj.zones,fillets:proj.fillets,nextId:proj.nextId,planOff}); }"

if old_snap in content:
    content = content.replace(old_snap, new_snap, 1)
    print("✓ mkSnap includes fillets")
else:
    print("✗ mkSnap not found")

# Update load function to handle fillets
old_load = "  const o=JSON.parse(s); proj.walls=o.walls; proj.doors=o.doors||[]; proj.columns=o.columns||[]; proj.stairs=o.stairs||[]; proj.elevs=o.elevs||[]; proj.wells=o.wells||[]; proj.balcs=o.balcs||[]; proj.rails=o.rails||[]; proj.zones=o.zones||[]; proj.nextId=o.nextId;"
new_load = "  const o=JSON.parse(s); proj.walls=o.walls; proj.doors=o.doors||[]; proj.columns=o.columns||[]; proj.stairs=o.stairs||[]; proj.elevs=o.elevs||[]; proj.wells=o.wells||[]; proj.balcs=o.balcs||[]; proj.rails=o.rails||[]; proj.zones=o.zones||[]; proj.fillets=o.fillets||[]; proj.nextId=o.nextId;"

if old_load in content:
    content = content.replace(old_load, new_load, 1)
    print("✓ Load includes fillets")
else:
    print("✗ Load not found")

# Update stCount update to include fillet count
old_count = '''  stCount.textContent=proj.walls.length;
  stOpen.textContent=proj.doors.length;'''
new_count = '''  stCount.textContent=proj.walls.length;
  stOpen.textContent=proj.doors.length;
  const stFilletEl=document.getElementById('stFillet');
  if(stFilletEl) stFilletEl.textContent=proj.fillets.length;'''

if old_count in content:
    content = content.replace(old_count, new_count, 1)
    print("✓ Fillet count display")
else:
    print("✗ Count display not found")

# ============================================================
# 3D Export: add fillets, free doors, anchor support
# ============================================================
# Update TPL world source - add fillet rendering
# Find the part: const fx=(bx0+bx1)/2,
# We'll add fillet drawing right after the floor/ceiling setup

old_3d_floor = "const fx=(bx0+bx1)/2, fz=(bz0+bz1)/2;"
new_3d_floor = "const fx=(bx0+bx1)/2, fz=(bz0+bz1)/2; const filletMat=new THREE.MeshStandardMaterial({color:0xff66cc,roughness:0.5,transparent:true,opacity:0.7});"

if old_3d_floor in content:
    content = content.replace(old_3d_floor, new_3d_floor, 1)
    print("✓ 3D fillet material added")
else:
    print("✗ 3D floor not found")

# Add fillet drawing in 3D - find the wall building section
old_3d_walls_start = "for(const w of D.walls){\n  const ax=w.a[0],az=w.a[1],bx=w.b[0],bz=w.b[1];\n  const L=Math.hypot(bx-ax,bz-az); if(L<0.01)continue;\n  const on=Math.atan2(bx-ax,bz-az); const ux=(bx-ax)/L,uz=(bz-az)/L;\n  const cuts=[0,1];\n  for(const o of (D.doors||[])) if(o.wallId===w.id){ cuts.push(o.t/L-o.w/2/L,o.t/L+o.w/2/L); }\n  cuts.sort((a,b)=>a-b);"

new_3d_walls_start = """for(const w of D.walls){
  const ax=w.a[0],az=w.a[1],bx=w.b[0],bz=w.b[1];
  const L=Math.hypot(bx-ax,bz-az); if(L<0.01)continue;
  const on=Math.atan2(bx-ax,bz-az); const ux=(bx-ax)/L,uz=(bz-az)/L;
  const cuts=[0,1];
  for(const o of (D.doors||[])) if(o.wallId===w.id && o.type!=='free'){ cuts.push(o.t/L-o.w/2/L,o.t/L+o.w/2/L); }
  cuts.sort((a,b)=>a-b);"""

if old_3d_walls_start in content:
    content = content.replace(old_3d_walls_start, new_3d_walls_start, 1)
    print("✓ 3D wall cut logic updated")
else:
    print("✗ 3D wall start not found")

# Add free door rendering - add before the final for loop
old_3d_doors_end = '''  for(const o of (D.doors||[])){ if(o.wallId!==w.id)continue;
    const c=o.t/L,cx=ax+(bx-ax)*c,cz=az+(bz-az)*c,ow=o.w;'''

new_3d_doors_end = '''  // Free doors: separate render pass
  for(const o of (D.doors||[])){
    if(o.type!=='free' || !o.a || !o.b) continue;
    const ax2=o.a[0],az2=o.a[1],bx2=o.b[0],bz2=o.b[1];
    const L2=Math.hypot(bx2-ax2,bz2-az2); if(L2<0.01)continue;
    const on2=Math.atan2(bx2-ax2,bz2-az2); const ux2=(bx2-ax2)/L2,uz2=(bz2-az2)/L2;
    const cx2=(ax2+bx2)/2, cz2=(az2+bz2)/2;
    if(o.type==='free'){
      addBox(cx2,H/2,cz2,W,H,L2,on2,wallMat);
    }
  }
  for(const o of (D.doors||[])){ if(o.wallId!==w.id||o.type==='free')continue;
    const c=o.t/L,cx=ax+(bx-ax)*c,cz=az+(bz-az)*c,ow=o.w;'''

if old_3d_doors_end in content:
    content = content.replace(old_3d_doors_end, new_3d_doors_end, 1)
    print("✓ 3D free door render added")
else:
    print("✗ 3D doors end not found")

# Add 3D fillet rendering
old_3d_elevs = "  for(const ev of (DATA.elevs||[])){\n    const EW=ev.w||1.6, ED=ev.d||1.7;\n    addBox(ev.x,H/2,ev.z,ED,H,EW,(ev.rot||0),new THREE.MeshStandardMaterial({color:0x8a8f94,roughness:.6}));\n  }"
new_3d_elevs = """  for(const ev of (DATA.elevs||[])){
    const EW=ev.w||1.6, ED=ev.d||1.7;
    addBox(ev.x,H/2,ev.z,ED,H,EW,(ev.rot||0),new THREE.MeshStandardMaterial({color:0x8a8f94,roughness:.6}));
  }
  // فیلت‌ها - نمایش به صورت نیم‌استوانه
  for(const f of (DATA.fillets||[])){
    const ax=f.a[0],az=f.a[1],bx=f.b[0],bz=f.b[1];
    const fx2=(ax+bx)/2, fz2=(az+bz)/2;
    const r=f.r||0.3;
    const cyl=new THREE.Mesh(new THREE.CylinderGeometry(r,r,H,16,1,true),filletMat);
    cyl.position.set(fx2,H/2,fz2);
    scene.add(cyl);
  }"""

if old_3d_elevs in content:
    content = content.replace(old_3d_elevs, new_3d_elevs, 1)
    print("✓ 3D fillet rendering added")
else:
    print("✗ 3D elevs not found")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f"Final size: {len(content)} bytes")
