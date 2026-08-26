# تطبيق ui-ux-pro-max على واجهات النظام

**المشروع:** Lab Receipt System
**المصدر التصميمي:** [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill)
**الـstack:** Vue 3 + Vite + Tailwind CSS
**تاريخ التطبيق:** 26 أغسطس 2026

## الاتجاه البصري

تم اختيار **Minimalism & Swiss Style** لأنه يناسب لوحة تشغيل مختبرية كثيفة البيانات: بنية شبكية واضحة، تباين عالٍ، حدود خفيفة، hierarchy مباشر، وحركة محدودة لا تعيق العمل المتكرر. ضُبطت كثافة التصميم على 8/10، والحركة على 2/10، والاختلاف البصري على 3/10؛ أي واجهة عملية مستقرة وليست صفحة تسويقية.

| Token | القيمة | الاستخدام |
|---|---|---|
| Primary | `#2563EB` | الروابط والتركيز والحالة الأساسية |
| Primary strong | `#1E3A5F` | أزرار الإجراءات الأساسية الحالية |
| Accent | `#EA580C` | أفعال CTA التي تحتاج لفت انتباه |
| Background | `#F8FAFC` | مساحة التطبيق الرئيسية |
| Foreground | `#1E293B` | النص الأساسي |
| Muted foreground | `#475569` | النص الثانوي |
| Border | `#E2E8F0` | حدود البطاقات والحقول |
| Destructive | `#DC2626` | الحذف والتحذيرات الحرجة |

تم الإبقاء على خطوط النظام وfallbacks المحلية بدل استيراد Google Fonts أثناء التشغيل، لأن التطبيق Offline-first وCSP الحالية تمنع الاعتماد غير الضروري على مصدر خارجي. يدعم ذلك العربية والإنجليزية دون إضافة request شبكة عند فتح الواجهة.

## ما تم تطبيقه

أضيفت CSS custom properties مركزية، وربطت الخلفية والألوان والحاويات بها، وأضيفت أصناف `page-title`, `page-subtitle`, `status-strip`, `status-strip--offline`, و`status-strip--safe` لإعادة الاستخدام في الصفحات الحالية والقادمة. أصبحت أزرار `.gov-btn` بارتفاع لمس أدنى 44px، وأصبحت الحقول `.gov-input` و`.gov-select` بارتفاع مماثل وحجم نص 16px، مع focus ring واضح للوحة المفاتيح.

تمت إضافة `prefers-reduced-motion` لإلغاء الحركة غير الضرورية، مع انتقالات قصيرة 200ms بدل القفزات الفورية. كما أضيف `cursor: pointer` للعناصر القابلة للنقر، وأصبحت `app-shell` و`app-main` تستخدمان background token موحدًا في `Layout.vue`.

## قواعد يجب الالتزام بها في الصفحات القادمة

| القاعدة | معيار المراجعة |
|---|---|
| Accessibility | تباين نص لا يقل عن 4.5:1، focus واضح، labels مرئية، وaria-label للأيقونات المنفردة. |
| Touch/keyboard | هدف التفاعل 44×44px على الأقل، وعدم الاعتماد على hover وحده. |
| Responsive | مراجعة 375px و768px و1024px و1440px، وعدم وجود horizontal scroll غير مقصود. |
| Motion | احترام `prefers-reduced-motion` وعدم استخدام parallax أو حركة ضرورية لإنجاز العملية. |
| Icons | استخدام SVG من مجموعة متسقة؛ لا emoji كأيقونات. |
| Data density | استخدام الجداول والبطاقات المتدرجة، مع empty/loading/error states واضحة. |
| Privacy UX | عدم عرض PHI أو tokens في toast أو error، وإظهار حالة Offline/Safe بوضوح دون كشف بيانات حساسة. |
| Forms | label دائم، validation قرب الحقل، ورسالة تصف الإجراء المطلوب لا مجرد كلمة «خطأ». |

## حدود التطبيق الحالي

التغيير الحالي هو **طبقة Design System عامة محسنة** متوافقة مع الصفحات الموجودة، وليس إعادة تصميم كاملة لكل Dashboard وTransactions وReports وSettings. إعادة تصميم كل صفحة يجب أن تتم بمراجعة page-specific override من `design-system/lab-receipt-system/pages/` ثم اختبار بصري ووظيفي مستقل، حتى لا تتغير semantics أو RBAC أو نماذج الإدخال دون قصد.

## التحقق

نجحت اختبارات Vitest: **24 اختبارًا عبر 10 ملفات**، ونجح `npm run build` مع Vite/PWA. يجب إضافة visual regression screenshots عند اعتماد إعادة تصميم صفحات كاملة، لأن اختبار DOM وحده لا يثبت جودة التباين أو عدم قص الحقول العربية.

## مراجع

[1]: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/blob/main/.claude/skills/ui-ux-pro-max/SKILL.md "UI/UX Pro Max Skill — official SKILL.md"
[2]: https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html "WCAG 2.2 — Contrast (Minimum)"
