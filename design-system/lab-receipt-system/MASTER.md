# MASTER.md — نظام إدارة الإيصالات المختبرية

**المشروع:** Lab Receipt System / نظام إدارة الاستلام والتسليم المختبري
**المنتج:** منصة آمنة لإدارة الإيصالات، التسليم، المرفقات، سلسلة الحيازة، المزامنة Offline-first، والتقارير.
**المنصات:** Vue 3 + Vite + Tailwind CSS للويب، وPySide6 لسطح المكتب.
**اللغات:** العربية RTL هي اللغة الافتراضية، والإنجليزية LTR مدعومة بالكامل.
**المرجع التصميمي:** [UI/UX Pro Max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill)
**نسخة النظام التصميمي:** 1.0
**آخر تحديث:** 26 أغسطس 2026

> هذا الملف هو **مصدر الحقيقة البصري والتفاعلي** للنظام. يجب قراءة هذا الملف قبل إنشاء صفحة أو مكوّن جديد. يمكن لملف page-specific override أن يخصص القواعد، لكنه لا يلغي قواعد الوصول والخصوصية وسلامة البيانات الواردة هنا.

## 1. فلسفة المنتج

نظام إدارة الإيصالات أداة تشغيلية حرجة وليست صفحة تسويقية. لذلك يجب أن يكون التصميم **واضحًا، سريع القراءة، قليل الزخرفة، قابلًا للتدقيق، وصريحًا بشأن حالة البيانات**. الأولوية هي منع الخطأ، كشف التعارض، وحفظ سلسلة الحيازة، ثم تحسين الكفاءة البصرية.

يعتمد النظام على أسلوب **Minimalism & Swiss Operations**: شبكة واضحة، مساحات منظمة، hierarchy قوي، حدود خفيفة، بطاقات وظيفية، ألوان دلالية، وحركة محدودة. لا تستخدم عناصر زخرفية تؤخر الوصول إلى الإجراء أو تخفي حالة Offline أو quarantine.

| أولوية التصميم | المعنى التشغيلي |
|---:|---|
| 1 | سلامة البيانات ومنع الإجراء غير المقصود. |
| 2 | وضوح نطاق المؤسسة/الفرع وحالة المزامنة. |
| 3 | سرعة القراءة والإنجاز في الجداول والنماذج. |
| 4 | الوصول بلوحة المفاتيح والشاشات الصغيرة. |
| 5 | الاتساق البصري بين الويب وDesktop. |
| 6 | الحركة والتزيين، ولا تُستخدم إلا إذا أضافت معنى. |

## 2. Design Dials

| Dial | القيمة | القرار |
|---|---:|---|
| Variance | 3/10 | واجهة مستقرة ومتمركزة، بلا layouts تجريبية أو asymmetry غير وظيفية. |
| Motion | 2/10 | انتقالات قصيرة وfeedback واضح؛ لا parallax ولا animation ضروري. |
| Density | 8/10 | كثافة مناسبة للجداول والعمليات اليومية، مع الحفاظ على ارتفاعات التفاعل والقراءة. |
| Contrast | AAA where practical | النص العادي لا يقل عن 4.5:1، والعناصر الحرجة تستهدف تباينًا أعلى. |
| Data tone | Operational | الأرقام والحالات والتواريخ أهم من الصور والزخرفة. |

## 3. Color Tokens

لا تضع ألوانًا خامًا داخل الصفحات. استخدم tokens الدلالية، ويجب أن يبقى معنى اللون واضحًا مع وجود نص أو icon مساعد؛ لا يعتمد النظام على اللون وحده.

| Token | Hex | الاستخدام |
|---|---|---|
| `--color-primary` | `#2563EB` | التركيز، الروابط، الإجراء الأساسي، focus ring. |
| `--color-primary-strong` | `#1E3A5F` | أزرار الإجراءات التشغيلية الرئيسية. |
| `--color-secondary` | `#3B82F6` | عناصر ثانوية وروابط مساندة. |
| `--color-accent` | `#EA580C` | CTA مهم مثل اعتماد أو بدء تسليم؛ لا يستخدم للتزيين العام. |
| `--color-background` | `#F8FAFC` | خلفية مساحة التطبيق. |
| `--color-card` | `#FFFFFF` | البطاقات والنماذج واللوحات. |
| `--color-foreground` | `#1E293B` | النص الأساسي والعناوين. |
| `--color-muted-foreground` | `#475569` | النص الثانوي والمعلومات المساعدة. |
| `--color-muted` | `#E9EFF8` | خلفيات الحالات المحايدة. |
| `--color-border` | `#E2E8F0` | الحدود والفواصل. |
| `--color-success` | `#15803D` | تم الحفظ/المزامنة/التحقق بنجاح، مع نص. |
| `--color-warning` | `#B45309` | stale، مراجعة، أو خطر يحتاج انتباهًا. |
| `--color-danger` | `#DC2626` | حذف، رفض، توقيع غير صالح، أو فشل حرج. |
| `--color-info` | `#1D4ED8` | Offline snapshot، Safe Mode، ومعلومة تشغيلية. |
| `--color-focus` | `#2563EB` | focus-visible واضح. |

### قواعد دلالية للحالات

| الحالة | اللون المساعد | النص الإلزامي |
|---|---|---|
| Draft | neutral | مسودة — لم تُعتمد |
| Pending sync | warning | بانتظار المزامنة |
| Synced | success | تمت المزامنة |
| Stale | warning | بيانات قديمة — آخر تحديث: … |
| Conflict/Quarantine | danger | تعارض يحتاج مراجعة |
| Safe Mode | info | الوضع الآمن مفعّل |
| Emergency | danger | وضع الطوارئ — العمليات محدودة |
| Signature valid | success | التوقيع صالح |
| Signature invalid | danger | التوقيع غير صالح — تم العزل |

## 4. Typography

لا تعتمد على تحميل خط خارجي أثناء التشغيل؛ النظام Offline-first ويجب ألا يحتاج إلى Google Fonts لفتح الواجهة. استخدم خطوط النظام مع fallback عربي/إنجليزي واضح.

```css
font-family: "Segoe UI", Tahoma, Arial, sans-serif;
font-family: ui-monospace, "Cascadia Code", "Segoe UI Mono", monospace;
```

| المستوى | الحجم | الوزن | الاستخدام |
|---|---:|---:|---|
| Page title | 24–28px | 700 | عنوان الصفحة الرئيسي. |
| Section title | 18–20px | 700 | عنوان بطاقة أو قسم. |
| Body | 16px | 400 | نص الحقول والمحتوى الأساسي. |
| Label | 14px | 600 | label دائم فوق الحقول. |
| Helper/error | 13–14px | 400/600 | تعليمات ورسائل قريبة من الحقل. |
| Dense table | 13–14px | 400/600 | جداول العمليات، مع line-height مريح. |
| Numeric/code | 13–14px | 500 | IDs، timestamps، hashes، وreceipt numbers. |

يجب أن يكون line-height للنص العادي قريبًا من 1.5، وألا يستخدم نص body بحجم أقل من 12px. حافظ على محاذاة الأرقام والتواريخ بطريقة ثابتة، واستخدم tabular numbers عند عرض KPI أو جداول مالية/عددية.

## 5. Spacing, Layout, and Responsive Rules

استخدم spacing scale ثابتة، مع كثافة 8/10 للوحة التشغيل دون ضغط الأهداف التفاعلية.

| Token | القيمة | الاستخدام |
|---|---:|---|
| `--space-xs` | 2px | فروق دقيقة داخل badge. |
| `--space-sm` | 4px | مسافة icon مع label. |
| `--space-md` | 8px | gap صغير وpadding داخلي. |
| `--space-lg` | 12px | padding حقل أو قسم صغير. |
| `--space-xl` | 16px | gap قياسي بين الحقول. |
| `--space-2xl` | 24px | padding البطاقة وmargin القسم. |
| `--space-3xl` | 32px | بداية صفحة أو قسم كبير. |

| Viewport | القرار |
|---:|---|
| 375px | single-column، أفعال أساسية بعرض كامل، والجداول تتحول إلى scroll معلن أو cards. |
| 768px | form grid بعمودين عند الحاجة، sidebar قابل للطي. |
| 1024px | dashboard كامل مع KPI وchart وattention queue. |
| 1440px | max-width مريح؛ لا تمدد السطر إلى عرض يصعب قراءته. |

استخدم CSS logical properties مثل `margin-inline` و`padding-inline` بدل left/right الثابتة. يجب ألا يسبب RTL أو LTR horizontal overflow غير مقصود، ولا يجوز أن تُخفى رسالة أو زر خلف sidebar أو navbar ثابت.

## 6. Interaction and Accessibility

تُطبق قواعد الوصول كجزء من المكوّن، لا كتحسين لاحق. يجب أن تكون كل الأفعال قابلة للاستخدام بالماوس ولوحة المفاتيح، وأن يبقى focus مرئيًا، وأن تكون labels مرئية لا مجرد placeholders.

| القاعدة | معيار القبول |
|---|---|
| Touch target | 44×44px على الأقل للأزرار والحقول والعناصر القابلة للنقر. |
| Focus | `:focus-visible` واضح بتباين مناسب ولا يُزال بواسطة `outline: none` بلا بديل. |
| Labels | كل input/select/textarea له label مرتبط فعليًا. |
| Icon buttons | `aria-label` أو نص مرئي؛ لا icon-only بلا اسم. |
| Errors | رسالة قرب الحقل + summary عند النماذج الطويلة + focus على أول خطأ. |
| Tables | headers واضحة، وتبقى الصفوف مفهومة عند التنقل بالكيبورد. |
| Color | الحالة تعرض لونًا ونصًا/icon؛ لا تستخدم اللون وحده. |
| Reduced motion | احترام `prefers-reduced-motion: reduce`. |
| Zoom | لا تعطل browser zoom ولا تعتمد على حجم ثابت يمنع القراءة. |

## 7. Component Rules

### Buttons

يوجد زر primary واحد لكل منطقة عمل. زر الحذف أو الإجراء غير القابل للعكس danger منفصل بصريًا، ويحتاج confirmation وربما re-auth. كل button يظهر loading state ويُعطّل منعًا للتكرار أثناء الطلب.

```css
.gov-btn {
  min-height: 44px;
  padding-inline: 16px;
  border-radius: 8px;
  font-weight: 600;
  transition: color 200ms ease, background-color 200ms ease, border-color 200ms ease;
}
```

لا تستخدم `transform: scale()` في hover إذا سبب layout shift، ولا تغيّر أبعاد الزر عند hover. استخدم background/border/color transition فقط.

### Cards

البطاقة container وظيفي وليست decoration. استخدم خلفية بيضاء وحدًا `--color-border` وظلًا خفيفًا. لا تجعل البطاقة كلها clickable إذا كانت تحتوي عدة أفعال؛ اجعل الإجراء واضحًا ومسمى.

### Inputs and Forms

كل حقل له label، helper text عند الحاجة، ورسالة خطأ قريبة. لا تفقد القيمة المحلية عند فشل الشبكة أو انتهاء الجلسة. في النماذج الحساسة، اعرض review step قبل الحفظ النهائي، وبيّن هل الحفظ محلي أم تمت مزامنته.

### Badges and Status Strips

استخدم status strip عند Offline أو Safe Mode أو stale data، مع icon أو نص. لا تجعل التحذير toast مؤقتًا فقط؛ التحذير التشغيلي يجب أن يبقى مرئيًا حتى يعالجه المستخدم.

### Modals

استخدم modal للتأكيدات القصيرة أو re-auth فقط. يجب trap focus، دعم Escape عندما لا يكون الإجراء حرجًا، استعادة focus إلى العنصر الذي فتح modal، ومنع تمرير الصفحة خلفه. لا تضع نموذجًا طويلًا داخل modal؛ استخدم صفحة أو drawer واضحًا.

### Tables

الجداول هي المكوّن الأساسي للنظام. يجب أن تدعم sorting/filtering/pagination أو virtualization عند الحجم الكبير، وتحافظ على header واضح، row hover خفيف، وempty/loading/error states. لا تخفِ معلومات الحالة في tooltip فقط.

## 8. الصفحة القياسية

كل صفحة مصادق عليها تتبع الهيكل التالي:

```text
Page shell
├── Page header: title + subtitle + scope + last updated
├── Status strip: offline/safe/stale/conflict عند الحاجة
├── Primary action + secondary actions
├── Filters/search عند وجود بيانات كثيرة
├── Main content: KPI/table/form/chart
└── Empty/error/retry state
```

يجب أن يكون نطاق المؤسسة/الفرع ظاهرًا للمستخدم ولا يُستنتج من الواجهة فقط. إذا كانت البيانات snapshot محلية، اعرض وقت التقاطها وحالتها بدل تقديمها كبيانات لحظية.

## 9. Dashboard Pattern

Dashboard لوحة تشغيل، وليس صفحة عرض. استخدم KPI مختصرة في الأعلى، ثم الرسوم، ثم attention queue.

| المنطقة | المحتوى |
|---|---|
| Header | العنوان، النطاق، آخر تحديث، زر إنشاء receipt، وزر sync عند السماح. |
| KPI | إجمالي المعاملات، قيد المراجعة، quarantine، وآخر sync ناجح. |
| Charts | معاملات عبر الزمن، استلام مقابل تسليم، وتوزيع الحالات. |
| Attention queue | conflicts، failed jobs، stale backups، وdual-verification items. |
| Activity | آخر الأحداث مع رابط إلى details وchain of custody. |

كل chart له title وlegend وlabels أو data table بديلة. لا تستخدم animation ضرورية لفهم البيانات، ولا تعرض KPI بلا الفترة والنطاق.

## 10. Reports Pattern

التقرير يمر بثلاث مراحل: **اختيار النطاق → معاينة → تصدير**. لا يبدأ التصدير تلقائيًا بمجرد تغيير filter.

يجب أن تعرض الواجهة عدد السجلات، النطاق، وقت آخر تحديث، مصدر البيانات، وتحذير stale/offline. التصدير الكبير يمر عبر JobManager بحالات `queued`, `running`, `completed`, `failed`, `cancelled`، ولا يحجز UI thread.

لا يحتوي اسم الملف أو toast أو error على PHI أو token. قبل PDF/Excel يجب أن يرى المستخدم ما سيُصدّر، وأن يكون tenant/facility scope مفروضًا من الخادم لا من query يرسله العميل.

## 11. Transactions and Chain of Custody

قائمة المعاملات تستخدم search-first layout: بحث واضح، فلاتر قابلة للطي، جدول قابل للتصفح، وأفعال صف مسماة. صفحة التفاصيل تعرض Chain of Custody كتسلسل زمني غير قابل للتعديل، مع actor وfacility وdevice وtimestamp وحالة التحقق والتعارض.

لا يُعدّل event تاريخي. التصحيح يكون corrective event أو revision جديدًا. أي quarantine أو override يظهر بوضوح، ويعرض السبب وصلاحية المستخدم وحالة التوقيع أو التحقق.

## 12. Offline-first UX

حالة Offline ليست خطأً عامًا. يجب التفريق بين:

| الحالة | العرض |
|---|---|
| Online | اتصال متاح، آخر sync ووقت النجاح. |
| Offline | «أنت تعمل محليًا» مع استمرار الوظائف المسموحة. |
| Pending | عدد الأحداث بانتظار المزامنة. |
| Conflict | عدد التعارضات مع زر فتح quarantine. |
| Stale | آخر وقت بيانات معروف مع تحذير واضح. |
| Safe Mode | سبب التفعيل والأفعال المسموحة. |
| Emergency | العمليات المحدودة وخيار recovery/support. |

لا تحذف payload عند فشل sync، ولا تحول conflict إلى نجاح بصري. يجب أن يرى المستخدم الفرق بين `saved locally` و`synced remotely`.

## 13. Risk and Safety UX

الإجراء عالي الخطورة يحتاج hard warning أو confirmation أو dual verification بحسب Risk Engine. يجب أن يشرح التحذير **ما الذي سيحدث، ولماذا، وما البديل**. لا تستخدم «هل أنت متأكد؟» وحدها.

| مستوى الخطر | UX المطلوب |
|---|---|
| Low | تنفيذ مع feedback عادي. |
| Medium | confirmation مع ملخص الأثر. |
| High | confirmation صريح + re-auth عند الحاجة + audit. |
| Critical | منع افتراضي أو dual verification + سبب موثق. |
| Invalid signature/conflict | quarantine، لا overwrite، وفتح مسار مراجعة. |

## 14. Motion and Feedback

استخدم transitions من 150 إلى 300ms لتغيير اللون أو الظهور البسيط. يمكن استخدام fade/translate صغير 8–16px عند ظهور قسم غير حرج، مع fallback ثابت عند reduced motion. لا تحرك width/height بما يسبب layout shift، ولا تخفِ محتوى مهمًا إلى أن تعمل JavaScript.

كل طلب async يعرض feedback مناسبًا: loading، نجاح، فشل قابل لإعادة المحاولة، أو حفظ محلي. لا تستخدم spinner بلا نص في إجراء يستغرق أكثر من لحظات قليلة.

## 15. Icons and Visual Assets

استخدم SVG من مجموعة واحدة مثل Lucide أو Heroicons، مع `aria-hidden="true"` للأيقونات الزخرفية و`aria-label` للأزرار الأيقونية. لا تستخدم emoji كبديل للأيقونات، ولا تخلط styles متعددة.

الشعار والمرفقات والصور يجب أن تحجز أبعادها مسبقًا لمنع CLS. لا تُحمّل صورًا خارجية لواجهة التشغيل إذا كان ذلك يضر Offline-first أو CSP.

## 16. Desktop/PySide6 Mapping

يجب أن تعكس واجهة PySide6 القواعد نفسها حتى إن اختلفت آلية التنفيذ:

| Web | PySide6 |
|---|---|
| `gov-card` | QFrame بحد خفيف وpadding ثابت. |
| `gov-btn` | QPushButton بارتفاع تفاعلي مناسب وaccessible name. |
| `gov-input` | QLineEdit/QTextEdit مع label وvalidation قريب. |
| `status-strip` | QFrame ثابت لا يعتمد على toast مؤقت. |
| `JobManager` | worker/progress signal دون لمس widgets من thread. |
| Offline queue | badge بعدد pending/conflicts مع فتح quarantine. |
| Safe Mode | banner دائم يوضح السياسة والأفعال المسموحة. |

لا تشارك SQLite connection بين UI thread وworker. كل worker يفتح connection مستقلًا، ويعيد النتائج عبر signals.

## 17. Anti-Patterns ممنوعة

| ممنوع | السبب |
|---|---|
| Emoji كأيقونة | اختلاف العرض وضعف accessibility وعدم الاتساق. |
| Placeholder بدل label | يختفي السياق عند الكتابة ويضر الوصول. |
| لون بلا نص | لا يعمل مع عمى الألوان أو screen readers. |
| Toast لتحذير حرج | قد يختفي قبل أن يُفهم أو يُعالج. |
| Silent auto-save/print/sync | قد ينشئ أثرًا تشغيليًا غير مقصود. |
| `v-html` لبيانات المستخدم | يزيد خطر XSS؛ استخدم text binding وsanitization عند الضرورة. |
| `get_all()` بلا scope | خطر تسريب cross-tenant. |
| تعديل event تاريخي | يكسر قابلية التدقيق وسلسلة الحيازة. |
| spinner على UI thread | يعطي انطباع تجمد ويؤثر في العمليات. |
| card hover يغير layout | يسبب jitter ويصعب القراءة المتكررة. |
| dark mode منخفض التباين | يقلل وضوح الحالات والبيانات. |
| external font/image mandatory | يكسر Offline-first ويزيد surface الشبكة. |

## 18. Pre-Delivery Checklist

قبل اعتماد أي صفحة أو مكوّن:

- [ ] يستخدم tokens من هذا الملف ولا يحتوي ألوانًا أو spacing خامًا بلا سبب.
- [ ] يعمل RTL وLTR في 375px و768px و1024px و1440px.
- [ ] لا يوجد horizontal overflow غير مقصود.
- [ ] كل button/input لا يقل هدفه التفاعلي عن 44px.
- [ ] labels وfocus وkeyboard navigation مكتملة.
- [ ] الرسائل قريبة من الحقل، وsummary الأخطاء موجود للنماذج الطويلة.
- [ ] loading/empty/error/offline/stale states موجودة عند الحاجة.
- [ ] لا يعتمد أي status على اللون فقط.
- [ ] `prefers-reduced-motion` محترم.
- [ ] لا يوجد PHI أو token في UI logs/toasts/filenames/errors.
- [ ] الإجراءات الحساسة لها permission وconfirmation وre-auth/dual verification حسب الخطر.
- [ ] لا يعمل export أو sync كبير على UI thread.
- [ ] لا توجد أيقونات emoji أو icon-only بلا accessible name.
- [ ] نجحت unit/component/integration tests وvisual regression عند تغيير layout.
- [ ] تم فحص tenant/facility scope في API والـrepository والـexport.
- [ ] تم اختبار Offline وquarantine وعدم overwrite.

## 19. Page Override Contract

عند إنشاء ملف مثل `pages/dashboard.md` أو `pages/reports.md` يجب أن يتضمن:

```text
Page purpose
Primary user tasks
Information hierarchy
Allowed actions by role
Tenant/facility scope
Loading/empty/error/offline states
Responsive behavior
Chart/table rules
Keyboard and screen-reader behavior
Test cases and visual checkpoints
```

لا يجوز للـoverride تغيير primary/accent/destructive meanings أو تعطيل focus أو reduced motion أو privacy rules.

## 20. References

[1]: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/blob/main/.claude/skills/ui-ux-pro-max/SKILL.md "UI/UX Pro Max — official SKILL.md"
[2]: https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html "WCAG 2.2 — Contrast Minimum"
[3]: https://www.w3.org/WAI/WCAG22/Understanding/focus-visible.html "WCAG 2.2 — Focus Visible"
[4]: https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html "WCAG 2.2 — Target Size Minimum"
