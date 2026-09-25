# Copyright (c) 2026 Shkour Bashtawi (github.com/ShkourBashtawi). MIT License.
"""Arabic UI strings (key = the English text used in the code)."""

AR: dict[str, str] = {
    # ---- app / general ----
    "GameTalk Translator": "مترجم GameTalk",
    "Help": "المساعدة",
    "Save": "حفظ",
    "Cancel": "إلغاء",
    "Done": "تم",
    "(none)": "(بدون)",
    "English": "الإنجليزية",
    "Enabled": "مفعّل",
    "Profile": "ملف التعريف",
    "Profile:": "ملف التعريف:",
    "Profile: {name}": "ملف التعريف: {name}",
    "Version {version}": "الإصدار {version}",
    "Released under the MIT License.": "مرخّص بموجب رخصة MIT.",
    "About {app}": "حول {app}",
    "About…": "حول البرنامج…",
    "Exit": "خروج",
    "{app} — Settings": "{app} — الإعدادات",
    "{app} — Launcher": "{app} — لوحة التحكم",
    "{app} — Help": "{app} — المساعدة",
    "Explain this page": "اشرح هذه الصفحة",
    " and ": " و",
    # ---- overlay / controller messages ----
    "Listening...": "جارٍ الاستماع...",
    "Processing...": "جارٍ المعالجة...",
    "Drag me, then click Done": "اسحبني ثم اضغط «تم»",
    "Running in the tray. Hold {key}, speak, release.": (
        "البرنامج يعمل بجانب الساعة. اضغط {key} مع الاستمرار، تكلّم، ثم اترك الزر."
    ),
    "Add your Azure Speech key and region in Settings > Azure.": (
        "أضف مفتاح Azure Speech ومنطقته من الإعدادات ← Azure."
    ),
    "Add your Azure Translator key in Settings > Azure.": (
        "أضف مفتاح Azure Translator من الإعدادات ← Azure."
    ),
    "Add your Azure keys in Settings > Azure.": "أضف مفاتيح Azure من الإعدادات ← Azure.",
    "Add your Azure Speech key in Settings > Azure.": "أضف مفتاح Azure Speech من الإعدادات ← Azure.",
    "Your game is in exclusive fullscreen, so the overlay can't appear on top. Switch the game "
    "to Borderless or Windowed mode.": (
        "لعبتك في وضع ملء الشاشة الحصري، لذلك لا يمكن للنافذة الظهور فوقها. "
        "غيّر إعداد العرض في اللعبة إلى Borderless أو Windowed."
    ),
    "Hold {key} while you speak.": "اضغط {key} مع الاستمرار أثناء الكلام.",
    "Reloading speech model…": "جارٍ إعادة تحميل نموذج الكلام…",
    "Busy — try again in a moment.": "مشغول — حاول بعد لحظة.",
    "Speech model is still loading…": "نموذج الكلام ما زال يُحمَّل…",
    "No sound from the mic — is it muted? Pick another in Settings.": (
        "لا يوجد صوت من الميكروفون — هل هو مكتوم؟ اختر ميكروفوناً آخر من الإعدادات."
    ),
    "Didn't catch that — try again.": "لم أفهم — حاول مرة أخرى.",
    "Nothing to show yet.": "لا يوجد شيء لعرضه بعد.",
    "Couldn't save settings.": "تعذّر حفظ الإعدادات.",
    "{what} This only happens once.": "{what} يحدث هذا مرة واحدة فقط.",
    "Microphone error.": "خطأ في الميكروفون.",
    "Ready — hold {key} to talk": "جاهز — اضغط {key} مع الاستمرار للتحدث",
    "Loading speech model… the mic test starts after.": (
        "جارٍ تحميل نموذج الكلام… تبدأ تجربة الميكروفون بعده."
    ),
    "GameTalk is already running (tray icon).": "البرنامج يعمل مسبقاً (الأيقونة بجانب الساعة).",
    # ---- engine / errors (shown when they happen) ----
    "Downloading speech model…": "جارٍ تنزيل نموذج الكلام…",
    "Loading speech model…": "جارٍ تحميل نموذج الكلام…",
    "Downloading offline translator…": "جارٍ تنزيل المترجم المحلي…",
    "loading speech model…": "جارٍ تحميل نموذج الكلام…",
    "speech engine not ready": "محرك الكلام غير جاهز",
    "Speech model '{name}' is missing and couldn't be downloaded. Connect to the internet once, "
    "or pick another model.": (
        "نموذج الكلام '{name}' غير موجود وتعذّر تنزيله. اتصل بالإنترنت مرة واحدة أو اختر نموذجاً آخر."
    ),
    "Couldn't load the speech model.": "تعذّر تحميل نموذج الكلام.",
    "Speech model isn't loaded.": "نموذج الكلام غير محمَّل.",
    "GPU out of memory — try a smaller model or CPU.": (
        "ذاكرة كرت الشاشة ممتلئة — جرّب نموذجاً أصغر أو المعالج."
    ),
    "Translation failed — try again.": "فشلت الترجمة — حاول مرة أخرى.",
    "No NVIDIA GPU/CUDA found — using CPU.": "لم يُعثر على كرت NVIDIA — سيتم استخدام المعالج.",
    "GPU acceleration unavailable — using CPU.": "تسريع كرت الشاشة غير متاح — سيتم استخدام المعالج.",
    "Audio system unavailable.": "نظام الصوت غير متاح.",
    "Selected microphone not found.": "الميكروفون المختار غير موجود.",
    "No microphone found.": "لم يُعثر على أي ميكروفون.",
    "Can't open the microphone. It may be in use or blocked in Windows Privacy > Microphone.": (
        "تعذّر فتح الميكروفون. قد يكون مستخدماً أو محظوراً من خصوصية ويندوز ← الميكروفون."
    ),
    "Microphone access failed.": "تعذّر الوصول إلى الميكروفون.",
    "Azure Speech sent an unexpected reply.": "أرسل Azure Speech رداً غير متوقع.",
    "Azure Speech couldn't process the audio.": "لم يتمكن Azure Speech من معالجة الصوت.",
    "Azure Translator sent an unexpected reply.": "أرسل Azure Translator رداً غير متوقع.",
    "Azure Speech: invalid key or wrong region.": "Azure Speech: مفتاح غير صالح أو منطقة خاطئة.",
    "Azure Translator: invalid key or wrong region.": (
        "Azure Translator: مفتاح غير صالح أو منطقة خاطئة."
    ),
    "Azure Speech: rate limit or free quota reached.": (
        "Azure Speech: تم بلوغ حد الطلبات أو الحصة المجانية."
    ),
    "Azure Translator: rate limit or free quota reached.": (
        "Azure Translator: تم بلوغ حد الطلبات أو الحصة المجانية."
    ),
    "Can't reach Azure Speech — check internet and region.": (
        "تعذّر الوصول إلى Azure Speech — تحقق من الإنترنت والمنطقة."
    ),
    "Can't reach Azure Translator — check internet and region.": (
        "تعذّر الوصول إلى Azure Translator — تحقق من الإنترنت والمنطقة."
    ),
    "Azure Speech timed out — check your connection.": (
        "انتهت مهلة Azure Speech — تحقق من اتصالك."
    ),
    "Azure Translator timed out — check your connection.": (
        "انتهت مهلة Azure Translator — تحقق من اتصالك."
    ),
    "Azure Speech: connected": "Azure Speech: متصل",
    "Azure Translator: connected": "Azure Translator: متصل",
    "Azure Speech: no key/region entered": "Azure Speech: لم يُدخل مفتاح/منطقة",
    "Azure Translator: no key entered": "Azure Translator: لم يُدخل مفتاح",
    "Key encryption is only available on Windows": "تشفير المفاتيح متاح على ويندوز فقط",
    "Game controller support (XInput) isn't available.": "دعم يد التحكم (XInput) غير متاح.",
    "Global hotkeys are only supported on Windows.": "الأزرار العامة مدعومة على ويندوز فقط.",
    "Couldn't register the push-to-talk hotkey.": "تعذّر تسجيل زر التحدث.",
    "Couldn't register the mouse-button hotkey.": "تعذّر تسجيل زر الماوس.",
    "Offline translator isn't installed.": "المترجم المحلي غير مثبّت.",
    "Offline translator couldn't be downloaded. Connect to the internet once.": (
        "تعذّر تنزيل المترجم المحلي. اتصل بالإنترنت مرة واحدة."
    ),
    "Offline translator couldn't be loaded.": "تعذّر تحميل المترجم المحلي.",
    "Offline translator isn't available.": "المترجم المحلي غير متاح.",
    "Can't listen to the selected output device.": "تعذّر الاستماع إلى جهاز الصوت المختار.",
    # ---- launcher ----
    "🎤 Your voice": "🎤 صوتك",
    "Whisper {model} (this PC)": "Whisper {model} (هذا الجهاز)",
    "☁ Sent to Azure: your push-to-talk audio + the recognised text.": (
        "☁ يُرسَل إلى Azure: صوتك أثناء الضغط + النص المُتعرَّف عليه."
    ),
    "☁ Sent to Azure: only the recognised Arabic text — never your audio.": (
        "☁ يُرسَل إلى Azure: النص العربي فقط — ولا يُرسَل صوتك أبداً."
    ),
    "🔒 Nothing leaves this PC.": "🔒 لا شيء يخرج من جهازك.",
    "Azure Speech key + region": "مفتاح Azure Speech ومنطقته",
    "Azure Translator key": "مفتاح Azure Translator",
    "✅ key saved": "✅ المفتاح محفوظ",
    "⚠ no key": "⚠ لا يوجد مفتاح",
    "Switch the interface language": "تغيير لغة الواجهة",
    "v{version} · hold your hotkey, speak Arabic, read the English": (
        "الإصدار {version} · اضغط زرّك، تكلّم بالعربي، واقرأ الإنجليزي"
    ),
    "Checking…": "جارٍ الفحص…",
    "How GameTalk understands and translates you": "كيف يفهمك البرنامج ويترجم كلامك",
    "Speech → text": "الكلام ← نص",
    "who listens to your voice": "من يستمع لصوتك",
    "Text → translation": "النص ← ترجمة",
    "who turns it into English": "من يحوّله إلى الإنجليزية",
    "💻  Whisper — on this PC": "💻  Whisper — على جهازك",
    "Whisper model:": "نموذج Whisper:",
    "Your dialect:": "لهجتك:",
    "Translate to:": "الترجمة إلى:",
    "Whisper translates straight from your voice (English only).": (
        "Whisper يترجم من صوتك مباشرة (إلى الإنجليزية فقط)."
    ),
    "Whisper can only translate straight from your voice, not from text. With Azure Speech, "
    "translation is done by Azure Translator.": (
        "Whisper يترجم من الصوت مباشرة فقط، لا من النص. مع Azure Speech تتم الترجمة بواسطة "
        "Azure Translator."
    ),
    "⚠ Missing: {what}. Click “Azure keys” to add it.": (
        "⚠ ناقص: {what}. اضغط «مفاتيح Azure» لإضافته."
    ),
    "Features": "الميزات",
    "Manage…": "إدارة…",
    "On: {on}": "مفعّلة: {on}",
    "Off: {off}": "متوقفة: {off}",
    "Teammate subtitles (translate what you hear)": "ترجمة كلام الفريق (ترجمة ما تسمعه)",
    "▶  Start GameTalk": "▶  تشغيل البرنامج",
    "■  Stop GameTalk": "■  إيقاف البرنامج",
    "⚙  Settings": "⚙  الإعدادات",
    "🔑  Azure keys": "🔑  مفاتيح Azure",
    "🎤  Test microphone": "🎤  تجربة الميكروفون",
    "📂  Logs folder": "📂  مجلد السجلات",
    "Start GameTalk when Windows starts": "تشغيل البرنامج مع بدء ويندوز",
    "Create desktop shortcut to this launcher": "إنشاء اختصار على سطح المكتب",
    "Tip: you can close this window — GameTalk keeps running in the tray.": (
        "نصيحة: يمكنك إغلاق هذه النافذة — يبقى البرنامج يعمل بجانب الساعة."
    ),
    "Not running": "غير مشغّل",
    "Click Start — GameTalk then lives in the system tray.": (
        "اضغط تشغيل — وسيعمل البرنامج بجانب الساعة."
    ),
    "Running — hold {key} to talk": "يعمل — اضغط {key} مع الاستمرار للتحدث",
    "Running — disabled from the tray": "يعمل — لكنه موقوف من قائمة الأيقونة",
    "Couldn't change Windows startup: {e}": "تعذّر تغيير التشغيل مع ويندوز: {e}",
    "Shortcut created:": "تم إنشاء الاختصار:",
    "Couldn't create the shortcut: {e}": "تعذّر إنشاء الاختصار: {e}",
    "Replay": "الإعادة",
    "History": "السجل",
    "Quick phrases": "الجمل الجاهزة",
    "Corrections": "التصحيح",
    "Pronunciation": "النطق",
    "Controller": "يد التحكم",
    # ---- tray ----
    "Recent translations": "الترجمات الأخيرة",
    "Settings…": "الإعدادات…",
    "Test microphone": "تجربة الميكروفون",
    "Reload speech model": "إعادة تحميل نموذج الكلام",
    "Open launcher": "فتح لوحة التحكم",
    # ---- settings: structure ----
    "Settings marked per game belong to this profile.": (
        "الإعدادات الخاصة بكل لعبة تتبع ملف التعريف هذا."
    ),
    "New": "جديد",
    "Rename": "إعادة تسمية",
    "Delete": "حذف",
    "Profile name:": "اسم ملف التعريف:",
    "New profile": "ملف تعريف جديد",
    "Rename profile": "إعادة تسمية ملف التعريف",
    "Delete profile": "حذف ملف التعريف",
    "A profile with that name already exists.": "يوجد ملف تعريف بهذا الاسم مسبقاً.",
    "At least one profile is required.": "يجب وجود ملف تعريف واحد على الأقل.",
    # ---- settings: general ----
    "Interface language:": "لغة الواجهة:",
    "Takes effect when you click Save.": "يُطبَّق عند الضغط على حفظ.",
    "GameTalk is enabled": "البرنامج مفعّل",
    "Off = hotkeys do nothing until you turn it back on.": (
        "عند الإيقاف لا تعمل الأزرار حتى تعيد التفعيل."
    ),
    "Automatic (Windows language)": "تلقائي (لغة ويندوز)",
    # ---- settings: features ----
    "Replay key (show the last translation again)": "زر الإعادة (عرض آخر ترجمة مجدداً)",
    "Translation history (tray menu)": "سجل الترجمات (قائمة الأيقونة)",
    "Quick phrases on keys": "الجمل الجاهزة على الأزرار",
    "Correction rules": "قواعد التصحيح",
    "Pronunciation helper (English in Arabic letters)": "مساعد النطق (الإنجليزي بحروف عربية)",
    "Game controller button as push-to-talk": "زر يد التحكم للتحدث",
    "Warn when a game is in exclusive fullscreen": "التنبيه عندما تكون اللعبة بملء الشاشة الحصري",
    "Stuck-key protection": "الحماية من الزر العالق",
    "Trim silence before sending audio to Azure": "قص الصمت قبل إرسال الصوت إلى Azure",
    "Send gaming vocabulary to Azure Speech (phrase list)": (
        "إرسال كلمات الألعاب إلى Azure Speech (قائمة العبارات)"
    ),
    "Tray notifications": "إشعارات الأيقونة",
    # ---- settings: microphone ----
    "Refresh": "تحديث",
    "Re-scan audio devices (after plugging in a microphone)": (
        "إعادة البحث عن أجهزة الصوت (بعد توصيل ميكروفون)"
    ),
    "Input device:": "جهاز الإدخال:",
    "Input level:": "مستوى الصوت:",
    "Test microphone (speak for 3 s)": "تجربة الميكروفون (تكلّم 3 ثوانٍ)",
    "Result:": "النتيجة:",
    "Windows default": "افتراضي ويندوز",
    "{name} (not connected)": "{name} (غير متصل)",
    "Listening… speak now": "أستمع… تكلّم الآن",
    # ---- settings: speech ----
    "Recognition:": "التعرّف على الكلام:",
    "Azure dialect:": "لهجة Azure:",
    "The dialect you speak; Azure is more accurate with the match": (
        "اللهجة التي تتكلمها؛ Azure أدق عند اختيار اللهجة الصحيحة"
    ),
    "Model name or a local CTranslate2 model folder": "اسم النموذج أو مجلد نموذج CTranslate2 محلي",
    "Run on:": "التشغيل على:",
    "Auto uses your NVIDIA GPU when available and falls back to the CPU.": (
        "التلقائي يستخدم كرت NVIDIA إن وُجد، وإلا المعالج."
    ),
    "Source language:": "لغة الكلام:",
    "Auto-detect spoken language": "اكتشاف لغة الكلام تلقائياً",
    "Also show the original transcript (slower)": "عرض النص الأصلي أيضاً (أبطأ)",
    "Adds the Arabic text under the translation.": "يضيف النص العربي تحت الترجمة.",
    "tiny/base/small are fastest. medium and large-v3 translate dialect more naturally but need "
    "more VRAM (large-v3 ≈ 3 GB on GPU). Models download once, then run offline.": (
        "tiny/base/small هي الأسرع. medium وlarge-v3 تترجم اللهجات بشكل أطبع لكنها تحتاج ذاكرة "
        "كرت شاشة أكبر (large-v3 ≈ 3 غيغا). النماذج تُنزَّل مرة واحدة ثم تعمل بدون إنترنت."
    ),
    "Whisper (local, offline)": "Whisper (محلي، بدون إنترنت)",
    "Azure Speech (cloud, most accurate)": "Azure Speech (سحابي، الأدق)",
    "Auto (GPU if available)": "تلقائي (كرت الشاشة إن وُجد)",
    "GPU (NVIDIA CUDA)": "كرت الشاشة (NVIDIA CUDA)",
    "CPU": "المعالج",
    # ---- settings: translation ----
    "Provider:": "المزوّد:",
    "Target language:": "لغة الترجمة:",
    "Whisper's built-in translation always outputs English": (
        "ترجمة Whisper المدمجة تُخرج الإنجليزية دائماً"
    ),
    "Gaming translation mode (short, casual callouts)": "وضع ترجمة الألعاب (عبارات قصيرة وعفوية)",
    "Steers Whisper toward short squad-chat phrasing.": "يوجّه Whisper لعبارات قصيرة مثل كلام الفريق.",
    "Use gaming vocabulary as recognition hints": "استخدام كلمات الألعاب كتلميحات للتعرّف",
    "Whisper is nudged toward these words. Nothing is ever find-and-replaced.": (
        "يُوجَّه Whisper نحو هذه الكلمات. لا يتم استبدال أي كلمة."
    ),
    "One word or phrase per line, e.g. Medic, Flank, Fall back": (
        "كلمة أو عبارة في كل سطر، مثل Medic وFlank وFall back"
    ),
    "Up to {n} entries of {m} characters; duplicates are removed. The first 24 are sent to "
    "Whisper.": "حتى {n} كلمة بطول {m} حرفاً؛ تُحذف المكررات. أول 24 تُرسَل إلى Whisper.",
    "Gaming vocabulary:": "كلمات الألعاب:",
    "Whisper (local, speech → English)": "Whisper (محلي، من الكلام ← الإنجليزية)",
    "Azure Translator (cloud)": "Azure Translator (سحابي)",
    "Azure Speech → Azure Translator: your audio and its text are sent to Azure.": (
        "Azure Speech ← Azure Translator: يُرسَل صوتك ونصه إلى Azure."
    ),
    "Whisper recognises Arabic locally; only the recognised text is sent to Azure Translator.": (
        "Whisper يتعرّف على العربية على جهازك؛ ويُرسَل النص فقط إلى Azure Translator."
    ),
    "Everything runs locally; no audio or text leaves this PC. Vocabulary is a context hint, "
    "not a find-and-replace list.": (
        "كل شيء يعمل على جهازك؛ لا يخرج أي صوت أو نص. الكلمات تلميح للسياق وليست قائمة استبدال."
    ),
    # ---- languages ----
    "Arabic": "العربية",
    "French": "الفرنسية",
    "German": "الألمانية",
    "Spanish": "الإسبانية",
    "Portuguese": "البرتغالية",
    "Italian": "الإيطالية",
    "Turkish": "التركية",
    "Russian": "الروسية",
    "Persian": "الفارسية",
    "Urdu": "الأردية",
    "Hindi": "الهندية",
    "Chinese (Simplified)": "الصينية (المبسطة)",
    "Japanese": "اليابانية",
    "Korean": "الكورية",
    "Arabic — Saudi Arabia": "العربية — السعودية",
    "Arabic — UAE": "العربية — الإمارات",
    "Arabic — Kuwait": "العربية — الكويت",
    "Arabic — Qatar": "العربية — قطر",
    "Arabic — Bahrain": "العربية — البحرين",
    "Arabic — Oman": "العربية — عُمان",
    "Arabic — Yemen": "العربية — اليمن",
    "Arabic — Iraq": "العربية — العراق",
    "Arabic — Jordan": "العربية — الأردن",
    "Arabic — Lebanon": "العربية — لبنان",
    "Arabic — Syria": "العربية — سوريا",
    "Arabic — Palestine": "العربية — فلسطين",
    "Arabic — Egypt": "العربية — مصر",
    "Arabic — Libya": "العربية — ليبيا",
    "Arabic — Tunisia": "العربية — تونس",
    "Arabic — Algeria": "العربية — الجزائر",
    "Arabic — Morocco": "العربية — المغرب",
    # ---- settings: azure ----
    "Speech key:": "مفتاح Speech:",
    "Speech region:": "منطقة Speech:",
    "Translator key:": "مفتاح Translator:",
    "Translator region:": "منطقة Translator:",
    "e.g. westeurope, uaenorth, eastus": "مثل westeurope أو uaenorth أو eastus",
    "e.g. westeurope, or global": "مثل westeurope أو global",
    "Test connection": "اختبار الاتصال",
    "Forget saved keys": "حذف المفاتيح المحفوظة",
    "Testing…": "جارٍ الاختبار…",
    "Saved keys will be removed when you click Save.": "ستُحذف المفاتيح المحفوظة عند الضغط على حفظ.",
    "•••••••• saved — leave empty to keep": "•••••••• محفوظ — اتركه فارغاً للإبقاء عليه",
    "paste key here": "الصق المفتاح هنا",
    "Privacy: nothing is sent to Azure unless a profile uses it. Azure Speech receives your "
    "push-to-talk audio; Azure Translator receives only the recognised text. Keys are encrypted "
    "with your Windows account (DPAPI) before being saved.": (
        "الخصوصية: لا يُرسَل شيء إلى Azure إلا إذا استخدمه ملف تعريف. Azure Speech يستقبل صوتك "
        "أثناء الضغط فقط، وAzure Translator يستقبل النص فقط. المفاتيح تُشفَّر بحساب ويندوز "
        "(DPAPI) قبل حفظها."
    ),
    # ---- settings: hotkey ----
    "Press a key…": "اضغط زراً…",
    "Press a key or mouse button (Esc cancels)": "اضغط زراً أو زر ماوس (Esc للإلغاء)",
    "Talk key:": "زر التحدث:",
    "Push-to-talk (hold to record)": "الضغط المستمر (اضغط مع الاستمرار للتسجيل)",
    "Toggle (press to start, press again to stop)": "التبديل (اضغطة للبدء واضغطة للإيقاف)",
    "Mode:": "الطريقة:",
    "Replay key:": "زر الإعادة:",
    "The key still reaches the game — pick one the game doesn't use.": (
        "الزر يصل إلى اللعبة أيضاً — اختر زراً لا تستخدمه اللعبة."
    ),
    # ---- settings: overlay ----
    "Position:": "المكان:",
    "Offset from edge:": "البعد عن الطرف:",
    "Distance from the chosen screen edge": "المسافة عن طرف الشاشة المختار",
    "Monitor:": "الشاشة:",
    "Monitor with the game": "الشاشة التي عليها اللعبة",
    "Primary monitor": "الشاشة الرئيسية",
    "Font:": "الخط:",
    "Font size:": "حجم الخط:",
    "Maximum width:": "أقصى عرض:",
    "Background opacity:": "شفافية الخلفية:",
    "Text opacity:": "شفافية النص:",
    "Colours:": "الألوان:",
    "Text": "النص",
    "Background": "الخلفية",
    "Accent": "اللون المميز",
    "Choose a colour": "اختر لوناً",
    "Dark outline around the text": "إطار داكن حول النص",
    "Keeps text readable over bright scenes.": "يبقي النص مقروءاً فوق المشاهد الفاتحة.",
    "Corner radius:": "استدارة الزوايا:",
    "Display duration:": "مدة العرض:",
    "Long translations stay up a little longer so you can read them.": (
        "الترجمات الطويلة تبقى مدة أطول قليلاً لتتمكن من قراءتها."
    ),
    "Never auto-hide": "عدم الإخفاء تلقائياً",
    "Animation:": "الحركة:",
    "Fade in/out": "ظهور واختفاء تدريجي",
    "Preview": "معاينة",
    "Move overlay": "تحريك النافذة",
    "Top left": "أعلى اليسار",
    "Top center": "أعلى الوسط",
    "Top right": "أعلى اليمين",
    "Middle left": "منتصف اليسار",
    "Center": "الوسط",
    "Middle right": "منتصف اليمين",
    "Bottom left": "أسفل اليسار",
    "Bottom center": "أسفل الوسط",
    "Bottom right": "أسفل اليمين",
    # ---- settings: phrases / corrections ----
    "Key": "الزر",
    "Phrase": "الجملة",
    "Add phrase": "إضافة جملة",
    "Remove selected": "حذف المحدد",
    "A phrase can't use the talk key or the replay key. Phrases are per game.": (
        "لا يمكن للجملة استخدام زر التحدث أو زر الإعادة. الجمل خاصة بكل لعبة."
    ),
    "Find (English)": "ابحث عن (بالإنجليزية)",
    "Replace with": "استبدل بـ",
    "Add rule": "إضافة قاعدة",
    "Whole words only, upper/lower case ignored, applied once (no loops). Rules are per game.": (
        "كلمات كاملة فقط، بدون تمييز الحروف الكبيرة والصغيرة، تُطبَّق مرة واحدة (بدون تكرار). "
        "القواعد خاصة بكل لعبة."
    ),
    # ---- settings: gamepad ----
    "Talk button:": "زر التحدث:",
    "Replay button:": "زر الإعادة:",
    "Xbox controllers work directly. PlayStation controllers work through Steam Input or "
    "DS4Windows.": "يد Xbox تعمل مباشرة. يد بلايستيشن تعمل عبر Steam Input أو DS4Windows.",
    # ---- settings: teammates ----
    "Listen to:": "الاستماع إلى:",
    "Windows default output": "مخرج الصوت الافتراضي لويندوز",
    "Translate with:": "الترجمة بواسطة:",
    "Also show the original English": "عرض النص الإنجليزي الأصلي أيضاً",
    "Sensitivity:": "الحساسية:",
    "Higher catches quieter voices (and more noise).": "الأعلى يلتقط أصواتاً أخفض (وضجيجاً أكثر).",
    "Subtitle position:": "مكان الترجمة:",
    "Distance from edge:": "البعد عن الطرف:",
    "Uses some CPU/GPU while people are talking. It pauses while you talk and handles one "
    "sentence at a time.": (
        "يستهلك قليلاً من المعالج/كرت الشاشة أثناء كلام الآخرين. يتوقف أثناء كلامك ويعالج جملة "
        "واحدة في كل مرة."
    ),
    "Whisper (local)": "Whisper (محلي)",
    "Azure Speech (cloud)": "Azure Speech (سحابي)",
    "Offline model (on this PC)": "نموذج محلي (على جهازك)",
    "Don't translate (show English text)": "بدون ترجمة (عرض النص الإنجليزي)",
    # ---- settings: games ----
    "Game executables:": "ملفات تشغيل الألعاب:",
    "e.g. cs2.exe, VALORANT-Win64-Shipping.exe": "مثل cs2.exe أو VALORANT-Win64-Shipping.exe",
    "Switch to this profile automatically when the game is focused": (
        "التبديل لهذا الملف تلقائياً عند فتح اللعبة"
    ),
    "Each profile keeps its own hotkey, microphone, model, overlay position, size, opacity, "
    "vocabulary, quick phrases and correction rules. Find a game's .exe name in Task Manager > "
    "Details.": (
        "لكل ملف تعريف زره وميكروفونه ونموذجه ومكان النافذة وحجمها وشفافيتها وكلماته وجمله "
        "الجاهزة وقواعد التصحيح الخاصة به. اسم ملف اللعبة ‎.exe موجود في مدير المهام ← التفاصيل."
    ),
    # ---- feature descriptions ----
    "Press the replay key (F10) to show your last translation again.": "اضغط زر الإعادة (F10) لعرض آخر ترجمة مرة أخرى.",
    "Keeps your recent translations in memory; pick one from the tray menu to show it again.": "يحتفظ بآخر ترجماتك في الذاكرة؛ اختر أي واحدة من قائمة الأيقونة لعرضها مجدداً.",
    "Ready-made sentences on keys, shown instantly without speaking.": "جمل جاهزة على أزرار، تظهر فوراً بدون كلام.",
    "Fixes words that are often translated wrong (your own rules).": "يصحح الكلمات التي تُترجم خطأ كثيراً (بقواعدك أنت).",
    "Shows how to say the English sentence, written in Arabic letters.": "يعرض طريقة نطق الجملة الإنجليزية مكتوبة بحروف عربية.",
    "Hold a controller button (e.g. RB) to talk, like the keyboard hotkey.": "اضغط زراً في يد التحكم (مثل RB) للتحدث، مثل زر لوحة المفاتيح.",
    "Shows what your teammates say, translated, as subtitles.": "يعرض كلام زملائك في الفريق مترجماً كترجمة على الشاشة.",
    "Tells you once when a game hides the overlay, so you can switch to Borderless.": "ينبّهك مرة واحدة عندما تخفي اللعبة النافذة، لتغيّر إلى Borderless.",
    "Stops the recording even if Windows misses the moment you let go of the key.": "يوقف التسجيل حتى لو لم يلاحظ ويندوز لحظة ترك الزر.",
    "Sends only the part of the recording with speech: less data, faster, cheaper.": "يرسل الجزء الذي فيه كلام فقط: بيانات أقل، أسرع، وأرخص.",
    "Helps Azure Speech recognise game words like Medic or Flank.": "يساعد Azure Speech على فهم كلمات الألعاب مثل Medic وFlank.",
    "Small pop-up messages for warnings and tips.": "رسائل منبثقة صغيرة للتنبيهات والنصائح.",
    # ---- self-test, phrasebook, quick text, open mic, usage ----
    "A game is in exclusive fullscreen now — the overlay can't appear over it.": "لعبة تعمل الآن بملء الشاشة الحصري — لا يمكن للنافذة الظهور فوقها.",
    "A key opens a small box: type Arabic, press Enter, get English for text chat.": "زر يفتح مربعاً صغيراً: اكتب بالعربي واضغط Enter لتحصل على الإنجليزي للشات الكتابي.",
    "A short beep so you know GameTalk heard you, even without looking.": "صوت قصير لتعرف أن البرنامج سمعك دون أن تنظر.",
    "Add": "إضافة",
    "Add to quick phrases": "إضافة إلى الجمل الجاهزة",
    "Added. Give them keys in Settings → Quick phrases.": "تمت الإضافة. خصّص لها أزراراً من الإعدادات ← الجمل الجاهزة.",
    "Administrator": "صلاحيات المسؤول",
    "Again ↻": "مرة أخرى ↻",
    "An NVIDIA GPU was found but Whisper runs on the CPU.": "يوجد كرت NVIDIA لكن Whisper يعمل على المعالج.",
    "Arabic dialect corrections before translating": "تصحيح اللهجة العربية قبل الترجمة",
    "Azure usage counter and quota warnings": "عدّاد استهلاك Azure وتنبيهات الحصة",
    "Clear everything": "مسح الكل",
    "Close": "إغلاق",
    "Connect an Xbox controller (or use Steam Input / DS4Windows).": "وصّل يد Xbox (أو استخدم Steam Input / DS4Windows).",
    "Contains no speech and no keys — safe to share.": "لا يحتوي على كلامك ولا مفاتيحك — آمن للمشاركة.",
    "Controller connected.": "يد التحكم متصلة.",
    "Copy": "نسخ",
    "Copy report": "نسخ التقرير",
    "Copy translations to the clipboard": "نسخ الترجمات إلى الحافظة",
    "Counts how much of Azure's free monthly quota you've used and warns at 80% and 100%.": "يحسب كم استهلكت من حصة Azure المجانية الشهرية وينبّهك عند 80% و100%.",
    "Delete every saved phrase? This can't be undone.": "حذف كل العبارات المحفوظة؟ لا يمكن التراجع عن ذلك.",
    "Disk space": "مساحة القرص",
    "Downloaded": "تم التنزيل",
    "Export profile": "تصدير ملف التعريف",
    "Import profile": "استيراد ملف التعريف",
    "Export…": "تصدير…",
    "Import…": "استيراد…",
    "Fullscreen": "ملء الشاشة",
    "Game controller": "يد التحكم",
    "GameTalk runs as a normal user. Games started as administrator won't send it the hotkey — then run GameTalk as administrator too.": "البرنامج يعمل كمستخدم عادي. الألعاب المشغّلة كمسؤول لن ترسل له الزر — عندها شغّل البرنامج كمسؤول أيضاً.",
    "GameTalk runs as administrator.": "البرنامج يعمل بصلاحيات المسؤول.",
    "Graphics card": "كرت الشاشة",
    "Hotkeys": "الأزرار",
    "How do you say this in English?": "كيف تقول هذا بالإنجليزية؟",
    "I knew it ✓": "عرفتها ✓",
    "Imported as “{name}”.": "تم الاستيراد باسم «{name}».",
    "It will download on first use (internet needed once).": "سيُنزَّل عند أول استخدام (يلزم الإنترنت مرة واحدة).",
    "Keeps the sentences you use on this PC so you can practise them. Off = nothing saved.": "يحفظ الجمل التي تستخدمها على جهازك لتتدرب عليها. عند الإيقاف لا يُحفظ شيء.",
    "Learning mode (save my phrasebook)": "وضع التعلّم (حفظ دفتر عباراتي)",
    "Learning mode is off: phrases are only kept until GameTalk closes. Turn it on in Settings → Features to keep your phrasebook.": "وضع التعلّم متوقف: تُحفظ العبارات حتى إغلاق البرنامج فقط. فعّله من الإعدادات ← الميزات للاحتفاظ بدفترك.",
    "Listening for: {keys}": "يستمع إلى: {keys}",
    "Microphone": "الميكروفون",
    "Models need up to 3 GB. Free some space.": "النماذج تحتاج حتى 3 غيغا. وفّر بعض المساحة.",
    "My phrasebook": "دفتر عباراتي",
    "My phrases": "عباراتي",
    "NVIDIA GPU available": "كرت NVIDIA متاح",
    "No NVIDIA GPU: Whisper uses the CPU (slower). Azure mode avoids this.": "لا يوجد كرت NVIDIA: يعمل Whisper على المعالج (أبطأ). وضع Azure يتجنب ذلك.",
    "No controller connected.": "لا توجد يد تحكم متصلة.",
    "No phrases yet — use GameTalk and they'll appear here.": "لا توجد عبارات بعد — استخدم البرنامج وستظهر هنا.",
    "Not downloaded yet (~160 MB).": "لم يُنزَّل بعد (حوالي 160 ميغا).",
    "Not used by your current settings.": "غير مستخدم في إعداداتك الحالية.",
    "Offline translator (Arabic → English)": "المترجم المحلي (عربي ← إنجليزي)",
    "Offline translator (English → Arabic)": "المترجم المحلي (إنجليزي ← عربي)",
    "Open mic (no key needed — the key mutes/unmutes)": "المايك المفتوح (بدون زر — الزر للكتم وإلغائه)",
    "Open mic sensitivity:": "حساسية المايك المفتوح:",
    "Open mic: listening": "المايك المفتوح: يستمع",
    "Open mic: muted": "المايك المفتوح: مكتوم",
    "Open with:": "يُفتح بالزر:",
    "Opens and picks up sound.": "يعمل ويلتقط الصوت.",
    "Output device available.": "جهاز الصوت متاح.",
    "Overlay": "النافذة فوق اللعبة",
    "Paste the English yourself into a game's text chat (Ctrl+V). Nothing is typed for you.": "الصق الإنجليزي بنفسك في شات اللعبة الكتابي (Ctrl+V). لا يُكتب أي شيء نيابة عنك.",
    "Pick another microphone in Settings → Microphone.": "اختر ميكروفوناً آخر من الإعدادات ← الميكروفون.",
    "Practice": "التدريب",
    "Privacy: this is the only feature that saves what you said — the English sentences (and Arabic, when available) — in a file on this PC. Nothing is uploaded. Clear it any time from the phrasebook window.": "الخصوصية: هذه الميزة الوحيدة التي تحفظ ما قلته — الجمل الإنجليزية (والعربية إن وُجدت) — في ملف على جهازك. لا يُرفع شيء. امسحها متى شئت من نافذة دفتر العبارات.",
    "Quick text box (type Arabic, get English)": "مربع الكتابة السريع (اكتب عربي، واحصل على إنجليزي)",
    "Raise the microphone volume in Windows Sound settings.": "ارفع صوت الميكروفون من إعدادات الصوت في ويندوز.",
    "Ready (click-through, never takes focus).": "جاهزة (لا تعترض الماوس ولا تأخذ التركيز).",
    "Reset counter": "تصفير العدّاد",
    "Restart GameTalk.": "أعد تشغيل البرنامج.",
    "Run again": "إعادة الفحص",
    "Saved. Share this file with friends.": "تم الحفظ. شارك هذا الملف مع أصدقائك.",
    "Say the same thing often? GameTalk suggests putting it on a key.": "تكرر نفس الجملة كثيراً؟ البرنامج يقترح وضعها على زر.",
    "Say this out loud, then check the pronunciation:": "قلها بصوتك، ثم تحقق من النطق:",
    "Self-test": "الفحص الشامل",
    "Settings → Azure: check the key and region.": "الإعدادات ← Azure: تحقق من المفتاح والمنطقة.",
    "Settings → Speech → Run on: Auto. Update the NVIDIA driver if it persists.": "الإعدادات ← التعرّف على الكلام ← التشغيل على: تلقائي. حدّث تعريف NVIDIA إن استمرت المشكلة.",
    "Settings → Speech: pick another model, or connect to the internet once.": "الإعدادات ← التعرّف على الكلام: اختر نموذجاً آخر أو اتصل بالإنترنت مرة واحدة.",
    "Settings → Teammate subtitles → Listen to.": "الإعدادات ← ترجمة كلام الفريق ← الاستماع إلى.",
    "Show answer": "إظهار الجواب",
    "Skipped: you're recording right now.": "تم التخطي: أنت تسجّل الآن.",
    "Sound cues when recording starts/stops": "أصوات تنبيه عند بدء التسجيل وإيقافه",
    "Sound volume:": "مستوى صوت التنبيه:",
    "Speech engine": "محرك الكلام",
    "Speech: {m:.0f} of {mt:.0f} free minutes ({sp:.0%}) · Translator: {c:,} of {ct:,} free characters ({tp:.0%})": "Speech: {m:.0f} من {mt:.0f} دقيقة مجانية ({sp:.0%}) · Translator: {c:,} من {ct:,} حرف مجاني ({tp:.0%})",
    "Still loading…": "ما زال يُحمَّل…",
    "Suggest quick phrases for sentences you repeat": "اقتراح جمل جاهزة للجمل التي تكررها",
    "Suggestions (sentences you say often):": "اقتراحات (جمل تقولها كثيراً):",
    "Switch the game to Borderless or Windowed.": "غيّر اللعبة إلى Borderless أو Windowed.",
    "Teammate subtitles": "ترجمة كلام الفريق",
    "The box takes keyboard focus while it's open (you type into it); Esc closes it and returns to the game. The offline model downloads once (~160 MB).": "المربع يأخذ تركيز الكيبورد وهو مفتوح (لأنك تكتب فيه)؛ Esc يغلقه ويعيدك للعبة. النموذج المحلي يُنزَّل مرة واحدة (حوالي 160 ميغا).",
    "The hotkey listener isn't running.": "مستمع الأزرار لا يعمل.",
    "The microphone gives no sound at all.": "الميكروفون لا يعطي أي صوت.",
    "The microphone stays open while this mode is on. Audio stays in memory only.": "يبقى الميكروفون مفتوحاً ما دام هذا الوضع مفعّلاً. الصوت يبقى في الذاكرة فقط.",
    "The overlay window couldn't be created; results go to tray notifications.": "تعذّر إنشاء النافذة فوق اللعبة؛ النتائج تظهر كإشعارات بجانب الساعة.",
    "The selected output device isn't connected.": "جهاز الصوت المختار غير متصل.",
    "This isn't a GameTalk profile file.": "هذا ليس ملف تعريف لـ GameTalk.",
    "This month:": "هذا الشهر:",
    "Times": "المرات",
    "Tools:": "أدوات:",
    "Translating…": "جارٍ الترجمة…",
    "Turns dialect words into standard Arabic first (خليكم → ابقوا) for better translations.": "يحوّل كلمات اللهجة إلى الفصحى أولاً (خليكم ← ابقوا) لترجمة أفضل.",
    "Type Arabic, press Enter — Esc closes": "اكتب بالعربي واضغط Enter — Esc للإغلاق",
    "Unmute it, pick your real microphone in Settings → Microphone, or allow it in Windows Privacy → Microphone.": "ألغِ الكتم، أو اختر الميكروفون الحقيقي من الإعدادات ← الميكروفون، أو اسمح به من خصوصية ويندوز ← الميكروفون.",
    "Update your graphics driver and restart GameTalk.": "حدّث تعريف كرت الشاشة وأعد تشغيل البرنامج.",
    "Used when there is Arabic text to translate (Azure/Hybrid modes and the quick text box). Comes with common dialect words; edit freely.": "تُستخدم عندما يوجد نص عربي للترجمة (وضع Azure والوضع الهجين ومربع الكتابة السريع). تأتي مع كلمات لهجة شائعة؛ عدّلها كما تشاء.",
    "Whisper model": "نموذج Whisper",
    "Works, but very quiet.": "يعمل، لكن صوته منخفض جداً.",
    "You often say “{text}”. Add it as a quick phrase in Settings → Quick phrases.": "تقول «{text}» كثيراً. أضفها كجملة جاهزة من الإعدادات ← الجمل الجاهزة.",
    "{app} — My phrasebook": "{app} — دفتر عباراتي",
    "{app} — Self-test": "{app} — الفحص الشامل",
    "{gb:.1f} GB free": "{gb:.1f} غيغا متاحة",
    "{known} of {total} phrases known": "تعرف {known} من {total} عبارة",
    "{name}: 80% of this month's free quota used.": "{name}: تم استهلاك 80% من الحصة المجانية لهذا الشهر.",
    "{name}: this month's free quota is used up.": "{name}: انتهت الحصة المجانية لهذا الشهر.",
    "⚠️ Works, with {n} warning(s)": "⚠️ يعمل، مع {n} تنبيه",
    "✅ Everything looks good": "✅ كل شيء سليم",
    "❌ {n} problem(s) found": "❌ وُجدت {n} مشكلة",
    "📘  My phrasebook": "📘  دفتر عباراتي",
    "📘  Open my phrasebook": "📘  فتح دفتر عباراتي",
    "🩺  Run self-test": "🩺  تشغيل الفحص الشامل",
    "🩺  Self-test": "🩺  الفحص الشامل",
    "Dialect word": "كلمة اللهجة",
    "Standard Arabic": "الفصحى",
    "Automatic (Azure if keys are saved, otherwise offline)": "تلقائي (Azure إذا المفاتيح محفوظة، وإلا محلي)",
}
