# HOVI v26 — فاز ۳: بالکن + نرده (کامل با 3D و GLB)

## قانون طلایی (تجربهٔ v25)
- الگوی پیاده‌سازی = **دقیقاً همان چک‌لیست نورباز (wells) که در v24 اضافه شد**. برای یافتن همهٔ نقاط اتصال grep کن: `well`
  - دادهٔ proj، serialize (همه جاها)، load (btnLoad + syncBack)، Delete (۲ مکان)، دکمهٔ تولبار، setTool+hint، pickWellW، drawWells، preview، dragInfo، m3 world، GLTF (`well_`)، TPL
- پچ جراحی: `rep(old,new)` با `assert src.count(old)==cnt`. **تابع تکراری تعریف نکن** (در v25 دوبار openStairEdit تعریف شده بود — اشتباه فاحش)
- داخل رشتهٔ TPL هرگز `</script>` خام و فارسیِ غیر\uXXXX ننویس — از الگوی escapes موجود TPL پیروی کن
- فقط `/root/hovi/editor_v1.html` را تغییر بده. تست‌ها در `/tmp/pwshot/`

## ۱) داده
```js
proj.balcs = [{id:'b'+n, pts:[[x,z],...>=3]}]   // چندضلعی بستهٔ بالکن
proj.rails = [{id:'r'+n, pts:[[x,z],...>=2]}]   // پلی‌لاین نرده
```
- serialize: `balcs:proj.balcs,rails:proj.rails` به همهٔ serializeها اضافه شود (grep `elevs:proj.elevs` — همه را پیدا کن)
- load دو مکان: کنار `proj.wells=o.wells||[]` → `proj.balcs=o.balcs||[]; proj.rails=o.rails||[];`
- Delete دو مکان: کنار فیلتر wells → فیلتر balcs و rails
- undo: اگر pushUndo از serialize استفاده می‌کند خودکار است — **تست کن**، اگر نه اضافه کن

## ۲) ابزار بالکن (tool 'balc')
- دکمهٔ `btnBalc` «⬒ بالکن» کنار btnWell + کلید عددی بعدیِ آزاد (ببین کدام اعداد آزادند)
- نصب زنجیره‌ای مثل دیوار: balcPts؛ کلیک=گوشهٔ بعد؛ **Enter یا dblclick=بستن** (≥۳ گوشه)؛ راست‌کلیک/Esc=لغو؛ Shift=گونیا نسبت به گوشهٔ قبل
- hint: «کلیک: گوشهٔ بالکن — Enter: پایان» / «حداقل ۳ گوشه»
- 2D (تابع drawBalcs در refresh): fill نیمه‌شفاف + هاشور مورب ۴۵° داخل polygon (canvas clip) + خط دولا روی محیط (نماد نرده) + برچسب «بالکن» در مرکز
- درگ: انتقال کل polygon (dragInfo type 'balc' — الگوی well)؛ Del؛ قفل `~` (lockedIds) پشتیبانی شود

## ۳) ابزار نرده (tool 'rail')
- دکمهٔ `btnRail` «⌒ نرده» + کلید عددی آزاد بعدی
- زنجیره‌ای مثل دیوار: کلیک‌ها = نقاط شکست؛ راست‌کلیک = پایان (≥۲ نقطه)؛ Esc=لغو کامل؛ Shift=گونیا
- 2D: خط دولای موازی (فاصله ±۰٫۰۶m) + خط‌چین وسط؛ رنگ متمایز (سبزآبی تیره)
- درگ انتقال کل، Del، قفل، undo

## ۴) 3D ادیتور (M3_WORLD_SRC)
- DATA.balcs / DATA.rails خوانده شود
- بالکن: کف ExtrudeGeometry (depth 0.12m) از polygon + نرده روی هر ضلع: پایه‌ها (استوانه r=0.02 هر ≤1.2m) + دست‌انداز box 0.06×0.05 در h=1.0 + میلهٔ میانی h=0.5
- rail: همان سازندهٔ نرده روی polyline
- نام‌گذاری مش‌ها با پیشوند `balc_` و `rail_`

## ۵) GLTF (hoviBuildGLTF)
- mat جدید: 4=rail (فلز تیره)، 5=tile (خاکستری روشن) — لیست mats انتهای builder کامل شود
- تابع addTri (آینهٔ addBox برای مثلث) برای مثلث‌بندی fan کف بالکن از مرکز
- نرده: هر ضلع = addBox دست‌انداز با yaw=atan2 + پایه‌ها addBox کوچک
- مش‌ها: `balc_<id>` کف، `balcp_<id>_<i>` پایه‌ها، `balcr_<id>_<i>` دست‌اندازها؛ `rail_<id>_<i>`
- تور: همان اجزا در TPL ساخته شوند (کف بالکن قابل راه‌رفتن y=0)

## ۶) تست پذیرش — `/tmp/pwshot/test_v26.js` (الگوی test_v24.js)
1. نصب بالکن ۴کلیک + Enter → `proj.balcs[0].pts.length===4`
2. نصب نرده ۲کلیک + راست‌کلیک → `proj.rails[0].pts.length===2`
3. Esc وسط نصب → پاک شود، بدون خطا
4. Del روی نردهٔ انتخابی حذف + Ctrl+Z برگرداند
5. serialize شامل balcs/rails؛ بارگذاری roundtrip سالم
6. btnGLTF → فایل GLB: JSON chunk شامل مش‌های با پیشوند balc_ و rail_ (≥۹ مش)
7. btnExport (تور) → بدون خطای کنسول
8. خروجی `V26-OK`
9. رگرسیون: v21 v22b v23d v23j v24 v25_panel همه PASS

## گزارش تو (عامل کد)
لیست پچ‌ها (old→new خلاصه) + خروجی کامل تست‌ها + تأیید acorn parse کل اسکریپت‌ها
