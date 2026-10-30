# ورك فلو موظف السوشيال ميديا

حزمة Waset لتجهيز ومراجعة ونشر 3 ستوري يوميًا و4 بوستات أسبوعيًا، باستخدام Monday وTopaz وأداة ضغط محلية على الماك. النشر يدوي.

- [ابدأ هنا](social-media-operator/ابدأ-هنا.md)
- [دليل الموظف](social-media-operator/دليل-الموظف.md)
- [تعليمات الشات](social-media-operator/تعليمات-الشات.txt)
- [مهارة الشات](social-media-operator/chat-skill/SKILL.md)
- [تحميل الحزمة ZIP](../../raw/HEAD/social-media-operator.zip)
- [نتائج الاختبارات وحدود التحقق](social-media-operator/VALIDATION.md)

## أداة الماك

فك الحزمة، افتح `mac-tool/Setup.command` لإعداد الاعتماديات عند الحاجة، ثم `mac-tool/Compress.command` لاختيار فولدر الفيديوهات. تحفظ الأداة نتائج منفصلة ولا تستبدل الأصل.

## الاختبارات

```sh
python3 -m unittest discover -s social-media-operator/tests -v
```

تحتاج Python 3 وFFmpeg وFFprobe. إعداد حسابات الموظف وفولدر Dropbox يتم عند الاستخدام الأول.
