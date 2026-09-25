<div align="center">

<img src="docs/images/icon.png" width="96" alt="GameTalk icon">

# GameTalk Translator

**Speak Arabic. Read English. Keep playing.**<br>
**تكلّم عربي، اقرأ إنجليزي، وكمّل لعبك.**

[![Windows 10/11](https://img.shields.io/badge/Windows-10%20%7C%2011-0078D6?logo=windows&logoColor=white)](#en-install)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](#en-install)
[![Whisper](https://img.shields.io/badge/Whisper-local%20%26%20offline-22c55e)](#en-how)
[![Azure](https://img.shields.io/badge/Azure-optional-0089D6?logo=microsoftazure&logoColor=white)](#en-azure)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**[English](#english)** · **[العربية](#arabic)**

<img src="docs/images/overlay-in-game.png" alt="GameTalk overlay on top of a game" width="900">

<sub>Bottom: your Arabic, translated to English, with pronunciation help. Top: a teammate's English, subtitled in Arabic.</sub>

</div>

---

<a id="english"></a>

## 🇬🇧 English

### Contents

- [What is GameTalk?](#en-what)
- [Highlights](#en-highlights)
- [Screenshots](#en-screenshots)
- [How it works](#en-how)
- [Installation](#en-install)
- [First run: 5 minutes](#en-first-run)
- [Everyday use](#en-usage)
- [Speech and translation engines](#en-engines)
- [Azure (optional)](#en-azure)
- [All features](#en-features)
- [Settings pages](#en-settings)
- [Profiles per game](#en-profiles)
- [Privacy](#en-privacy)
- [Performance](#en-performance)
- [Troubleshooting](#en-troubleshooting)
- [For developers](#en-developers)
- [Author and license](#en-license)

<a id="en-what"></a>

### 🎮 What is GameTalk?

GameTalk Translator is a small Windows app for Arabic-speaking gamers who play with
English-speaking teammates.

1. **Hold a key** (default **F9**) and speak Arabic, in any dialect.
2. **Let go.** About a second later, a small overlay above your game shows the sentence in natural
   English, e.g. «خليكم وراي، أنا رح أفتح الباب» → *"Stay behind me, I'll open the door."*
3. **Say it** yourself on voice chat, with optional Arabic-letter pronunciation help.

It also works the other way: **teammate subtitles** translate what your teammates say into Arabic
subtitles.

> **Safe for games.** GameTalk never speaks for you, never types into a game, and never injects
> into, hooks or modifies any game. It listens for its hotkey through Windows Raw Input and draws
> a click-through window that never takes focus away from your game.

<a id="en-highlights"></a>

### ✨ Highlights

| | |
|---|---|
| 🎙️ **Push-to-talk, toggle or open mic** | Keyboard key, mouse button (Mouse4/5) or controller button (RB, …) |
| 💻 **Works fully offline** | Whisper runs on your NVIDIA GPU or your CPU; nothing leaves your PC |
| ☁️ **Optional Azure** | Dialect-aware Azure Speech and Azure Translator, each chosen separately |
| 🪟 **Overlay that stays out of your way** | Click-through, never steals focus, per-game position, size, colours and fonts |
| 👥 **Teammate subtitles** | Translates what you *hear* (game or Discord) into Arabic |
| ⌨️ **Quick text box** | Press F8, type Arabic, get English for text chat |
| 💬 **Quick phrases** | "Enemy spotted!" on Numpad1, shown instantly |
| 📘 **Learning mode** | Your personal phrasebook plus flash cards, so you need the app less over time |
| 🇸🇦 **Full Arabic interface** | Right-to-left UI, and every feature explained in Arabic and English |
| 🪶 **Lightweight** | 0% CPU when idle; the mic is only open while you hold the key |

<a id="en-screenshots"></a>

### 📸 Screenshots

| Launcher | Settings |
|:---:|:---:|
| <img src="docs/images/launcher-en.png" width="330"> | <img src="docs/images/settings-features-en.png" width="520"> |
| **Overlay states** | **Quick text box (F8)** |
| <img src="docs/images/overlay-states.png" width="520"> | <img src="docs/images/quicktext-en.png" width="420"> |
| **Self-test** | **My phrasebook** |
| <img src="docs/images/selftest-en.png" width="420"> | <img src="docs/images/phrasebook-en.png" width="460"> |

<details>
<summary><b>More screenshots: every settings page</b></summary>

| | |
|:---:|:---:|
| General<br><img src="docs/images/settings-general-en.png" width="440"> | Microphone<br><img src="docs/images/settings-microphone-en.png" width="440"> |
| Speech recognition<br><img src="docs/images/settings-speech-en.png" width="440"> | Translation<br><img src="docs/images/settings-translation-en.png" width="440"> |
| Azure keys<br><img src="docs/images/settings-azure-en.png" width="440"> | Hotkeys<br><img src="docs/images/settings-hotkey-en.png" width="440"> |
| Overlay<br><img src="docs/images/settings-overlay-en.png" width="440"> | Quick phrases<br><img src="docs/images/settings-phrases-en.png" width="440"> |
| Correction rules<br><img src="docs/images/settings-corrections-en.png" width="440"> | Quick text box<br><img src="docs/images/settings-quicktext-en.png" width="440"> |
| Learning mode<br><img src="docs/images/settings-learning-en.png" width="440"> | Game controller<br><img src="docs/images/settings-gamepad-en.png" width="440"> |
| Teammate subtitles<br><img src="docs/images/settings-teammates-en.png" width="440"> | Games (auto profiles)<br><img src="docs/images/settings-games-en.png" width="440"> |
| Built-in help<br><img src="docs/images/help-en.png" width="440"> | |

</details>

<a id="en-how"></a>

### ⚙️ How it works

```mermaid
flowchart LR
    K["Hold F9"] --> M["Mic records<br/>(RAM only)"]
    M --> S{"Speech → text"}
    S -->|"Whisper (this PC)"| W["Arabic audio →<br/>English text"]
    S -->|"Azure Speech"| AS["Arabic text<br/>(your dialect)"]
    AS --> T{"Text → translation"}
    T -->|"Azure Translator"| AT["English or<br/>14 other languages"]
    T -->|"Offline model"| OM["English"]
    W --> O["Overlay above the game"]
    AT --> O
    OM --> O
```

The two steps are chosen **separately** in the launcher:

| Step | On this PC (free, private) | Azure (cloud, most accurate for dialects) |
|---|---|---|
| **1. Speech → text** | Whisper `tiny` → `large-v3`, on GPU (CUDA) or CPU | Azure Speech with 17 Arabic dialects (ar-SA, ar-JO, ar-EG, …) |
| **2. Text → translation** | Whisper translates straight to English | Azure Translator: English or 14 other languages |

<a id="en-install"></a>

### 📦 Installation

#### Option A: installer (recommended)

1. Download **`GameTalk-Setup-x.y.z.exe`** from the
   **[Releases page](https://github.com/Cavebest/GameTalk/releases/latest)**.
2. Run it and choose **English or Arabic**. It installs to `Program Files` by default. You can
   pick *"Install for me only"* if you don't have admin rights.
3. Optional: desktop shortcut, and start with Windows.

You don't need Python. NVIDIA GPU support (cuBLAS) is included, and without an NVIDIA GPU the app
runs on the CPU. To uninstall, go to **Windows Settings → Apps**. Your settings in
`%APPDATA%\GameTalk` are kept.

> Windows SmartScreen may warn that the app is from an *unknown publisher* because it isn't
> code-signed. Click **More info → Run anyway**.

#### Option B: from source

Requires Windows 10/11 and [Python 3.10+](https://www.python.org/downloads/) (tested on 3.14).

```bash
git clone https://github.com/Cavebest/GameTalk.git
```

Then double-click **`GameTalk.bat`**. The first time, it creates `.venv` and installs everything
(GPU support is added automatically if an NVIDIA GPU is found). After that it opens the launcher.

<details>
<summary>Manual install</summary>

```bash
py -m venv .venv
```

```bash
.venv\Scripts\pip install -e .[cuda]
```

```bash
.venv\Scripts\python -m gametalk.launcher
```

`[cuda]` adds NVIDIA's cuBLAS runtime so Whisper can use an NVIDIA GPU without installing the
CUDA toolkit. Leave it off on machines without an NVIDIA GPU. cuDNN is not needed. If a GPU ever
reports a missing `cudnn*.dll`, run `pip install nvidia-cudnn-cu12`.

</details>

<a id="en-first-run"></a>

### 🚀 First run: 5 minutes

1. **Open the launcher**: the *GameTalk* shortcut, `GameTalk.exe`, or `GameTalk.bat`.
2. **Pick your engines** (step 1 and step 2). The default is Whisper on this PC.
3. **Settings → Microphone**: pick your real headset mic and try **Test**.
4. Click **▶ Start GameTalk**. It moves to the system tray next to the clock.
   - The first time, the Whisper model downloads once (`small` ≈ 480 MB). After that it works
     offline.
5. In your game, **hold F9, speak Arabic, and let go**.
6. Something not working? Run **🩺 Self-test**. It checks everything and tells you what to fix.

> 💡 Use **Borderless** or **Windowed** fullscreen in your game. *Exclusive* fullscreen hides every
> overlay, and GameTalk will warn you once if it detects it.

<a id="en-usage"></a>

### 🕹️ Everyday use

| Action | Default |
|---|---|
| Talk (push-to-talk) | **Hold F9**, speak, release |
| Toggle mode | Press once to start and again to stop |
| Open mic | No key: GameTalk hears when you start and stop talking, and the key mutes/unmutes |
| Show the last translation again | **F10** |
| Quick text box (type instead of talk) | **F8** |
| Quick phrases | Any key you assign, e.g. **Numpad1** → *"Enemy spotted!"* |
| Controller | An Xbox/XInput button, e.g. **RB** |
| Tray menu | Enable/Disable, profile, recent translations, settings, self-test, help, exit |

- **Keep talking**: you can start the next sentence while the previous one is still being
  translated. A small red dot means *"you are still recording"*.
- An accidental short tap just shows *"Hold F9 while you speak"*. Mouse-button chatter is ignored.
- Supported keys: F1–F24, Insert, Home, End, PageUp/Down, Pause, ScrollLock, numpad keys,
  Mouse4 and Mouse5. The key still reaches the game, so pick one the game doesn't use.

<a id="en-engines"></a>

### 🧠 Speech and translation engines

| Model | Size | Notes |
|---|---|---|
| `tiny` / `base` | 75–145 MB | Very fast, weaker with dialects |
| **`small`** (default) | ~480 MB | Good balance, well under a second on GPU |
| `medium` | ~1.5 GB | Noticeably more natural English for Gulf, Levantine and Egyptian dialects |
| `large-v3` | ~3 GB | Most accurate local model (~3 GB VRAM) |

**Offline text translation** uses small OPUS-MT models (Arabic ⇄ English). They power the quick
text box and teammate subtitles without Azure.

**Arabic dialect corrections** run before text translation and turn dialect words into standard
Arabic (خليكم → ابقوا, هلق → الآن, …). This makes offline models and Azure much more accurate.
The starter list is editable per game.

<a id="en-azure"></a>

### ☁️ Azure (optional)

Use Azure if you want the best accuracy for your **dialect**. The free **F0** tiers are enough
for voice chat: 5 hours of speech and 2 million characters of translation per month. GameTalk
counts your usage and warns at 80% and 100%.

1. Go to [portal.azure.com](https://portal.azure.com/) → **Create a resource** → **Speech** →
   *Keys and Endpoint*. Copy **Key 1** and the **Location/Region**.
2. **Create a resource** → **Translator**. Copy its **Key** and **Region** (`global` for a global
   resource).
3. In the launcher, click **🔑 Azure keys**. Paste the values, click **Test connection**, then
   **Save**.

One *Azure AI services* multi-service resource also works: use the same key and region twice.
Keys are **encrypted with your Windows account (DPAPI)** and are never logged or exported.

| Launcher choice | What is sent to Azure |
|---|---|
| Whisper + Whisper | Nothing |
| Whisper + Azure Translator | The recognised **text** only |
| Azure Speech + Azure Translator | Your push-to-talk **audio**, with silence trimmed, plus the text |

<a id="en-features"></a>

### 🧩 All features

You can switch every feature on or off in **Settings → Features on/off**. A switched-off feature
uses no CPU, memory or network. Every feature has a **?** button with a full explanation in
Arabic and English.

| Feature | What it does | Default |
|---|---|:---:|
| 🔁 Replay key | **F10** shows your last translation again | On |
| 🕘 History | Your last translations in the tray menu (memory only) | On |
| 💬 Quick phrases | Ready-made sentences on keys, shown instantly with no speech needed | Off |
| 💡 Quick-phrase suggestions | Say the same sentence three times and GameTalk offers to put it on a key | On |
| ✏️ Correction rules | Your own fixes, e.g. *"Zafira" → "ammo"* (whole words, one pass) | On |
| 🇸🇦 Arabic dialect corrections | Dialect → standard Arabic before translating | On |
| 🔤 Pronunciation helper | Shows the English in Arabic letters: *"Wait for me"* → «وايت فور مي» | Off |
| 🎮 Game controller | An XInput button as push-to-talk, plus an optional replay button | Off |
| 👥 Teammate subtitles | Listens to what your PC plays and shows teammates' speech in Arabic. Uses Whisper or Azure for recognition, and the offline model or Azure for translation | Off |
| ⌨️ Quick text box | **F8**: type Arabic, press Enter, get English. You can copy it for text chat | Off |
| 🎙️ Open mic | No key needed. Voice activity detection finds the start and end of each sentence | Off |
| 📘 Learning mode | Your phrasebook plus flash-card practice. This is the only feature that saves what you said, and only on this PC | Off |
| 📋 Copy to clipboard | Puts each translation on the clipboard for you to paste yourself | Off |
| 🔔 Sound cues | Soft beeps when recording starts and stops (volume adjustable) | Off |
| 📊 Azure usage counter | Tracks this month's free quota | On |
| 🗣️ Azure phrase list | Sends your gaming vocabulary to Azure Speech so it recognises *Medic*, *Flank*, … | On |
| 🖥️ Fullscreen warning | Tells you once when a game uses exclusive fullscreen | On |
| 🧷 Stuck-key protection | Stops recording even if Windows misses the key release | On |
| ✂️ Silence trimming | Sends only the speech part to Azure: less data, faster and cheaper | On |
| 🔔 Tray notifications | Short notices from the tray icon | On |

**Tools**
- **🩺 Self-test** checks the model, GPU, microphone, hotkeys, overlay, Azure, downloaded models,
  controller and disk space, then suggests fixes. Its report contains no speech and no keys.
- **Export / Import profile** shares a game profile (phrases, corrections, overlay, …) as a file.
  Keys are never included.

<a id="en-settings"></a>

### 🛠️ Settings pages

| Page | What you can change |
|---|---|
| General | Interface language (Arabic/English/auto), enable/disable, notifications, start with Windows, sound cues, clipboard |
| Features on/off | Every switch from the table above, with explanations |
| Microphone | Input device, refresh after plugging in, live level meter, 3-second test |
| Speech recognition | Whisper model, GPU/CPU/Auto, spoken language, Azure dialect, show the original text |
| Translation | Engine, target language, gaming mode (short, natural sentences), gaming vocabulary |
| Azure keys | Speech key and region, Translator key and region, connection test, usage |
| Hotkeys | Talk key (or press-to-capture), push/toggle/open mic, replay key, quick-text key |
| Overlay | Position, offset, monitor, font, size, width, colours, opacity, corners, duration, fade, preview, drag to move |
| Quick phrases | Key → sentence table, plus suggestions |
| Correction rules | Your word fixes and the Arabic dialect list |
| Quick text box | Key, and which translator (auto/offline/Azure) |
| Learning mode | Phrasebook on/off, open the phrasebook |
| Game controller | Talk button and replay button |
| Teammate subtitles | Output device, recogniser, translator, target language, sensitivity, position, font and duration |
| Games | The game `.exe` names that switch profiles automatically |

<a id="en-profiles"></a>

### 🎯 Profiles per game

Each profile keeps its own hotkey, mode, microphone, model, engines, overlay position, size,
opacity, font, duration, vocabulary, quick phrases and corrections. Add the game's executable
name (Task Manager → Details, e.g. `cs2.exe`), and the profile switches on automatically when that
game gets focus.

<a id="en-privacy"></a>

### 🔒 Privacy

- **Local mode sends nothing.** Recognition and translation run on your PC.
- The **mic is open only while you hold the key**. Audio lives in RAM and is discarded after each
  sentence. Nothing is recorded to disk.
- **Logs** (`%APPDATA%\GameTalk\logs`) contain timings and error types only, never what you said.
- **Azure keys** are encrypted with Windows DPAPI and never written in plain text.
- The only other network access is the one-time model download from Hugging Face, with telemetry
  off.
- Learning mode is **opt-in**, and it is the only place sentences are stored (`phrasebook.json`,
  on this PC).

<a id="en-performance"></a>

### ⚡ Performance

- **Idle CPU: 0%.** GameTalk runs no polling or timers while idle, and the mic is closed.
- The hotkey uses **Raw Input**, not keyboard hooks. It sits outside the game's input path, so it
  adds **no input latency**.
- A translation appears **~0.1–0.3 s** after you release the key (NVIDIA GPU, `medium`).

| Mode | RAM | Note |
|---|---|---|
| Local, GPU | ~800 MB (+ ~1 GB VRAM) | The model stays loaded for instant replies |
| Local, CPU | ~430 MB | |
| Azure | ~90 MB | No local model loaded |
| + subtitles / pronunciation / controller | +~120 MB | Offline EN→AR model and dictionary |

<a id="en-troubleshooting"></a>

### 🧯 Troubleshooting

| Problem | Fix |
|---|---|
| I can't see the overlay in my game | Switch the game to **Borderless** or **Windowed** fullscreen |
| Nothing happens when I press the key in the game | If the game runs **as administrator**, run GameTalk as administrator too |
| "Didn't catch that" | Check the mic in **Settings → Microphone → Test**, and hold the key a moment longer |
| The translation isn't accurate | Try `medium` or `large-v3`, or Azure Speech with your dialect, and add correction rules |
| The first translation is slow | The first run on a new GPU compiles once (~20 s). It's instant after that |
| Mic unplugged or changed | **Settings → Microphone → Refresh**. GameTalk also retries automatically |
| Anything else | Run **🩺 Self-test**, then **Copy report** (safe to share) |

> Some kernel-level anti-cheats dislike any overlay. GameTalk doesn't inject or hook anything,
> but check your game's rules.

<a id="en-developers"></a>

### 👩‍💻 For developers

```bash
.venv\Scripts\pip install -e .[cuda,dev]
```

```bash
.venv\Scripts\python -m pytest
```

```bash
.venv\Scripts\ruff check .
```

**Command line:** `python -m gametalk [--settings] [--azure] [--test-mic] [--selftest]
[--phrasebook] [--verbose]`. If GameTalk is already running, these options are forwarded to the
running copy.

**Build the installer:** run `packaging\build_installer.bat`. It uses PyInstaller to build
`dist\GameTalk\GameTalk.exe`, and Inno Setup 6 to build `dist\GameTalk-Setup-<version>.exe`. Set
`GAMETALK_CUDA=0` for a smaller build without NVIDIA support.

<details>
<summary>Project structure</summary>

| Module | Role |
|---|---|
| `gametalk/__main__.py` | Startup, logging, single instance |
| `gametalk/app.py` | Controller: hotkey → recorder → speech worker → overlay |
| `gametalk/hotkey.py` | Global hotkeys via Raw Input, foreground-game watcher |
| `gametalk/audio.py` | Push-to-talk recorder, device list, silence trimming |
| `gametalk/speech.py` | faster-whisper on a worker thread, CUDA → CPU fallback |
| `gametalk/translate.py` | Speech → text → translation pipelines, gaming mode, cleanup |
| `gametalk/azure.py` | Azure Speech (REST + SDK phrase lists) and Translator v3 |
| `gametalk/local_mt.py` | Offline OPUS-MT Arabic ⇄ English (CTranslate2) |
| `gametalk/overlay.py` | Click-through overlay that never takes focus |
| `gametalk/teammates.py` | Loopback capture for teammate subtitles |
| `gametalk/voice.py` | Open-mic voice activity detection |
| `gametalk/gamepad.py` | XInput controller buttons |
| `gametalk/quick_text.py`, `learn.py`, `phrasebook.py` | Quick text box, learning mode |
| `gametalk/pronounce.py` | English → Arabic-letter pronunciation (CMUdict) |
| `gametalk/diagnostics.py` | Self-test |
| `gametalk/launcher.py`, `settings_dialog.py`, `tray.py`, `help.py`, `theme.py` | UI |
| `gametalk/i18n.py`, `i18n_ar.py` | Arabic/English interface |
| `gametalk/config.py`, `credentials.py`, `usage.py` | Settings, DPAPI keys, Azure usage |
| `gametalk/ipc.py`, `runtime.py`, `win32.py` | Launcher ↔ app channel, startup, Win32 bindings |
| `packaging/` | PyInstaller spec, Inno Setup script, icon and version resources |
| `tests/` | 170+ pytest tests |

</details>

<a id="en-license"></a>

### 👤 Author and license

Created by **[Shkour Bashtawi](https://github.com/ShkourBashtawi)**.
Released under the **[MIT License](LICENSE)**. Third-party components (faster-whisper,
CTranslate2, Qt/PySide6, Whisper and OPUS-MT models, Microsoft Azure services) remain under their
own licenses and terms.

<div align="right"><a href="#english">⬆ Back to top</a></div>

---

<a id="arabic"></a>

<div dir="rtl">

## 🇸🇦 العربية

### المحتويات

- [شو هو GameTalk؟](#ar-what)
- [أهم المميزات](#ar-highlights)
- [صور من البرنامج](#ar-screenshots)
- [كيف بيشتغل؟](#ar-how)
- [التثبيت](#ar-install)
- [أول تشغيل: 5 دقائق](#ar-first-run)
- [الاستعمال اليومي](#ar-usage)
- [محركات التعرّف والترجمة](#ar-engines)
- [Azure (اختياري)](#ar-azure)
- [كل الميزات](#ar-features)
- [صفحات الإعدادات](#ar-settings)
- [ملف تعريف لكل لعبة](#ar-profiles)
- [الخصوصية](#ar-privacy)
- [الأداء](#ar-performance)
- [حل المشاكل](#ar-troubleshooting)
- [المطوّر والترخيص](#ar-license)

<a id="ar-what"></a>

### 🎮 شو هو GameTalk؟

GameTalk Translator برنامج صغير على ويندوز للاعبين العرب اللي بيلعبوا مع فريق بيحكي إنجليزي.

1. **اضغط الزر مع الاستمرار** (الافتراضي **F9**) واحكِ عربي بأي لهجة.
2. **اترك الزر**، وخلال ثانية تقريباً بتطلع لك الجملة بإنجليزي طبيعي فوق اللعبة.
   مثال: «خليكم وراي، أنا رح أفتح الباب» ← *"Stay behind me, I'll open the door."*
3. **اقرأها بصوتك** على الفويس شات. وإذا بدك، بيعرض لك كمان طريقة نطقها بحروف عربية.

وبيشتغل بالعكس كمان: **ترجمة كلام الفريق** بتعرض كلام زملائك مترجم للعربي كترجمة على الشاشة.

> **آمن مع الألعاب:** البرنامج ما بيحكي عنك، وما بيكتب شي باللعبة، وما بيدخل على ملفات اللعبة
> أو بيعدّلها أبداً. كل اللي بيعمله إنه يسمع زره، ويرسم نافذة شفافة فوق اللعبة ما بتاخذ منها
> التركيز وما بتمنع الماوس.

<a id="ar-highlights"></a>

### ✨ أهم المميزات

| | |
|---|---|
| 🎙️ **ضغط مستمر أو ضغطة تشغيل/إيقاف أو مايك مفتوح** | زر كيبورد، أو زر ماوس جانبي (Mouse4/5)، أو زر يد تحكم (RB مثلاً) |
| 💻 **بيشتغل بدون إنترنت** | Whisper بيشتغل على كرت NVIDIA أو المعالج، وما بيطلع شي من جهازك |
| ☁️ **Azure اختياري** | Azure Speech بيفهم اللهجات، وAzure Translator للترجمة، وكل واحد بتختاره لحال |
| 🪟 **نافذة ما بتزعجك** | الماوس بيمرّ من خلالها وما بتسرق التركيز، ومكانها وحجمها وألوانها قابلة للتخصيص لكل لعبة |
| 👥 **ترجمة كلام الفريق** | بيترجم اللي *بتسمعه* (من اللعبة أو الديسكورد) للعربي |
| ⌨️ **مربع الكتابة السريع** | اضغط F8 واكتب عربي، بيطلع لك إنجليزي للشات الكتابي |
| 💬 **جمل جاهزة** | مثلاً *"Enemy spotted!"* على Numpad1، وبتظهر فوراً |
| 📘 **وضع التعلّم** | دفتر عباراتك وبطاقات تدريب، لحتى تصير تعتمد عليه أقل مع الوقت |
| 🇸🇦 **واجهة عربية كاملة** | من اليمين لليسار، وكل ميزة مشروحة بالعربي والإنجليزي |
| 🪶 **خفيف** | 0% معالج وهو مش شغّال، والمايك بيفتح بس وإنت ضاغط الزر |

<a id="ar-screenshots"></a>

### 📸 صور من البرنامج

| لوحة التحكم | الإعدادات |
|:---:|:---:|
| <img src="docs/images/launcher-ar.png" width="330"> | <img src="docs/images/settings-features-ar.png" width="520"> |
| **الإعدادات: الترجمة** | **المساعدة المدمجة** |
| <img src="docs/images/settings-translation-ar.png" width="460"> | <img src="docs/images/help-ar.png" width="460"> |
| **الإعدادات: النافذة فوق اللعبة** | **الإعدادات: ترجمة كلام الفريق** |
| <img src="docs/images/settings-overlay-ar.png" width="460"> | <img src="docs/images/settings-teammates-ar.png" width="460"> |

<details>
<summary><b>صور أكثر</b></summary>

| | |
|:---:|:---:|
| مراحل النافذة: بسمع، بعالج، الترجمة<br><img src="docs/images/overlay-states.png" width="440"> | مربع الكتابة السريع (F8)<br><img src="docs/images/quicktext-en.png" width="400"> |
| الفحص الشامل<br><img src="docs/images/selftest-en.png" width="400"> | دفتر عباراتي<br><img src="docs/images/phrasebook-en.png" width="440"> |
| الإعدادات: عام<br><img src="docs/images/settings-general-ar.png" width="440"> | |

</details>

<a id="ar-how"></a>

### ⚙️ كيف بيشتغل؟

```mermaid
flowchart LR
    K["اضغط F9"] --> M["المايك يسجّل<br/>(بالذاكرة بس)"]
    M --> S{"الكلام ← نص"}
    S -->|"Whisper على جهازك"| W["صوت عربي ←<br/>نص إنجليزي"]
    S -->|"Azure Speech"| AS["نص عربي<br/>(حسب لهجتك)"]
    AS --> T{"النص ← ترجمة"}
    T -->|"Azure Translator"| AT["إنجليزي أو<br/>14 لغة ثانية"]
    T -->|"موديل بدون نت"| OM["إنجليزي"]
    W --> O["النافذة فوق اللعبة"]
    AT --> O
    OM --> O
```

بتختار الخطوتين **كل وحدة لحال** من لوحة التحكم:

| الخطوة | على جهازك (مجاني وخاص) | Azure (سحابي، الأدق للهجات) |
|---|---|---|
| **1. الكلام ← نص** | Whisper من `tiny` لـ `large-v3`، على كرت الشاشة (CUDA) أو المعالج | Azure Speech مع 17 لهجة عربية (ar-SA, ar-JO, ar-EG, …) |
| **2. النص ← ترجمة** | Whisper بيترجم مباشرة للإنجليزي | Azure Translator: إنجليزي أو 14 لغة ثانية |

<a id="ar-install"></a>

### 📦 التثبيت

#### الطريقة الأولى: ملف التثبيت (الأسهل)

1. نزّل **`GameTalk-Setup-x.y.z.exe`** من
   **[صفحة الإصدارات (Releases)](https://github.com/Cavebest/GameTalk/releases/latest)**.
2. شغّله واختار **العربية** أو الإنجليزية. بيتثبّت في `Program Files`، وإذا ما عندك صلاحيات
   مدير اختار *"التثبيت لي فقط"*.
3. اختياري: اختصار على سطح المكتب، وتشغيل تلقائي مع ويندوز.

ما بتحتاج Python. دعم كروت NVIDIA موجود جوّا، وإذا ما عندك كرت NVIDIA بيشتغل على المعالج.
لإزالة البرنامج: **إعدادات ويندوز ← التطبيقات**. إعداداتك في `%APPDATA%\GameTalk` بتضل محفوظة.

> ممكن يطلع لك تحذير SmartScreen إنه *ناشر غير معروف*، لأن البرنامج مش موقّع رقمياً. اضغط
> **More info ← Run anyway**.

#### الطريقة الثانية: من الكود

بتحتاج ويندوز 10/11 و [Python 3.10+](https://www.python.org/downloads/).

```bash
git clone https://github.com/Cavebest/GameTalk.git
```

بعدين اضغط دبل كليك على **`GameTalk.bat`**. أول مرة بيجهّز كل شي لحاله (وبيضيف دعم كرت
NVIDIA إذا لقاه)، وبعدها بيفتح لوحة التحكم.

<a id="ar-first-run"></a>

### 🚀 أول تشغيل: 5 دقائق

1. **افتح لوحة التحكم**: من اختصار *GameTalk*، أو `GameTalk.exe`، أو `GameTalk.bat`.
2. **اختار المحركات** (الخطوة 1 والخطوة 2). الافتراضي Whisper على جهازك.
3. **الإعدادات ← المايكروفون**: اختار مايك السماعة الحقيقي وجرّب **تجربة**.
4. اضغط **▶ تشغيل البرنامج**، وبيصير أيقونة جنب الساعة.
   - أول مرة بينزّل موديل Whisper مرة وحدة بس (`small` حوالي 480 ميغا). بعدها بيشتغل بدون نت.
5. باللعبة: **اضغط F9 مع الاستمرار، احكِ عربي، واترك الزر**.
6. في مشكلة؟ شغّل **🩺 الفحص الشامل**. بيفحص كل شي وبيحكيلك شو تصلّح.

> 💡 خلّي اللعبة على **Borderless** أو **Windowed**. وضع ملء الشاشة *الحصري* (Exclusive
> Fullscreen) بيخبّي أي نافذة فوق اللعبة، والبرنامج بينبّهك مرة وحدة إذا لاحظه.

<a id="ar-usage"></a>

### 🕹️ الاستعمال اليومي

| شو بدك تعمل | الزر الافتراضي |
|---|---|
| تحكي (ضغط مستمر) | **اضغط F9 مع الاستمرار**، احكِ، واترك |
| وضع الضغطة | اضغط مرة للبدء ومرة للإيقاف |
| المايك المفتوح | بدون زر: البرنامج بيعرف لحاله متى بلّشت ومتى خلّصت، والزر بيكتم/بيفتح |
| إعادة عرض آخر ترجمة | **F10** |
| مربع الكتابة السريع | **F8** |
| الجمل الجاهزة | أي زر بتختاره، مثلاً **Numpad1** ← *"Enemy spotted!"* |
| يد التحكم | زر Xbox/XInput، مثلاً **RB** |
| قائمة الأيقونة | تفعيل/إيقاف، ملف التعريف، آخر الترجمات، الإعدادات، الفحص، المساعدة، خروج |

- **كمّل حكي**: بتقدر تبلّش الجملة الجاية والأولى لسا عم تترجم. النقطة الحمرا الصغيرة معناها
  *"لسا عم تسجّل"*.
- إذا ضغطت الزر بالغلط ضغطة قصيرة، بيطلع لك بس *"اضغط F9 مع الاستمرار وإنت عم تحكي"*.
- الأزرار المدعومة: F1–F24، Insert، Home، End، PageUp/Down، Pause، ScrollLock، أزرار الـ
  Numpad، Mouse4 و Mouse5. الزر بيوصل للعبة كمان، فاختار زر ما بتستعمله اللعبة.

<a id="ar-engines"></a>

### 🧠 محركات التعرّف والترجمة

| الموديل | الحجم | ملاحظات |
|---|---|---|
| `tiny` / `base` | 75–145 ميغا | سريع جداً، أضعف مع اللهجات |
| **`small`** (الافتراضي) | ~480 ميغا | توازن ممتاز، أقل من ثانية على كرت الشاشة |
| `medium` | ~1.5 غيغا | إنجليزي أطبع بكثير للهجات الخليجية والشامية والمصرية |
| `large-v3` | ~3 غيغا | الأدق محلياً (بياخذ حوالي 3 غيغا من ذاكرة الكرت) |

**الترجمة بدون نت للنصوص**: موديلات OPUS-MT صغيرة (عربي ⇄ إنجليزي)، وهي اللي بتشغّل مربع
الكتابة السريع وترجمة كلام الفريق بدون Azure.

**تصحيح اللهجة**: قبل ترجمة النص، البرنامج بيحوّل كلمات اللهجة للفصحى (خليكم ← ابقوا، هلق ←
الآن، …)، وهاد بيخلّي الترجمة أدق بكثير. في قائمة جاهزة، وبتقدر تعدّلها لكل لعبة.

<a id="ar-azure"></a>

### ☁️ Azure (اختياري)

استعمل Azure إذا بدك أعلى دقة **للهجتك**. الخطة المجانية **F0** بتكفي للفويس شات: 5 ساعات
كلام و2 مليون حرف ترجمة بالشهر. البرنامج بيعدّ استهلاكك وبينبّهك عند 80% و100%.

1. ادخل على [portal.azure.com](https://portal.azure.com/) ← **Create a resource** ← **Speech** ←
   *Keys and Endpoint*، وانسخ **Key 1** و **Location/Region**.
2. **Create a resource** ← **Translator**، وانسخ **Key** و **Region** (`global` إذا كان عالمي).
3. من لوحة التحكم اضغط **🔑 مفاتيح Azure**، الصق المفاتيح، اضغط **اختبار الاتصال** وبعدين
   **حفظ**.

ممكن كمان تستعمل مورد *Azure AI services* واحد لكل شي: حط نفس المفتاح والمنطقة بالمكانين.
المفاتيح **مشفّرة بحساب ويندوز تبعك (DPAPI)**، وما بتنكتب بالسجلات وما بتطلع مع التصدير.

| اختيارك بلوحة التحكم | شو بيروح لـ Azure |
|---|---|
| Whisper + Whisper | ولا شي |
| Whisper + Azure Translator | **النص** بس |
| Azure Speech + Azure Translator | **صوتك** وقت الضغط (بعد قص الصمت) والنص |

<a id="ar-features"></a>

### 🧩 كل الميزات

كل ميزة بتقدر تشغّلها أو توقفها من **الإعدادات ← تشغيل وإيقاف الميزات**. الميزة الموقّفة ما
بتستهلك معالج ولا ذاكرة ولا إنترنت، وكل ميزة إلها زر **؟** بشرح كامل بالعربي والإنجليزي.

| الميزة | شو بتعمل | افتراضياً |
|---|---|:---:|
| 🔁 زر الإعادة | **F10** بيعرض آخر ترجمة مرة ثانية | شغّالة |
| 🕘 سجل الترجمات | آخر ترجماتك بقائمة الأيقونة (بالذاكرة بس) | شغّالة |
| 💬 الجمل الجاهزة | جمل جاهزة على أزرار، بتظهر فوراً بدون كلام | موقّفة |
| 💡 اقتراح جمل جاهزة | إذا حكيت نفس الجملة 3 مرات، البرنامج بيقترح تحطها على زر | شغّالة |
| ✏️ قواعد التصحيح | تصحيحاتك إنت، مثلاً *"Zafira" ← "ammo"* | شغّالة |
| 🇸🇦 تصحيح اللهجة العربية | بيحوّل اللهجة لفصحى قبل الترجمة | شغّالة |
| 🔤 مساعد النطق | بيكتب الإنجليزي بحروف عربية: *"Wait for me"* ← «وايت فور مي» | موقّفة |
| 🎮 يد التحكم | زر بيد التحكم للتحدث، وزر للإعادة (اختياري) | موقّفة |
| 👥 ترجمة كلام الفريق | بيسمع صوت الجهاز وبيعرض كلام الفريق بالعربي. التعرّف بـ Whisper أو Azure، والترجمة بالموديل المحلي أو Azure | موقّفة |
| ⌨️ مربع الكتابة السريع | **F8**: اكتب عربي واضغط Enter، بيطلع لك إنجليزي تنسخه للشات | موقّفة |
| 🎙️ المايك المفتوح | بدون زر، البرنامج بيعرف لحاله بداية ونهاية كل جملة | موقّفة |
| 📘 وضع التعلّم | دفتر عباراتك وبطاقات تدريب. هاي الميزة الوحيدة اللي بتحفظ شو حكيت، وعلى جهازك بس | موقّفة |
| 📋 النسخ للحافظة | كل ترجمة بتنحط بالحافظة لتلصقها إنت | موقّفة |
| 🔔 أصوات التنبيه | صوت خفيف لما يبلّش ويخلص التسجيل (والصوت قابل للتعديل) | موقّفة |
| 📊 عدّاد استهلاك Azure | بيحسب استهلاكك من الخطة المجانية هالشهر | شغّالة |
| 🗣️ كلمات الألعاب لـ Azure | بيبعث كلمات الألعاب لـ Azure Speech ليفهم *Medic* و *Flank* وغيرها | شغّالة |
| 🖥️ تنبيه ملء الشاشة | بينبّهك مرة وحدة إذا اللعبة على ملء الشاشة الحصري | شغّالة |
| 🧷 الحماية من الزر العالق | بيوقف التسجيل حتى لو ويندوز ما وصّل ترك الزر | شغّالة |
| ✂️ قص الصمت | بيبعث لـ Azure الجزء اللي فيه كلام بس: بيانات أقل، أسرع، وأرخص | شغّالة |
| 🔔 إشعارات الأيقونة | ملاحظات قصيرة من أيقونة البرنامج | شغّالة |

**أدوات**
- **🩺 الفحص الشامل** بيفحص الموديل وكرت الشاشة والمايك والأزرار والنافذة وAzure والموديلات
  المنزّلة ويد التحكم والمساحة، وبيقترح الحل. التقرير ما فيه كلامك ولا مفاتيحك.
- **تصدير/استيراد ملف التعريف**: شارك إعدادات لعبة (الجمل، التصحيحات، شكل النافذة…) كملف.
  المفاتيح ما بتنضاف أبداً.

<a id="ar-settings"></a>

### 🛠️ صفحات الإعدادات

| الصفحة | شو فيها |
|---|---|
| عام | لغة الواجهة (عربي/إنجليزي/تلقائي)، التفعيل، الإشعارات، التشغيل مع ويندوز، الأصوات، الحافظة |
| تشغيل وإيقاف الميزات | كل مفاتيح الميزات مع الشرح |
| المايكروفون | اختيار المايك، التحديث بعد التوصيل، مؤشر الصوت، تجربة 3 ثواني |
| التعرّف على الكلام | موديل Whisper، كرت الشاشة/المعالج/تلقائي، لغة الكلام، لهجة Azure، عرض النص الأصلي |
| الترجمة | المحرك، اللغة الهدف، وضع الألعاب (جمل قصيرة وطبيعية)، كلمات الألعاب |
| مفاتيح Azure | مفتاح ومنطقة Speech، ومفتاح ومنطقة Translator، اختبار الاتصال، الاستهلاك |
| الأزرار | زر التحدث (أو التقاط زر)، ضغط مستمر/ضغطة/مايك مفتوح، زر الإعادة، زر الكتابة السريعة |
| النافذة فوق اللعبة | المكان، الإزاحة، الشاشة، الخط، الحجم، العرض، الألوان، الشفافية، الزوايا، المدة، الحركة، المعاينة، السحب |
| الجمل الجاهزة | جدول زر ← جملة، مع الاقتراحات |
| قواعد التصحيح | تصحيحاتك وقائمة اللهجة العربية |
| مربع الكتابة السريع | الزر، ومين يترجم (تلقائي/بدون نت/Azure) |
| وضع التعلّم | تشغيل دفتر العبارات وفتحه |
| يد التحكم | زر التحدث وزر الإعادة |
| ترجمة كلام الفريق | جهاز الصوت، التعرّف، الترجمة، اللغة، الحساسية، المكان، الخط، المدة |
| الألعاب | أسماء ملفات الألعاب (`.exe`) اللي بتبدّل ملف التعريف تلقائياً |

<a id="ar-profiles"></a>

### 🎯 ملف تعريف لكل لعبة

كل ملف تعريف إله إعداداته الخاصة: الزر، الوضع، المايك، الموديل، المحركات، مكان النافذة وحجمها
وشفافيتها، الخط، المدة، كلمات الألعاب، الجمل الجاهزة والتصحيحات. ضيف اسم ملف اللعبة (من مدير
المهام ← التفاصيل، مثلاً `cs2.exe`)، وملف التعريف بيتفعّل لحاله لما تفتح اللعبة.

<a id="ar-privacy"></a>

### 🔒 الخصوصية

- **الوضع المحلي ما بيبعث ولا شي.** التعرّف والترجمة على جهازك.
- **المايك بيفتح بس وإنت ضاغط الزر.** الصوت بالذاكرة وبينحذف بعد كل جملة، وما بينحفظ شي على
  الهارد.
- **السجلات** (`%APPDATA%\GameTalk\logs`) فيها أوقات وأنواع أخطاء بس، وأبداً مش كلامك.
- **مفاتيح Azure** مشفّرة بـ DPAPI، وما بتنكتب كنص عادي.
- الاتصال الوحيد غير هيك هو تنزيل الموديل أول مرة من Hugging Face، والتتبّع مقفول.
- وضع التعلّم **اختياري**، وهو المكان الوحيد اللي بتنحفظ فيه جمل (`phrasebook.json` على جهازك).

<a id="ar-performance"></a>

### ⚡ الأداء

- **المعالج وقت الراحة: 0%.** ما في أي فحص متكرر أو مؤقتات، والمايك مسكّر.
- الزر بيشتغل عن طريق **Raw Input** مش hooks، يعني برّا مسار إدخال اللعبة، فما بيضيف **أي
  تأخير** على الماوس أو الكيبورد.
- الترجمة بتظهر خلال **0.1 لـ 0.3 ثانية** تقريباً بعد ما تترك الزر (كرت NVIDIA، موديل
  `medium`).

| الوضع | الرام | ملاحظة |
|---|---|---|
| محلي، كرت شاشة | ~800 ميغا (+ ~1 غيغا من ذاكرة الكرت) | الموديل بيضل محمّل للرد الفوري |
| محلي، معالج | ~430 ميغا | |
| Azure | ~90 ميغا | ما في موديل محلي |
| + ترجمة الفريق / النطق / يد التحكم | +~120 ميغا | موديل ترجمة إنجليزي ← عربي وقاموس |

<a id="ar-troubleshooting"></a>

### 🧯 حل المشاكل

| المشكلة | الحل |
|---|---|
| ما بشوف النافذة باللعبة | خلّي اللعبة **Borderless** أو **Windowed** |
| الزر ما بيشتغل جوّا اللعبة | إذا اللعبة شغّالة **كمسؤول (Administrator)**، شغّل البرنامج كمسؤول كمان |
| بيطلع "ما فهمت" | جرّب المايك من **الإعدادات ← المايكروفون ← تجربة**، واضغط الزر شوي أطول |
| الترجمة مش دقيقة | جرّب `medium` أو `large-v3`، أو Azure Speech مع لهجتك، وضيف قواعد تصحيح |
| أول ترجمة بطيئة | أول مرة على كرت جديد بيجهّز حاله مرة وحدة (~20 ثانية)، وبعدها فوري |
| فصلت المايك أو غيّرته | **الإعدادات ← المايكروفون ← تحديث**، والبرنامج كمان بيعيد المحاولة لحاله |
| أي شي ثاني | شغّل **🩺 الفحص الشامل** وبعدين **نسخ التقرير** (آمن للمشاركة) |

> بعض أنظمة مكافحة الغش القوية ما بتحب أي نافذة فوق اللعبة. GameTalk ما بيدخل على اللعبة أبداً،
> بس تأكد من قوانين لعبتك.

<a id="ar-license"></a>

### 👤 المطوّر والترخيص

من تطوير **[Shkour Bashtawi](https://github.com/ShkourBashtawi)**.
مرخّص بموجب **[رخصة MIT](LICENSE)**. المكوّنات الخارجية (faster-whisper، CTranslate2،
Qt/PySide6، موديلات Whisper و OPUS-MT، وخدمات Microsoft Azure) إلها تراخيصها وشروطها الخاصة.

<div align="left"><a href="#arabic">⬆ للأعلى</a></div>

</div>
