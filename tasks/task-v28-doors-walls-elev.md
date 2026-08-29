# HOVI v28 — درب آزاد + دیوار صاف/فیلت + انکر دیوار + ریسایز آسانسور

## قانون طلایی
- الگوی پیاده‌سازی = کد موجود editor_v1.html. قبل از هر تغییر grep کن:
  - درب: `openingPos`, `pickOpening`, `drawOpenings`, `openDoorEdit`, `dragInfo={type:'open'`
  - دیوار 2D: `drawWalls` (lineCap)؛ دیوار 3D: `buildWall` + `addBox` (داخل رشتهٔ M3_WORLD_SRC — escaping را به‌هم نزن!)
  - آسانسور: `pickElevW`, `drawElevs`, `dragInfo={type:'elev'`
- پچ فقط با rep(old,new) + assert count. تست‌ها: /tmp/pwshot (acorn آنجاست).

## فیچر ۱ — درب بین‌دیواری (آزاد)
- ابزار door: بعد از pickWall شکست → حالت دوم: کلیک اول نزدیک **سرِ** یک دیوار (مگنت سر، شعاع MAGNET) → ذخیره در متغیر `freeDoorA` + hint «کلیک دوم: سرِ دیوار مقابل» → کلیک دوم نزدیک سرِ دیوار دیگر → درب آزاد:
  `proj.doors.push({id:'o'+nextId++, free:true, type:doorType, a:[ax,az], b:[bx,bz], w, swing:1, hinge:1})` — بدون wallId/t
- اگر دو سر روی یک دیوار باشند = خطا «روی یک دیوار نمی‌شود»
- openingPos: اگر op.free → مستقیم از a/b محاسبه (dx/nx از خود بازشو)
- drawOpenings/pickOpening/درگ/Panl(openDoorEdit)/F لولا: همه با op.free سازگار شود (openDoorEdit از op.t استفاده می‌کند — برای free: t=0 و درگ = جابجایی کل با نصف-عرض مگنت به سر دیوارها)
- 3D/GLB: در buildWall و تور (TPL world1) حلقهٔ جدا: برای op.free — قاب + لنگه بین a و b (زاویه از خود a/b)؛ مش‌ها با پیشوند `freedoor_`؛ برش دیوار لازم نیست (بین دو دیوار است)
- Del/undo/serialize/load/locks همه از قبل generic روی proj.doors — فقط سازگاری openingPos/Pick

## فیچر ۲ — سرِ صاف دیوار + فیلت دستی
- drawWalls: `lineCap='round'` → `'butt'` + پرکردن مربع اتصال: در انتهای هر دیوارِ متصل (سر مشترک با دیوار دیگر) مربع WALL_T×WALL_T حول سر رسم شود (fill همان رنگ دیوار) تا گوشه توپر صاف شود — 2D
- 3D: addBox دیوار طول کامل دارد ولی در گوشهٔ L گپ زاویه‌ای می‌ماند: برای هر سرِ دیوار که به سر دیوار دیگر می‌چسبد (فاصله < 0.02)، یک باکس مکمل ابعاد W×W×H در همان نقطه اضافه شود (پیشوند مش `wallcap_`)
- ابزار فیلت دستی: دکمهٔ جدید «⌒ فیلت» (مثل ابزار rail): کلیک روی **گوشهٔ مشترک دو دیوار** (مگنت سرها) → ورودی شعاع (پنل کوچک، نه prompt) → آرک 2D: خطوط دیوار نزدیک گوشه کوتاه + قوس؛ 3D: باکس‌های دیوار کوتاه + سیلندر ربع‌قوس (wallMat). داده: `proj.fillets=[{id, corner:[x,z], r}]` — serialize/load/undo/Del/درگ کامل. حداکثر r = min(طول هر دو دیوار)/2

## فیچر ۳ — انکر پوینت سر دیوار
- دیوار انتخابی یا hover: دو مربع 7px روی سرها (fill #00ffcc، بورد مشکی). فقط وقتی selId دیوار است
- hit-test انکر قبل از بقیه در mousedown؛ درگ انکر: سر a یا b = موقعیت موس (با snapPoint مگنت + Shift=orthoLock نسبت به سر دیگر)؛ pushUndo در شروع درگ
- بازشوها: op.t نسبت به a است — با تغییر طول دیوار، op.t مقیاس شود: op.t = op.t/L_old*L_new (کلمپ)
- 3D/GLB/طول نوشته — خودکار

## فیچر ۴ — ریسایز آسانسور
- schema: elevs += w,d (پیش‌فرض ELEV_W/ELEV_D)
- hover گوشه/لبه شفت (با rot) → cursor ew/ns/ns-resize؛ درگ لبه = یک‌طرفه (لبهٔ مقابل ثابت): محاسبه در مختصات محلی rot-دار؛ Alt = یکنواخت از مرکز (هر دو لبه)، Shift = اسنپ ۱۰cm
- حداقل 1.0×1.0؛ حین درگ hint زنده `1.6×1.7m`
- 3D/GLB از ev.w/ev.d می‌خوانند (آماده)
- test: ویرایش w/d → 3D مش عریض‌تر

## تست (Playwright) — test_v28.js
1. درب آزاد: دو دیوار جدا → کلیک سر A، سر B → doors[-1].free===true، رندر قوس؛ Del؛ undo
2. فیلت: گوشهٔ دو دیوار → قوس رسم (pixel check اختیاری)، proj.fillets len 1
3. انکر: درگ سر b دیوار → زاویه عوض شود، بازشو op.t مقیاس شده
4. آسانسور: درگ لبه → فقط یک بعد؛ Alt → مرکز ثابت؛ Shift → مضرب ۰.۱
5. رگرسیون: v21/v22b/v23d/v23j/v24/v25_panel/v26/v27 + acorn

## خروجی
- editor_v1.html فقط؛ تحویل بعدی جدا ساخته می‌شود (hovi_editor-v28.html + بج)
