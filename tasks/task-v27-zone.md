# HOVI v27 — Zone اتاق (برچسب + مساحت)

## قانون طلایی (تجربهٔ v25/v26)
- الگوی پیاده‌سازی = **دقیقاً همان فیچر بالکن (balcs) که در v26 اضافه شد**. برای همهٔ نقاط اتصال grep کن: `balc`
  - دادهٔ proj، serialize، load (دو مکان)، Delete، دکمهٔ تولبار، setTool+hint، pick، draw، preview، dragInfo، undo
- پچ جراحی: `rep(old,new)` با `assert src.count(old)==cnt`. **تابع تکراری تعریف نکن**
- **هر فرمان پایان زنجیره باید واقعاً finish را صدا بزند** (باگ v26: راست‌کلیک نرده فقط لغو بود و finishRail هیچ‌جا صدا زده نمی‌شد)
- داخل رشتهٔ TPL هرگز `</script>` خام ننویس
- فقط `/root/hovi/editor_v1.html` را تغییر بده. تست‌ها در `/tmp/pwshot/`

## ۱) داده
```js
proj.zones = [{id:'z'+n, pts:[[x,z],...>=3], name:'اتاق', color:'#22a}']
```
- serialize: `zones:proj.zones` کنار balcs/rails در همهٔ serializeها
- load دو مکان: `proj.zones=o.zones||[];`
- Delete: branch جدید در زنجیرهٔ فیلتر
- undo خودکار با pushUndo — تست کن

## ۲) ابزار zone (tool 'zone')
- دکمهٔ `btnZone` «⬚ ناحیه» کنار btnBalc/btnRail + کلید عددی آزاد بعدی
- نصب زنجیره‌ای مثل بالکن: zonePts؛ کلیک=گوشه؛ **Enter/dblclick=پایان (≥۳)**؛ راست‌کلیک/Esc=لغو؛ Shift=گونیا
- hint: «ناحیه — کلیک: گوشه — Enter: پایان (حداقل ۳)»
- 2D (drawZones در refresh):
  - fill رنگ zone با آلفای ~۰٫۱۲ + خط مرزی ۲px
  - **برچسب در مرکز ثقل polygon**: نام (فارسی، فونت موجود hint متن فارسی — ببین drawBalcs برچسب «بالکن» را چطور می‌کشد و همان تکنیک) + زیر آن مساحت `XX.X m²`
  - مساحت = shoelace روی pts، قدرمطلق/۲ (واحد متر چون مختصات جهان متر است)
- dblclick روی zone موجود (در tool select) = باز کردن پنل ویرایش — **هم‌سبک openStairEdit v25** (کارت وسط صفحه):
  - input نام (text)، ۵-۶ swatch رنگ (فارسی labels)، دکمهٔ «حذف ناحیه» قرمز، «تأیید»
  - **توجه:** فقط یکبار تابع ویرایش تعریف کن؛ گارد INPUT شورتکات‌ها (v25 درس): هنگام باز بودن پنل، Delete/کلیدهای بوم اجرا نشوند
- درگ انتقال کل polygon (dragInfo type 'zone' — الگوی balc)؛ Del؛ قفل `~`

## ۳) 3D ادیتور (M3_WORLD_SRC) — حداقلی
- DATA.zones خوانده شود؛ کف رنگی نیمه‌شفاف در y=0.01 (ExtrudeGeometry نازک یا ShapeGeometry) با MeshBasicMaterial transparent
- نام مش: `zone_<id>`
- اگر پیچیدگی بالا رفت، 3D را فقط GLB بگذار (تور لازم نیست برچسب داشته باشد)

## ۴) GLTF (hoviBuildGLTF)
- کف zone: addTri fan از مرکز (الگوی کف بالکن v26) — مش `zone_<id>` با mat رنگ zone (mat جدید اگر لازم)
- برچسب/متن در GLB لازم نیست

## ۵) تست پذیرش — `/tmp/pwshot/test_v27.js` (الگوی test_v26.js)
1. نصب zone ۳کلیک + Enter → `proj.zones[0].pts.length===3`
2. مساحت: مختصات معلوم (مثلاً 3×2=6m²) → مقدار محاسبه‌شدهٔ برچسب = 6.0 (eval کن تابع مساحت یا از DOM/data)
3. dblclick روی zone → پنل ویرایش باز شود (visibilitycheck مثل v25) — **حواست باشد #spacePanel روی نقطه نباشد**
4. تغییر نام + تأیید → `proj.zones[0].name` عوض شود؛ بدون prompt() (dialogs: 0)
5. حذف از پنل → zones=0؛ Ctrl+Z برگرداند
6. serialize شامل zones؛ roundtrip سالم
7. GLB: مش `zone_` وجود دارد
8. تور (btnExport) بدون خطای کنسول
9. Esc وسط نصب → هیچ‌چیز اضافه نشود
10. خروجی `V27-OK`
11. رگرسیون: test_v21 v22b v23d v23j v24 v25_panel v26 همه PASS

## گزارش تو
لیست پچ‌ها (old→new خلاصه) + خروجی کامل تست‌ها + تأیید acorn کل اسکریپت‌ها
