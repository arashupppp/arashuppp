const THREE=window.THREE3;
/* HOVI 3D world — v20 (بازنویسی ابزارهای ساخت از wcfix-v2 روی دادهٔ HOVI) */
function createWorld(container, DATA, onSync, onHint){
  const H=2.8, W=0.2, EYE=1.6, WALK=2.6, RUN=1.8;
  const scene=new THREE.Scene(); scene.background=new THREE.Color(0x87ceeb);
  const camera=new THREE.PerspectiveCamera(70,innerWidth/innerHeight,0.05,200);
  camera.position.set(1,EYE,1);
  const renderer=new THREE.WebGLRenderer({antialias:true});
  renderer.setSize(innerWidth,innerHeight);
  renderer.shadowMap.enabled=true; renderer.shadowMap.type=THREE.PCFSoftShadowMap;
  renderer.outputColorSpace=THREE.SRGBColorSpace; renderer.toneMapping=THREE.ACESFilmicToneMapping;
  container.appendChild(renderer.domElement);

  const amb=new THREE.AmbientLight(0xffffff,.55); scene.add(amb);
  const hemi=new THREE.HemisphereLight(0xbfd8ff,0x8a7a66,.45); scene.add(hemi);
  const sun=new THREE.DirectionalLight(0xffeecc,1.4); sun.castShadow=true;
  sun.shadow.mapSize.set(2048,2048);
  Object.assign(sun.shadow.camera,{left:-20,right:20,top:20,bottom:-20,near:.5,far:80});
  scene.add(sun);

  // ==== خورشید (۰–۲۴ مثل تور HOVI) ====
  let tod=12;
  function updateSun(){
    const t=(tod%24)/24, ang=(t-0.25)*Math.PI*2, sh=Math.sin(ang);
    const skyMix=THREE.MathUtils.clamp((sh+0.3)/1.3,0,1);
    scene.background=new THREE.Color(0x080820).lerp(new THREE.Color(0x87ceeb),skyMix);
    sun.position.set(40*Math.cos(ang),40*Math.max(0.1,sh),40*Math.sin(ang));
    sun.intensity=THREE.MathUtils.clamp(sh*1.3,0.15,1.4);
    amb.intensity=THREE.MathUtils.clamp(0.2+sh*0.6,0.12,0.75);
    hemi.intensity=0.12+skyMix*0.38;
  }
  updateSun();
  const setTOD=v=>{tod=v;updateSun();};

  // ==== زمین ====
  let bx0=1e9,bx1=-1e9,bz0=1e9,bz1=-1e9;
  for(const w of DATA.walls){bx0=Math.min(bx0,w.a[0],w.b[0]);bx1=Math.max(bx1,w.a[0],w.b[0]);bz0=Math.min(bz0,w.a[1],w.b[1]);bz1=Math.max(bz1,w.a[1],w.b[1]);}
  if(!DATA.walls.length){bx0=-5;bx1=5;bz0=-5;bz1=5;}
  const fx=(bx0+bx1)/2,fz=(bz0+bz1)/2;
  const floor=new THREE.Mesh(new THREE.PlaneGeometry(bx1-bx0+6,bz1-bz0+6),new THREE.MeshStandardMaterial({color:0xdad5cc,roughness:.95}));
  floor.rotation.x=-Math.PI/2; floor.position.set(fx,0,fz); floor.receiveShadow=true; scene.add(floor);

  const wallMat=new THREE.MeshStandardMaterial({color:0xd8d2c8,roughness:.75});
  const doorMat=new THREE.MeshStandardMaterial({color:0x8a6b46,roughness:.6});
  const ghostMat=new THREE.MeshBasicMaterial({color:0x00ffcc,transparent:true,opacity:.35});
  const collid=[], interact=[];

  function addBox(x,y,z,lx,ly,lz,ry,mat,solid=true){
    const m=new THREE.Mesh(new THREE.BoxGeometry(lx,ly,lz),mat);
    m.position.set(x,y,z); if(ry)m.rotation.y=ry;
    m.castShadow=true; m.receiveShadow=true; scene.add(m);
    if(solid)collid.push(m);
    return m;
  }
  // ==== دیوارهای داده با گپ درب‌ها ====
  function buildWall(w){
    const ax=w.a[0],az=w.a[1],bx=w.b[0],bz=w.b[1];
    const L=Math.hypot(bx-ax,bz-az); if(L<0.01)return;
    const on=Math.atan2(bx-ax,bz-az), ux=(bx-ax)/L, uz=(bz-az)/L;
    const cuts=[0,1];
    for(const o of (DATA.doors||[])) if(o.wallId===w.id) cuts.push(o.t/L-o.w/2/L, o.t/L+o.w/2/L);
    cuts.sort((a,b)=>a-b);
    for(let i=0;i<cuts.length-1;i++){
      const s0=Math.max(0,cuts[i]), s1=Math.min(1,cuts[i+1]);
      if(s1-s0<0.02)continue;
      const p1x=ax+(bx-ax)*s0,p1z=az+(bz-az)*s0,p2x=ax+(bx-ax)*s1,p2z=az+(bz-az)*s1;
      addBox((p1x+p2x)/2,H/2,(p1z+p2z)/2,W,H,Math.hypot(p2x-p1x,p2z-p1z),on,wallMat);
    }
    // درب‌های موجود: قاب + لنگهٔ انیمیشنی
    for(const o of (DATA.doors||[])){
      if(o.wallId!==w.id)continue;
      const c=o.t/L, cx=ax+(bx-ax)*c, cz=az+(bz-az)*c, ow=o.w;
      if(o.type==='open'){ continue; } // بازشوی بدون درب: هیچ
      if(o.type==='slide'){
        // کشویی: لنگهٔ ثابت سرتاسری داخل دیوار
        const leafS=new THREE.Mesh(new THREE.BoxGeometry(ow,2.1,0.05),doorMat);
        leafS.position.set(cx,1.05,cz); leafS.rotation.y=on; leafS.castShadow=true;
        scene.add(leafS); continue;
      }
      addBox(cx-ux*ow/2,H/2,cz-uz*ow/2,W/2,H,0.06,on,wallMat);
      addBox(cx+ux*ow/2,H/2,cz+uz*ow/2,W/2,H,0.06,on,wallMat);
      addBox(cx,H-0.05,cz,W/2,H,0.06,on,wallMat);
      const halfW=(o.type==='double')?ow/2:ow;
      const hingeSign=(o.hinge||1), swingSign=(o.swing||1);
      const leaf2=new THREE.Mesh(new THREE.BoxGeometry(halfW,2.1,0.05),doorMat);
      const pivot=new THREE.Group();
      if(o.type==='double'){
        // دولنگه: دو pivot قرینه
        const pivA=new THREE.Group(); pivA.position.set(cx-ux*ow/2,0,cz-uz*ow/2);
        const la=new THREE.Mesh(new THREE.BoxGeometry(halfW,2.1,0.05),doorMat);
        la.position.set(ux*halfW/2,1.05,0); la.castShadow=true;
        pivA.add(la); pivA.rotation.y=on; scene.add(pivA);
        pivA.userData={open:false,targetRot:on}; interact.push(pivA);
        const pivB=new THREE.Group(); pivB.position.set(cx+ux*ow/2,0,cz+uz*ow/2);
        const lb=la.clone(); lb.position.set(-ux*halfW/2,1.05,0);
        pivB.add(lb); pivB.rotation.y=on; scene.add(pivB);
        pivB.userData={open:false,targetRot:-on}; interact.push(pivB);
      } else {
        // تک‌لنگه: لولا سمت hinge، بازشو به سمت swing
        pivot.position.set(cx-ux*ow/2*hingeSign,0,cz-uz*ow/2*hingeSign);
        leaf2.position.set(ux*ow/2*hingeSign,1.05,0); leaf2.castShadow=true;
        pivot.add(leaf2); pivot.rotation.y=on; scene.add(pivot);
        pivot.userData={open:false,targetRot:on*swingSign};
        interact.push(pivot);
      }
    }
  }
  for(const w of DATA.walls)buildWall(w);
  for(const c of (DATA.columns||[])){
    const xs=c.pts.map(p=>p[0]),zs=c.pts.map(p=>p[1]);
    const cx=(Math.min(...xs)+Math.max(...xs))/2, cz=(Math.min(...zs)+Math.max(...zs))/2;
    const lw=Math.max(...xs)-Math.min(...xs), ld=Math.max(...zs)-Math.min(...zs);
    addBox(cx,H/2,cz,lw,H,ld,0,new THREE.MeshStandardMaterial({color:0x9a9a9a,roughness:.8}));
  }
  for(const s of (DATA.stairs||[])){
    const ax=s.a[0],az=s.a[1],bx=s.b[0],bz=s.b[1];
    const dx=bx-ax,dz=bz-az,L=Math.hypot(dx,dz);
    if(!(L>0.05))continue;
    const ry=Math.atan2(-(dz),dx); // rotation.y برای BoxGeometry (x به x، z به -z)
    const hw=(s.w||1)/2, Hs=s.h||2.8, n=Math.max(2,Math.round(Hs/0.18));
    const tread=L/n, rise=Hs/n;
    const smat=new THREE.MeshStandardMaterial({color:0xb0b0b0,roughness:.75});
    for(let i=0;i<n;i++){
      const cx=ax+dx*(i+0.5)/n, cz=az+dz*(i+0.5)/n, top=(i+1)*rise;
      addBox(cx,top/2,cz,tread,top,(s.w||1),ry,smat);
    }
  }
  for(const ev of (DATA.elevs||[])){
    const EW=ev.w||1.6, ED=ev.d||1.7;
    addBox(ev.x,H/2,ev.z,ED,H,EW,(ev.rot||0),new THREE.MeshStandardMaterial({color:0x8a8f94,roughness:.6}));
  }

  // ==== کنترل ====
  // کنترل دستی: pointer lock + yaw/pitch (بدون PLC — سازگار با file://)
  const controls={isLocked:false};
  const keys={}; const euler={y:0,x:0};
  const dom=renderer.domElement;
  dom.addEventListener('click',()=>{ if(!controls.isLocked) dom.requestPointerLock(); });
  const plc=()=>controls.isLocked=!!document.pointerLockElement;
  document.addEventListener('pointerlockchange',plc);
  const mmove=e=>{ if(!controls.isLocked)return;
    euler.y-=e.movementX*0.0022; euler.x-=e.movementY*0.0022;
    euler.x=Math.max(-1.55,Math.min(1.55,euler.x));
    camera.rotation.set(euler.x,euler.y,0,'YXZ');
  };
  addEventListener('mousemove',mmove);
  const kd=e=>{keys[e.code]=true;
    if(e.code==='KeyF'&&controls.isLocked)toggleDoor();
  };
  const ku=e=>{keys[e.code]=false;};
  addEventListener('keydown',kd); addEventListener('keyup',ku);

  function toggleDoor(){
    const ray=new THREE.Raycaster();
    ray.setFromCamera(new THREE.Vector2(0,0),camera);
    const hits=ray.intersectObjects(interact,true);
    if(hits.length&&hits[0].distance<4){
      let g=hits[0].object; while(g&&!g.userData.targetRot!==undefined&&g.parent)g=g.parent;
      if(g.userData){g.userData.open=!g.userData.open;
        g.userData.targetRot=g.userData.open?g.userData.baseRot!==undefined?g.userData.baseRot-Math.PI/2:((g.rotation.y||0)-Math.PI/2):(g.userData.baseRot??g.rotation.y);
        if(g.userData.baseRot===undefined)g.userData.baseRot=g.userData.open?g.userData.targetRot+Math.PI/2:g.userData.targetRot;
      }
    }
  }
  // ساده‌سازی: درب نزدیک × دوران نرم
  const animated=[];
  for(const p of interact)animated.push(p);

  // ==== ابزار ساخت (بازنویسی wcfix) ====
  let tool='none', buildStep=0, startP=null;
  const ghost=new THREE.Mesh(new THREE.BoxGeometry(1,0.2,0.1),ghostMat);
  ghost.visible=false; scene.add(ghost);
  const SPRAY=[0xff4444,0x44ff44,0x4488ff,0xffee44,0xff44ff,0x44ffff,0xffffff,0x222222];
  let sprayIdx=0;
  function setTool(t){
    tool=t; buildStep=0; startP=null; ghost.visible=false;
    document.querySelectorAll('.m3t').forEach(b=>{
      const on=b.dataset.t===t;
      b.style.background=on?'#ffcc00':'#333';
      b.style.color=on?'#000':'#ccc';
    });
    onHint(t==='wall'?'دیوار: ۲ کلیک — راست‌کلیک لغو':
           t==='door'?'درب: کلیک روی دیوار (آهنربا)':
           t==='spray'?'اسپری: نگه‌دار و بکش — Q رنگ بعدی':'نگاه آزاد');
  }
  document.querySelectorAll('.m3t').forEach(b=>b.onclick=()=>setTool(b.dataset.t));

  // اسپری
  let spraying=false;
  const sprayTex=(()=>{const c=document.createElement('canvas');c.width=c.height=64;
    const g=c.getContext('2d');const gr=g.createRadialGradient(32,32,4,32,32,30);
    gr.addColorStop(0,'rgba(255,255,255,1)');gr.addColorStop(1,'rgba(255,255,255,0)');
    g.fillStyle=gr;g.fillRect(0,0,64,64);return new THREE.CanvasTexture(c);})();
  function sprayAt(){
    const ray=new THREE.Raycaster();
    ray.setFromCamera(new THREE.Vector2(0,0),camera);
    const hits=ray.intersectObjects(collid);
    if(!hits.length||hits[0].distance>6)return;
    const p=hits[0].point.clone().addScaledVector(hits[0].face.normal,0.012);
    const s=new THREE.Sprite(new THREE.SpriteMaterial({map:sprayTex,color:SPRAY[sprayIdx],transparent:true,opacity:.9,depthWrite:false}));
    s.scale.set(.35,.35,1); s.position.copy(p); scene.add(s);
    api.history.push({type:'spray',obj:s});
  }

  // ساخت دیوار/درب روی دیوارها یا زمین
  function pickPoint(){
    const ray=new THREE.Raycaster();
    ray.setFromCamera(new THREE.Vector2(0,0),camera);
    const hits=ray.intersectObjects([...collid,floor]);
    return hits.length?hits[0].point:null;
  }
  function snapG(v){return Math.round(v*2)/2;} // گرید ۵۰cm مثل wcfix
  function clickBuild(){
    const p=pickPoint(); if(!p)return;
    if(tool==='wall'){
      const np=new THREE.Vector3(snapG(p.x),0,snapG(p.z));
      if(buildStep===0){startP=np;buildStep=1;ghost.visible=true;onHint('نقطهٔ دوم؟');}
      else{
        const dx=np.x-startP.x,dz=np.z-startP.z;
        if(Math.abs(dx)>=Math.abs(dz))np.z=startP.z; else np.x=startP.x; // گونیا
        if(Math.hypot(dx,dz)>0.4){
          const mesh=addBox((startP.x+np.x)/2,H/2,(startP.z+np.z)/2,W,H,Math.hypot(np.x-startP.x,np.z-startP.z),Math.atan2(np.x-startP.x,np.z-startP.z),wallMat);
          api.history.push({type:'wall3d',obj:mesh});
          api.built.walls.push({a:[startP.x,startP.z],b:[np.x,np.z]});
          onSync();
        }
        buildStep=0;startP=null;ghost.visible=false;
      }
    }else if(tool==='door'){
      // آهنربا: نزدیک‌ترین دیوار داده/ساخته‌شده
      let best=null,bd=1e9;
      const allWalls=DATA.walls.concat(api.built.walls.map((w,i)=>({a:w.a,b:w.b})));
      for(const w of allWalls){
        const dx=w.b[0]-w.a[0],dz=w.b[1]-w.a[1],L2=dx*dx+dz*dz;if(L2<1e-9)continue;
        let t=((p.x-w.a[0])*dx+(p.z-w.a[1])*dz)/L2;t=THREE.MathUtils.clamp(t,0.1,0.9);
        const cx=w.a[0]+dx*t,cz=w.a[1]+dz*t,d=Math.hypot(p.x-cx,p.z-cz);
        if(d<bd){bd=d;best={w,t,cx,cz,L:Math.sqrt(L2)};}
      }
      if(best&&bd<0.9){
        const ow=0.9;
        const ux=(best.w.b[0]-best.w.a[0])/best.L, uz=(best.w.b[1]-best.w.a[1])/best.L;
        addBox(best.cx-ux*ow/2,H/2,best.cz-uz*ow/2,W/2,H,0.06,Math.atan2(ux,uz),wallMat);
        addBox(best.cx+ux*ow/2,H/2,best.cz+uz*ow/2,W/2,H,0.06,Math.atan2(ux,uz),wallMat);
        addBox(best.cx,H-0.05,best.cz,W/2,H,0.06,Math.atan2(ux,uz),wallMat);
        const pivot=new THREE.Group();pivot.position.set(best.cx-ux*ow/2,0,best.cz-uz*ow/2);
        const leaf=new THREE.Mesh(new THREE.BoxGeometry(ow,2.1,0.05),doorMat);
        leaf.position.set(ux*ow/2,1.05,0);leaf.castShadow=true;
        pivot.add(leaf);const on=Math.atan2(ux,uz);pivot.rotation.y=on;
        pivot.userData={open:false,targetRot:on,baseRot:on};scene.add(pivot);interact.push(pivot);animated.push(pivot);
        api.built.doors.push({wall:{a:best.w.a,b:best.w.b},t:best.t*best.L,w:ow});
        api.history.push({type:'door3d',obj:pivot});
        onSync();
        onHint('درب نصب شد — F باز/بسته');
      }else onHint('نزدیک دیوار کلیک کن');
    }
  }

  // ==== ورود/خروج ====
  const blk=document.getElementById('m3blk');
  const enter=()=>{dom.requestPointerLock();blk.style.display='none';};
  blk.addEventListener('click',enter);
  document.addEventListener('pointerlockchange',()=>{ if(!document.pointerLockElement) blk.style.display='flex'; });

  // ==== رویدادها ====
  const md=e=>{
    if(!controls.isLocked)return;
    if(e.button===0){
      if(tool==='spray')spraying=true;
      else if(tool==='wall'||tool==='door')clickBuild();
    }else if(e.button===2&&tool==='wall'){buildStep=0;startP=null;ghost.visible=false;onHint('لغو شد');}
  };
  const mu=()=>spraying=false;
  const mm=()=>{ if(spraying)sprayAt();
    if(tool==='wall'&&buildStep===1){
      const p=pickPoint();
      if(p){const dx=snapG(p.x)-startP.x,dz=snapG(p.z)-startP.z;
        let ex=snapG(p.x),ez=snapG(p.z);
        if(Math.abs(dx)>=Math.abs(dz))ez=startP.z;else ex=startP.x;
        const L=Math.hypot(ex-startP.x,ez-startP.z);
        ghost.scale.set(W,L,0.12);ghost.position.set((startP.x+ex)/2,H/2,(startP.z+ez)/2);
        ghost.rotation.y=Math.atan2(ex-startP.x,ez-startP.z);ghost.visible=L>0.3;}
    }};
  renderer.domElement.addEventListener('mousedown',md);
  addEventListener('mouseup',mu);
  addEventListener('mousemove',mm);
  const ctxmenu=e=>e.preventDefault();
  addEventListener('contextmenu',ctxmenu);
  const keyQ=e=>{if(e.code==='KeyQ'&&controls.isLocked){sprayIdx=(sprayIdx+1)%SPRAY.length;onHint('رنگ اسپری: '+['قرمز','سبز','آبی','زرد','صورتی','فیروزه‌ای','سفید','مشکی'][sprayIdx]);}};
  addEventListener('keydown',keyQ);

  // ==== حرکت ====
  const clock=new THREE.Clock();
  let raf;
  function anim(){
    raf=requestAnimationFrame(anim);
    const dt=Math.min(clock.getDelta(),.05);
    for(const g of animated){
      if(g.userData.targetRot===undefined)continue;
      const d=g.userData.targetRot-g.rotation.y;
      if(Math.abs(d)>0.001)g.rotation.y+=d*Math.min(1,dt*8);
    }
    if(controls.isLocked){
      const v=new THREE.Vector3();
      if(keys['KeyW'])v.z-=1;if(keys['KeyS'])v.z+=1;
      if(keys['KeyA'])v.x-=1;if(keys['KeyD'])v.x+=1;
      if(v.lengthSq()){
        v.normalize();
        if(keys['ShiftLeft']||keys['ShiftRight'])v.multiplyScalar(RUN);
        v.applyQuaternion(camera.quaternion);v.y=0;v.normalize();
        // برخورد ساده: گام بعدی داخل هیچ باکسی نباشد
        const nx=camera.position.x+v.x*WALK*dt, nz=camera.position.z+v.z*WALK*dt;
        if(!hitsAt(nx,camera.position.z))camera.position.x=nx;
        if(!hitsAt(camera.position.x,nz))camera.position.z=nz;
      }
      camera.position.y=EYE;
    }
    renderer.render(scene,camera);
  }
  function hitsAt(x,z){
    for(const c of collid){
      if(Math.abs(EYE-c.position.y)>H/2+0.1)continue;
      // مختصات محلی باکس با توجه به چرخش y
      const dx=x-c.position.x, dz=z-c.position.z;
      const ry=-c.rotation.y;
      const lx=dx*Math.cos(ry)-dz*Math.sin(ry), lz=dx*Math.sin(ry)+dz*Math.cos(ry);
      const px=c.geometry.parameters.width/2+0.25, pz=c.geometry.parameters.depth/2+0.25;
      if(Math.abs(lx)<px&&Math.abs(lz)<pz)return true;
    }
    return false;
  }
  anim();

  const api={
    history:[],built:{walls:[],doors:[]},
    setTOD,
    dispose(){cancelAnimationFrame(raf);
      removeEventListener('keydown',kd);removeEventListener('keyup',ku);
      removeEventListener('keydown',keyQ);removeEventListener('mouseup',mu);
      removeEventListener('mousemove',mm);removeEventListener('contextmenu',ctxmenu);
      renderer.dispose();container.innerHTML='';},
    getBuilt(){return api.built;},
    debugBuildWall(ax,az,bx,bz){
      // همان منطق clickBuild دیوار — برای تست headless
      const s=new THREE.Vector3(ax,0,az), e=new THREE.Vector3(bx,0,bz);
      const mesh=addBox((s.x+e.x)/2,H/2,(s.z+e.z)/2,W,H,Math.hypot(e.x-s.x,e.z-s.z),Math.atan2(e.x-s.x,e.z-s.z),wallMat);
      api.history.push({type:'wall3d',obj:mesh});
      api.built.walls.push({a:[s.x,s.z],b:[e.x,e.z]});
      return api.built.walls.length;
    },
    debugBuildDoor(ax,az,bx,bz,t,ow){
      const w={a:[ax,az],b:[bx,bz]}; const L=Math.hypot(bx-ax,bz-az);
      const ux=(bx-ax)/L, uz=(bz-az)/L;
      const cx=ax+(bx-ax)*t, cz=az+(bz-az)*t;
      addBox(cx-ux*ow/2,H/2,cz-uz*ow/2,W/2,H,0.06,Math.atan2(ux,uz),wallMat);
      addBox(cx+ux*ow/2,H/2,cz+uz*ow/2,W/2,H,0.06,Math.atan2(ux,uz),wallMat);
      addBox(cx,H-0.05,cz,W/2,H,0.06,Math.atan2(ux,uz),wallMat);
      const pivot=new THREE.Group();pivot.position.set(cx-ux*ow/2,0,cz-uz*ow/2);
      const leaf=new THREE.Mesh(new THREE.BoxGeometry(ow,2.1,0.05),doorMat);
      leaf.position.set(ux*ow/2,1.05,0);leaf.castShadow=true;
      pivot.add(leaf);const on=Math.atan2(ux,uz);pivot.rotation.y=on;
      pivot.userData={open:false,targetRot:on,baseRot:on};scene.add(pivot);interact.push(pivot);animated.push(pivot);
      api.built.doors.push({wall:{a:w.a,b:w.b},t:t*L,w:ow});
      return api.built.doors.length;
    },
    debugSpray(){ sprayAt(); return api.history.filter(h=>h.type==='spray').length; },
    debugLook(yaw,pitch){ euler.y=yaw; euler.x=pitch||0; camera.rotation.set(euler.x,euler.y,0,'YXZ'); },
    debugPos(x,z){ camera.position.set(x,EYE,z); }
  };
  var apiRef=api;
  return api;
}
window.__createWorld3=createWorld;
