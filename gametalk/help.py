# Copyright (c) 2026 Shkour Bashtawi (github.com/ShkourBashtawi). MIT License.
"""Built-in help: every feature explained in Arabic and English.

TOPICS[key] = (title_en, title_ar, summary_en, summary_ar, body_en, body_ar)
The summary is shown at the top of each settings page; the body in the Help window.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QTextBrowser,
    QVBoxLayout,
)

from . import APP_NAME, theme
from .i18n import language, tr

TOPICS: dict[str, tuple[str, str, str, str, str, str]] = {
    "start": (
        "Getting started",
        "البداية",
        "Hold your hotkey, speak Arabic, let go — read the English out loud in voice chat.",
        "اضغط زر التحدث مع الاستمرار، احكِ بالعربي، اترك الزر — واقرأ الجملة الإنجليزية بصوتك.",
        """<ol><li>Open GameTalk from the launcher (<b>Start</b>). It runs in the system tray.</li>
<li>In your game, <b>hold F9</b> (or your hotkey) and speak Arabic.</li>
<li>Release the key. A moment later the English sentence appears on top of the game.</li>
<li>Read it out loud in your normal game voice chat.</li></ol>
<p>GameTalk never types into the game and never speaks for you. It only shows text.</p>
<p>Tip: first time? Open <b>Settings → Microphone</b> and pick your real microphone.</p>""",
        """<ol><li>شغّل البرنامج من نافذة التحكم (<b>تشغيل</b>). بيشتغل كأيقونة جنب الساعة.</li>
<li>داخل اللعبة <b>اضغط F9 مع الاستمرار</b> (أو الزر اللي اخترته) واحكِ بالعربي.</li>
<li>اترك الزر، وبعد لحظة بتطلع الجملة بالإنجليزي فوق اللعبة.</li>
<li>اقرأها بصوتك بالمايك العادي تبع اللعبة.</li></ol>
<p>البرنامج ما بيكتب إشي بالعبة وما بيحكي عنك. بيعرض النص بس.</p>
<p>نصيحة: أول مرة؟ افتح <b>الإعدادات ← المايكروفون</b> واختار المايك الحقيقي تبعك.</p>""",
    ),
    "general": (
        "General",
        "عام",
        "Language of the program, notifications and the main on/off switch.",
        "لغة البرنامج، الإشعارات، والتشغيل والإيقاف العام.",
        """<p><b>Interface language</b>: Arabic, English, or automatic (follows Windows).</p>
<p><b>Enabled</b>: turns the whole program on or off without closing it (also in the tray).</p>
<p><b>Tray notifications</b>: small pop-ups for warnings (e.g. missing key, fullscreen).</p>""",
        """<p><b>لغة الواجهة</b>: عربي، إنجليزي، أو تلقائي حسب لغة ويندوز.</p>
<p><b>مفعّل</b>: بيشغّل أو بيوقف البرنامج كله بدون ما تسكّره (موجود كمان بقائمة الأيقونة).</p>
<p><b>إشعارات</b>: رسائل صغيرة للتنبيهات (مثل مفتاح ناقص أو وضع ملء الشاشة).</p>""",
    ),
    "microphone": (
        "Microphone",
        "المايكروفون",
        "Which microphone to listen to while you hold the key. Nothing is recorded otherwise.",
        "أي مايك بيسمع منه البرنامج وإنت ضاغط الزر. غير هيك ما بيسجّل إشي.",
        """<p>Pick your real microphone. "Windows default" uses whatever Windows has selected.</p>
<p><b>Refresh</b> re-scans devices (after plugging a USB mic in).</p>
<p><b>Test microphone</b> records 3 seconds and shows the translation, with a level bar.</p>
<p>If you see "No sound from the mic", the mic is muted, blocked in
<i>Windows Privacy → Microphone</i>, or it's a virtual device that is silent.</p>""",
        """<p>اختار المايك الحقيقي تبعك. «افتراضي ويندوز» بيستعمل المايك المختار بويندوز.</p>
<p><b>تحديث</b> بيعيد البحث عن الأجهزة (بعد ما توصّل مايك USB).</p>
<p><b>تجربة المايك</b> بيسجّل 3 ثواني وبيعرض الترجمة، مع شريط مستوى الصوت.</p>
<p>إذا طلعت «ما في صوت من المايك» يعني المايك مكتوم، أو ممنوع من
<i>خصوصية ويندوز ← الميكروفون</i>، أو جهاز وهمي صامت.</p>""",
    ),
    "speech": (
        "Speech recognition",
        "التعرّف على الكلام",
        "Who turns your voice into text: Whisper on this PC, or Azure Speech (most accurate).",
        "مين بيحوّل صوتك لنص: Whisper على جهازك، أو Azure Speech (الأدق).",
        """<p><b>Whisper (local)</b>: runs on your PC, free and private. Bigger models are more
accurate: <i>medium</i> is a good balance on a gaming GPU. Models download once.</p>
<p><b>Azure Speech</b>: Microsoft's cloud, best for Arabic dialects. Pick your dialect
(Saudi, Syrian, Egyptian…). Your push-to-talk audio is sent to Azure.</p>
<p><b>Run on</b>: Auto uses your NVIDIA GPU if available, otherwise the CPU.</p>
<p><b>Show original transcript</b>: also shows the Arabic text under the translation.</p>""",
        """<p><b>Whisper (محلي)</b>: بيشتغل على جهازك، مجاني وخاص. النماذج الأكبر أدق:
<i>medium</i> توازن ممتاز مع كرت شاشة ألعاب. النموذج بينزل مرة وحدة.</p>
<p><b>Azure Speech</b>: خدمة مايكروسوفت السحابية، الأفضل للهجات العربية. اختار لهجتك
(سعودي، سوري، مصري…). صوتك وقت الضغط بس بينبعث لـ Azure.</p>
<p><b>التشغيل على</b>: تلقائي بيستعمل كرت NVIDIA إذا موجود، وإلا المعالج.</p>
<p><b>عرض النص الأصلي</b>: بيعرض النص العربي تحت الترجمة كمان.</p>""",
    ),
    "translation": (
        "Translation",
        "الترجمة",
        "Who turns the text into English: Whisper (direct from voice) or Azure Translator.",
        "مين بيحوّل النص للإنجليزي: Whisper (مباشرة من الصوت) أو Azure Translator.",
        """<p><b>Whisper</b> translates straight from your voice to English, offline.</p>
<p><b>Azure Translator</b> translates the recognised text; only text is sent (not audio).
It can also translate to other languages.</p>
<p><b>Gaming translation mode</b>: short, casual squad-chat English.</p>
<p><b>Gaming vocabulary</b>: words like Medic, Flank, Revive help Whisper (and Azure Speech
with the phrase list) recognise game terms. It is a hint — it never replaces words.</p>""",
        """<p><b>Whisper</b> بيترجم من صوتك للإنجليزي مباشرة، بدون إنترنت.</p>
<p><b>Azure Translator</b> بيترجم النص؛ النص بس بينبعث (مش الصوت). وبيقدر يترجم
للغات ثانية كمان.</p>
<p><b>وضع ترجمة الألعاب</b>: إنجليزي قصير وعفوي مثل كلام الفريق.</p>
<p><b>كلمات الألعاب</b>: كلمات مثل Medic وFlank وRevive بتساعد Whisper (وAzure Speech مع
قائمة العبارات) يفهم مصطلحات اللعبة. هي تلميح بس — ما بتستبدل كلمات أبداً.</p>""",
    ),
    "azure": (
        "Cloud keys",
        "مفاتيح السحابة",
        "Keys for Microsoft Azure and Google Translate (only needed if you choose them).",
        "مفاتيح Microsoft Azure و Google Translate (بتلزم بس إذا اخترتهم).",
        """<ol><li>portal.azure.com → Create resource → <b>Speech</b> → Keys and Endpoint →
copy <b>Key 1</b> and <b>Location/Region</b>.</li>
<li>Create resource → <b>Translator</b> → copy its Key and Region (<i>global</i> for a global
resource).</li>
<li>Paste them in Settings → Azure, press <b>Test connection</b>, then Save.</li></ol>
<p>Keys are encrypted with your Windows account and never written to logs. The free F0
tiers are enough for voice chat.</p>
<p><b>Phrase list</b> (Features page): sends your gaming vocabulary to Azure Speech so it
recognises game words better.</p>
<p><b>Usage counter</b>: shows how much of this month's free quota you've used (5 audio hours
for Speech, 2 million characters for Translator) and warns you at 80% and 100%.</p>
<h3>Google Translate</h3>
<ol><li>console.cloud.google.com → create a project and turn on <b>billing</b> (a card is
required even for the free amount).</li>
<li>APIs &amp; Services → Library → enable <b>Cloud Translation API</b>.</li>
<li>APIs &amp; Services → Credentials → <b>Create API key</b> (restrict it to Cloud Translation
API).</li>
<li>Paste the key here, choose the model, press <b>Test Google</b>, then Save.</li></ol>
<p><b>Standard (NMT)</b>: the first 500,000 characters each month are free (about 16,000
short sentences), then $20 per million. <b>Translation LLM</b>: Google's smarter model, better
with dialect and context; it needs your <b>project ID</b> (shown on the Cloud console home page)
and costs $10 per million characters in + $10 per million out, from the same monthly
credit. Only the recognised text is sent to Google — never your voice.</p>""",
        """<ol><li>portal.azure.com ← إنشاء مورد ← <b>Speech</b> ← المفاتيح ونقطة النهاية ←
انسخ <b>Key 1</b> و<b>المنطقة</b>.</li>
<li>إنشاء مورد ← <b>Translator</b> ← انسخ المفتاح والمنطقة (<i>global</i> إذا المورد عالمي).</li>
<li>الصقهم بالإعدادات ← Azure، اضغط <b>اختبار الاتصال</b>، وبعدين حفظ.</li></ol>
<p>المفاتيح بتنحفظ مشفّرة بحساب ويندوز تبعك وما بتنكتب بالسجلات. الخطط المجانية F0
بتكفي للمحادثة الصوتية.</p>
<p><b>قائمة العبارات</b> (صفحة الميزات): بتبعث كلمات الألعاب لـ Azure Speech عشان يفهم
مصطلحات اللعبة أحسن.</p>
<p><b>عدّاد الاستهلاك</b>: بيوضح قديش استعملت من الحصة المجانية لهالشهر (5 ساعات صوت لـ Speech،
ومليونين حرف لـ Translator) وبينبّهك عند 80% و100%.</p>
<h3>Google Translate</h3>
<ol><li>console.cloud.google.com ← أنشئ مشروع وفعّل <b>الدفع (Billing)</b> (البطاقة إجبارية حتى
للكمية المجانية).</li>
<li>APIs &amp; Services ← Library ← فعّل <b>Cloud Translation API</b>.</li>
<li>APIs &amp; Services ← Credentials ← <b>Create API key</b> (وقيّده على Cloud Translation
API).</li>
<li>الصق المفتاح هون، اختار الموديل، اضغط <b>اختبار Google</b>، وبعدين حفظ.</li></ol>
<p><b>العادي (NMT)</b>: أول 500 ألف حرف كل شهر مجانية (تقريباً 16 ألف جملة قصيرة)، وبعدها 20$
لكل مليون حرف. <b>Translation LLM</b>: موديل جوجل الأذكى، أحسن مع اللهجة والسياق؛ بده
<b>رقم المشروع (Project ID)</b> (موجود بالصفحة الرئيسية للـ Cloud console)، وسعره 10$ لكل مليون حرف
داخل + 10$ لكل مليون حرف طالع، من نفس الرصيد الشهري. بس النص المفهوم بيروح لجوجل — صوتك أبداً.</p>""",
    ),
    "hotkey": (
        "Hotkeys",
        "الأزرار",
        "The key you hold to talk, the replay key, and push-to-talk vs toggle.",
        "زر التحدث، زر إعادة العرض، والضغط المستمر أو التبديل.",
        """<p><b>Push-to-talk</b>: hold to record, release to translate.
<b>Toggle</b>: press once to start, again to stop.</p>
<p>Supported: F1–F24, Insert, Home, End, PageUp, PageDown, Pause, ScrollLock, Numpad keys,
Mouse 4 and Mouse 5. Press <b>Press a key…</b> and then the key you want.</p>
<p>The key still reaches the game — choose one the game doesn't use.</p>
<p><b>Stuck-key protection</b> (Features): if Windows loses the key-up (e.g. an admin window
took focus), the recording still stops.</p>""",
        """<p><b>الضغط المستمر</b>: اضغط مع الاستمرار للتسجيل، واترك للترجمة.
<b>التبديل</b>: اضغطة للبدء، واضغطة ثانية للإيقاف.</p>
<p>المدعوم: F1–F24، Insert، Home، End، PageUp، PageDown، Pause، ScrollLock، أزرار
Numpad، وزر الماوس 4 و5. اضغط <b>اضغط زر…</b> وبعدين الزر اللي بدك ياه.</p>
<p>الزر بيوصل للعبة كمان — اختار زر اللعبة ما بتستعمله.</p>
<p><b>حماية الزر العالق</b> (الميزات): إذا ويندوز ضيّع ترك الزر (مثلاً نافذة أدمن أخذت
التركيز)، التسجيل بيوقف برضو.</p>""",
    ),
    "replay": (
        "Replay & history",
        "إعادة العرض والسجل",
        "Missed a sentence? Press the replay key (F10) to show the last one again.",
        "فاتتك جملة؟ اضغط زر الإعادة (F10) وبترجع آخر جملة للشاشة.",
        """<p><b>Replay key</b> (default F10) shows your last translation again.</p>
<p><b>History</b> keeps your last translations (in memory only, never saved to disk).
Right-click the tray icon → <b>Recent translations</b> and click one to show it again.</p>""",
        """<p><b>زر الإعادة</b> (الافتراضي F10) بيرجّع آخر ترجمة للشاشة.</p>
<p><b>السجل</b> بيحتفظ بآخر ترجماتك (بالذاكرة بس، ما بينحفظ على الجهاز).
كليك يمين على الأيقونة ← <b>الترجمات الأخيرة</b> واضغط أي وحدة لتظهر من جديد.</p>""",
    ),
    "phrases": (
        "Quick phrases",
        "الجمل الجاهزة",
        "Ready-made sentences on a key: shown instantly, no speaking needed.",
        "جمل جاهزة على أزرار: بتطلع فوراً بدون ما تحكي.",
        """<p>Give a phrase like <i>Enemy spotted!</i> a key (e.g. Numpad1). Pressing it shows the
sentence instantly — no recording, no waiting, no internet.</p>
<p>Each profile (game) has its own phrases. A phrase can't use the talk or replay key.</p>
<p><b>Suggestions</b>: when you say the same sentence 3 times, GameTalk suggests turning it into a
quick phrase (shown on this page with an Add button).</p>""",
        """<p>اعطِ جملة مثل <i>Enemy spotted!</i> زر (مثلاً Numpad1). لما تضغطه بتطلع الجملة
فوراً — بدون تسجيل ولا انتظار ولا إنترنت.</p>
<p>كل ملف تعريف (لعبة) إله جمله الخاصة. الجملة ما بتقدر تستعمل زر التحدث أو زر الإعادة.</p>
<p><b>الاقتراحات</b>: لما تقول نفس الجملة 3 مرات، البرنامج بيقترح تحطها كجملة جاهزة (بتطلع بهاي
الصفحة مع زر إضافة).</p>""",
    ),
    "corrections": (
        "Correction rules",
        "قواعد التصحيح",
        'Fix mistakes that keep coming back, e.g. "Zafira" → "ammo".',
        "صلّح غلطات بتتكرر، مثلاً «Zafira» ← «ammo».",
        """<p>Each rule replaces a whole word or phrase in the English result. It ignores upper
and lower case and only matches whole words ("ammo" won't touch "ammonia").</p>
<p>Rules run once, so they can never loop. Each game profile has its own rules.</p>
<p><b>Arabic dialect corrections</b> run <i>before</i> translating: they turn dialect words into
standard Arabic (e.g. خليكم → ابقوا, وراي → خلفي), which Azure and the offline model translate
much better. A starter list is included; edit it per game.</p>""",
        """<p>كل قاعدة بتستبدل كلمة أو عبارة كاملة بالترجمة الإنجليزية. ما بتفرق بين الحروف
الكبيرة والصغيرة، وبتطابق الكلمات الكاملة بس («ammo» ما بتلمس «ammonia»).</p>
<p>القواعد بتنطبق مرة وحدة، فما بتعلق بحلقة أبداً. كل لعبة إلها قواعدها.</p>
<p><b>تصحيح اللهجة العربية</b> بيصير <i>قبل</i> الترجمة: بيحوّل كلمات اللهجة لعربي فصيح (مثلاً
خليكم ← ابقوا، وراي ← خلفي)، وهيك Azure والنموذج المحلي بيترجموا أحسن بكثير. في قائمة جاهزة،
وبتقدر تعدّلها لكل لعبة.</p>""",
    ),
    "pronunciation": (
        "Pronunciation helper",
        "مساعد النطق",
        "Shows how to say the English sentence, written in Arabic letters.",
        "بيعرض طريقة نطق الجملة الإنجليزية مكتوبة بحروف عربية.",
        """<p>Under the English sentence you get e.g. <i>Wait for me</i> → «وايت فور مي».</p>
<p>Works offline with an English pronunciation dictionary (loaded only when this is on).</p>""",
        """<p>تحت الجملة الإنجليزية بيطلعلك مثلاً <i>Wait for me</i> ← «وايت فور مي».</p>
<p>بيشتغل بدون إنترنت بقاموس نطق إنجليزي (بينحمّل بس إذا الميزة مفعّلة).</p>""",
    ),
    "overlay": (
        "Overlay",
        "النافذة فوق اللعبة",
        "Where and how the text appears over your game. It never takes focus or clicks.",
        "وين وكيف بيطلع النص فوق اللعبة. ما بياخذ التركيز وما بيوقف الماوس.",
        """<p>Position, offset, monitor, size, font, colours, opacity, outline and how long the
text stays. <b>Preview</b> shows an example; <b>Move overlay</b> lets you drag it.</p>
<p>Long translations shrink or get shortened so they never cover the game, and stay a bit
longer so you can read them.</p>
<p>Games in <b>exclusive fullscreen</b> hide every overlay — use Borderless/Windowed.</p>""",
        """<p>المكان، البُعد عن الطرف، الشاشة، الحجم، الخط، الألوان، الشفافية، الإطار حول النص،
ومدة ظهور النص. <b>معاينة</b> بتعرض مثال، و<b>تحريك</b> بتخليك تسحبها.</p>
<p>الترجمات الطويلة بتصغر أو بتنقص عشان ما تغطي اللعبة، وبتضل مدة أطول لتلحق تقرأها.</p>
<p>الألعاب بوضع <b>ملء الشاشة الحصري</b> بتخفي أي نافذة فوقها —
استعمل Borderless أو Windowed.</p>""",
    ),
    "gamepad": (
        "Game controller",
        "يد التحكم",
        "Use a controller button (e.g. RB) as push-to-talk.",
        "استعمل زر من يد التحكم (مثلاً RB) كزر للتحدث.",
        """<p>Works with Xbox controllers (XInput). PlayStation controllers work through Steam
Input or DS4Windows. Pick the talk button and, optionally, a replay button.</p>
<p>Only while enabled, GameTalk reads the controller 60 times a second (very light).</p>""",
        """<p>بيشتغل مع يد Xbox (XInput). يد بلايستيشن بتشتغل عن طريق Steam Input أو DS4Windows.
اختار زر التحدث، وإذا بدك زر للإعادة.</p>
<p>وهي مفعّلة بس، البرنامج بيقرأ اليد 60 مرة بالثانية (خفيف جداً).</p>""",
    ),
    "teammates": (
        "Teammate subtitles",
        "ترجمة كلام الفريق",
        "Listens to what your PC plays (game / Discord) and shows teammates' speech in Arabic.",
        "بيسمع الصوت اللي طالع من جهازك (اللعبة / ديسكورد) وبيعرض كلام زملائك بالعربي.",
        """<p>Choose the output to listen to (your headset/speakers, or e.g. "Sonar - Chat" for
Discord only). Speech is recognised with Whisper or Azure, then translated with the
<b>offline model</b> (no internet, downloaded once ~160 MB) or <b>Azure Translator</b>.</p>
<p>It pauses while you talk and handles one sentence at a time, so it stays light. It uses
some GPU/CPU while people speak — turn it off if your game needs every frame.</p>
<p><b>Sensitivity</b>: higher catches quieter voices (and more noise).</p>""",
        """<p>اختار الصوت اللي بدك البرنامج يسمعه (السماعة، أو مثلاً «Sonar - Chat» لديسكورد بس).
الكلام بيتعرّف عليه Whisper أو Azure، وبيترجمه <b>النموذج المحلي</b> (بدون إنترنت، بينزل
مرة وحدة تقريباً 160 ميغا) أو <b>Azure Translator</b>.</p>
<p>بيوقف وإنت عم تحكي، وبيعالج جملة وحدة بكل مرة، فبيضل خفيف. بياخذ شوية من كرت الشاشة أو
المعالج وقت ما حدا يحكي — طفّيه إذا لعبتك بدها كل فريم.</p>
<p><b>الحساسية</b>: كل ما زادت بيلقط أصوات أوطى (ومعها ضجة أكثر).</p>""",
    ),
    "voice": (
        "Open mic",
        "المايك المفتوح",
        "No key needed: GameTalk notices when you start and stop talking.",
        "بدون زر: البرنامج بيعرف لحاله لما تبلش تحكي ولما توقف.",
        """<p>Choose <b>Open mic</b> in Settings → Hotkeys. GameTalk listens all the time, cuts your
speech into sentences and translates each one. Your talk key becomes a <b>mute/unmute</b> switch.</p>
<p>Noise that isn't speech (keyboard, game sounds) is ignored. The microphone stays open while
this mode is on — audio stays in memory only and is never saved.</p>
<p><b>Sensitivity</b>: higher catches quieter speech (and more noise).</p>""",
        """<p>اختار <b>المايك المفتوح</b> من الإعدادات ← الأزرار. البرنامج بيسمع طول الوقت، بيقسم كلامك
لجمل وبيترجم كل جملة. زر التحدث بيصير زر <b>كتم/إلغاء كتم</b>.</p>
<p>الضجة اللي مش كلام (الكيبورد، أصوات اللعبة) بتنتجاهل. المايك بيضل مفتوح وهاد الوضع شغال —
الصوت بالذاكرة بس وما بينحفظ أبداً.</p>
<p><b>الحساسية</b>: كل ما زادت بيلقط كلام أوطى (ومعه ضجة أكثر).</p>""",
    ),
    "quicktext": (
        "Quick text box",
        "مربع الكتابة السريع",
        "Press a key, type Arabic, press Enter — get English for text chat.",
        "اضغط زر، اكتب بالعربي، اضغط Enter — بتطلعلك الجملة بالإنجليزي للشات الكتابي.",
        """<p>Press the quick text key (default <b>F8</b>). A small box opens above the game: type
Arabic and press <b>Enter</b>. The English appears in the box and on the overlay; press
<b>Copy</b> (or turn on "copy translations to the clipboard") and paste it into the game's chat
yourself. <b>Esc</b> closes the box and returns to the game.</p>
<p>Translated with Azure Translator (if your key is saved) or the offline model (downloads once,
~160 MB). Dialect words are fixed first by the Arabic correction rules.</p>""",
        """<p>اضغط زر الكتابة السريعة (الافتراضي <b>F8</b>). بيطلع مربع صغير فوق اللعبة: اكتب بالعربي
واضغط <b>Enter</b>. الإنجليزي بيطلع بالمربع وعلى الشاشة؛ اضغط <b>نسخ</b> (أو فعّل «نسخ الترجمة»)
والصقها بشات اللعبة بنفسك. <b>Esc</b> بيسكّر المربع وبيرجعك للعبة.</p>
<p>الترجمة بـ Azure Translator (إذا مفتاحك محفوظ) أو بالنموذج المحلي (بينزل مرة وحدة تقريباً
160 ميغا). كلمات اللهجة بتتصلح أول بقواعد التصحيح العربية.</p>""",
    ),
    "learning": (
        "Learning mode",
        "وضع التعلّم",
        "Your own phrasebook of sentences you use, with practice cards.",
        "دفتر عبارات خاص فيك من الجمل اللي بتستعملها، مع بطاقات تدريب.",
        """<p>When learning mode is on, GameTalk keeps the English sentences you use (and the Arabic,
when available) in a phrasebook on this PC. Open it from the tray or launcher:</p>
<ul><li><b>My phrases</b>: most used first, with how to pronounce them. Add any to your quick
phrases in one click.</li>
<li><b>Practice</b>: see the Arabic, say the English out loud, then reveal to check. Mark "I knew
it" and the card moves back.</li></ul>
<p>Privacy: this is the only feature that saves what you said. It's off by default, never
uploaded, and you can clear it any time.</p>""",
        """<p>لما وضع التعلّم مفعّل، البرنامج بيحفظ الجمل الإنجليزية اللي بتستعملها (والعربي إذا موجود)
بدفتر على جهازك. افتحه من الأيقونة أو لوحة التحكم:</p>
<ul><li><b>عباراتي</b>: الأكثر استعمالاً أول، مع طريقة النطق. ضيف أي وحدة للجمل الجاهزة بضغطة.</li>
<li><b>التدريب</b>: بتشوف العربي، بتقول الإنجليزي بصوتك، وبعدين بتكشف الجواب. اضغط «عرفتها»
والبطاقة بتتأخر.</li></ul>
<p>الخصوصية: هاي الميزة الوحيدة اللي بتحفظ كلامك. موقوفة افتراضياً، ما بتنرفع لأي مكان، وبتقدر
تمسحها بأي وقت.</p>""",
    ),
    "sounds": (
        "Sound cues",
        "أصوات التنبيه",
        "A short beep when recording starts and stops.",
        "صوت قصير لما يبلش التسجيل ولما يوقف.",
        """<p>A rising beep means "listening", a falling beep means "got it, translating", a low beep
means something went wrong. Handy when the overlay is hidden (e.g. exclusive fullscreen). Set
the volume in Settings → General.</p>""",
        """<p>صوت طالع يعني «عم بسمعك»، صوت نازل يعني «وصلني، عم بترجم»، وصوت واطي يعني في مشكلة.
مفيد لما النافذة مخفية (مثلاً ملء الشاشة الحصري). بتضبط الصوت من الإعدادات ← عام.</p>""",
    ),
    "selftest": (
        "Self-test",
        "الفحص الشامل",
        "Checks every part of GameTalk in one click and tells you what to fix.",
        "بيفحص كل أجزاء البرنامج بضغطة وحدة وبيقلك شو لازم تصلح.",
        """<p>Checks the speech engine, graphics card, microphone (opens it for 1 second),
hotkeys, overlay, fullscreen, administrator rights, Azure keys, downloaded models, teammate
audio, game controller and disk space. Each problem comes with a suggested fix.</p>
<p><b>Copy report</b> gives a text you can send to someone helping you — it contains no speech
and no keys.</p>""",
        """<p>بيفحص محرك الكلام، كرت الشاشة، المايك (بيفتحه ثانية وحدة)، الأزرار، النافذة، ملء الشاشة،
صلاحيات المسؤول، مفاتيح Azure، النماذج المنزّلة، صوت الفريق، يد التحكم، ومساحة القرص. كل مشكلة
معها اقتراح للحل.</p>
<p><b>نسخ التقرير</b> بيعطيك نص تبعثه لحدا عم يساعدك — ما فيه كلامك ولا مفاتيحك.</p>""",
    ),
    "profiles": (
        "Game profiles",
        "ملفات الألعاب",
        "Different settings for each game, switched automatically when the game is focused.",
        "إعدادات مختلفة لكل لعبة، بتتبدل لحالها لما تفتح اللعبة.",
        """<p>Each profile has its own hotkey, microphone, model, providers, overlay position,
size, opacity, vocabulary, quick phrases and correction rules.</p>
<p>Add the game's .exe name (Task Manager → Details, e.g. <i>cs2.exe</i>) to switch
automatically when that game is in front.</p>
<p><b>Export / Import</b> saves a profile (phrases, corrections, vocabulary, overlay…) to a file
you can send to friends. Keys are never included.</p>""",
        """<p>كل ملف إله زر تحدث ومايك ونموذج ومزودين ومكان نافذة وحجم وشفافية وكلمات وجمل جاهزة
وقواعد تصحيح خاصة فيه.</p>
<p>ضيف اسم ملف اللعبة ‎.exe (مدير المهام ← التفاصيل، مثلاً <i>cs2.exe</i>) عشان يتبدل
الملف لحاله لما تكون اللعبة قدامك.</p>
<p><b>تصدير / استيراد</b> بيحفظ ملف تعريف (الجمل، التصحيحات، الكلمات، شكل النافذة…) بملف بتبعثه
لأصحابك. المفاتيح ما بتنضاف أبداً.</p>""",
    ),
    "features": (
        "Features on/off",
        "تشغيل وإيقاف الميزات",
        "Turn every optional system on or off.",
        "شغّل أو وقّف أي ميزة إضافية.",
        """<p>Everything extra can be switched off: replay, history, quick phrases, corrections,
pronunciation, gamepad, teammate subtitles, fullscreen warning, stuck-key protection,
silence trimming for Azure, Azure phrase list and notifications.</p>
<p>Switched-off features use no CPU, memory or network at all.</p>""",
        """<p>كل ميزة إضافية بتقدر توقفها: الإعادة، السجل، الجمل الجاهزة، التصحيح، النطق، يد
التحكم، ترجمة الفريق، تنبيه ملء الشاشة، حماية الزر العالق، قص الصمت قبل Azure، قائمة
عبارات Azure والإشعارات.</p>
<p>الميزة الموقوفة ما بتستهلك معالج ولا ذاكرة ولا إنترنت أبداً.</p>""",
    ),
    "privacy": (
        "Privacy & performance",
        "الخصوصية والأداء",
        "What stays on your PC, what goes to Azure, and how light GameTalk is.",
        "شو بيضل على جهازك، شو بيروح لـ Azure، وقديش البرنامج خفيف.",
        """<ul><li>Local mode: nothing leaves your PC.</li>
<li>Azure Speech: only your push-to-talk audio is sent. Azure Translator: only text.</li>
<li>Audio lives in memory only and is never saved. Logs never contain what you said.</li>
<li>Idle: 0% CPU, no polling. The microphone is closed until you press the key.</li>
<li>Nothing is injected into games; the hotkey uses Windows Raw Input.</li></ul>""",
        """<ul><li>الوضع المحلي: ولا إشي بيطلع من جهازك.</li>
<li>Azure Speech: صوتك وقت الضغط بس. Azure Translator: النص بس.</li>
<li>الصوت بالذاكرة بس وما بينحفظ أبداً. السجلات ما فيها كلامك.</li>
<li>وقت الراحة: 0% معالج، بدون فحص مستمر. المايك مسكّر لحتى تضغط الزر.</li>
<li>ما في أي حقن داخل الألعاب؛ الزر بيستعمل Raw Input تبع ويندوز.</li></ul>""",
    ),
    "trouble": (
        "Troubleshooting",
        "حل المشاكل",
        "Common problems and quick fixes.",
        "مشاكل شائعة وحلول سريعة.",
        """<ul><li><b>Overlay not visible in game</b>: switch the game to Borderless/Windowed.</li>
<li><b>Hotkey doesn't work in one game</b>: that game runs as administrator — run GameTalk
as administrator too.</li>
<li><b>"No sound from the mic"</b>: pick your real microphone in Settings → Microphone.</li>
<li><b>Wrong translations</b>: use a bigger Whisper model (medium), Azure mode, or add a
correction rule.</li>
<li><b>Azure errors</b>: Settings → Azure → Test connection shows what's wrong.</li></ul>""",
        """<ul><li><b>النافذة ما بتطلع باللعبة</b>: حط اللعبة على Borderless أو Windowed.</li>
<li><b>الزر ما بيشتغل بلعبة معيّنة</b>: اللعبة شغالة كمسؤول — شغّل البرنامج كمسؤول كمان.</li>
<li><b>«ما في صوت من المايك»</b>: اختار المايك الحقيقي من الإعدادات ← المايكروفون.</li>
<li><b>ترجمة غلط</b>: استعمل نموذج Whisper أكبر (medium)، أو وضع Azure، أو ضيف قاعدة تصحيح.</li>
<li><b>أخطاء Azure</b>: الإعدادات ← Azure ← اختبار الاتصال بيوضحلك شو المشكلة.</li></ul>""",
    ),
}


def title(key: str) -> str:
    t = TOPICS.get(key)
    return (t[1] if language() == "ar" else t[0]) if t else key


def summary(key: str) -> str:
    t = TOPICS.get(key)
    return (t[3] if language() == "ar" else t[2]) if t else ""


def body(key: str) -> str:
    t = TOPICS.get(key)
    return (t[5] if language() == "ar" else t[4]) if t else ""


class HelpDialog(QDialog):
    def __init__(self, topic: str | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("{app} — Help", app=tr(APP_NAME)))
        theme.apply(
            self,
            "QListWidget { background: #161619; border: 1px solid #222227; border-radius: 8px;"
            " padding: 4px; } QListWidget::item { padding: 7px 10px; border-radius: 6px; }"
            " QListWidget::item:selected { background: #3a1a0e; color: white; }"
            " QTextBrowser { background: #161619; border: 1px solid #222227;"
            " border-radius: 8px; padding: 10px; font-size: 11pt; }",
        )
        self.resize(820, 560)
        root = QHBoxLayout(self)
        self.list = QListWidget()
        self.list.setFixedWidth(220)
        for key in TOPICS:
            item = QListWidgetItem(title(key))
            item.setData(Qt.ItemDataRole.UserRole, key)
            self.list.addItem(item)
        self.view = QTextBrowser()
        self.view.setOpenExternalLinks(True)
        right = QVBoxLayout()
        right.addWidget(self.view)
        root.addWidget(self.list)
        root.addLayout(right, 1)
        self.list.currentItemChanged.connect(self._show)
        self.show_topic(topic or "start")

    def show_topic(self, key: str) -> None:
        for i in range(self.list.count()):
            if self.list.item(i).data(Qt.ItemDataRole.UserRole) == key:
                self.list.setCurrentRow(i)
                return

    def _show(self, item) -> None:
        if item is None:
            return
        key = item.data(Qt.ItemDataRole.UserRole)
        direction = "rtl" if language() == "ar" else "ltr"
        self.view.setHtml(
            f'<div dir="{direction}"><h2>{title(key)}</h2>'
            f'<p style="color:#8c8c96">{summary(key)}</p>{body(key)}</div>'
        )
