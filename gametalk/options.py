# Copyright (c) 2026 Shkour Bashtawi (github.com/ShkourBashtawi). MIT License.
"""Labels and the feature list shared by the main window, the tray and the tests."""

from __future__ import annotations

PREVIEW_TEXT = "Wait for me, I'm coming."
DEVICE_LABELS = {"auto": "Auto (GPU if available)", "cuda": "GPU (NVIDIA CUDA)", "cpu": "CPU"}
MONITOR_LABELS = {"game": "Monitor with the game", "primary": "Primary monitor"}
POSITION_LABELS = {
    "top-left": "Top left",
    "top-center": "Top center",
    "top-right": "Top right",
    "middle-left": "Middle left",
    "center": "Center",
    "middle-right": "Middle right",
    "bottom-left": "Bottom left",
    "bottom-center": "Bottom center",
    "bottom-right": "Bottom right",
}

# Feature switches: key in Features/TeammateSettings -> (label, help topic, explanation)
FEATURE_SWITCHES = [
    (
        "replay_enabled",
        "Replay key (show the last translation again)",
        "replay",
        "Press the replay key (F10) to show your last translation again.",
    ),
    (
        "history_enabled",
        "Translation history (tray menu)",
        "replay",
        "Keeps your recent translations in memory; pick one from the tray menu to show it again.",
    ),
    (
        "quick_phrases_enabled",
        "Quick phrases on keys",
        "phrases",
        "Ready-made sentences on keys, shown instantly without speaking.",
    ),
    (
        "corrections_enabled",
        "Correction rules",
        "corrections",
        "Fixes words that are often translated wrong (your own rules).",
    ),
    (
        "pronunciation_enabled",
        "Pronunciation helper (English in Arabic letters)",
        "pronunciation",
        "Shows how to say the English sentence, written in Arabic letters.",
    ),
    (
        "gamepad_enabled",
        "Game controller button as push-to-talk",
        "gamepad",
        "Hold a controller button (e.g. RB) to talk, like the keyboard hotkey.",
    ),
    (
        "teammates.enabled",
        "Teammate subtitles (translate what you hear)",
        "teammates",
        "Shows what your teammates say, translated, as subtitles.",
    ),
    (
        "fullscreen_warning",
        "Warn when a game is in exclusive fullscreen",
        "overlay",
        "Tells you once when a game hides the overlay, so you can switch to Borderless.",
    ),
    (
        "stuck_key_protection",
        "Stuck-key protection",
        "hotkey",
        "Stops the recording even if Windows misses the moment you let go of the key.",
    ),
    (
        "trim_silence",
        "Trim silence before sending audio to Azure",
        "privacy",
        "Sends only the part of the recording with speech: less data, faster, cheaper.",
    ),
    (
        "azure_phrase_list",
        "Send gaming vocabulary to Azure Speech (phrase list)",
        "azure",
        "Helps Azure Speech recognise game words like Medic or Flank.",
    ),
    (
        "tray_notifications",
        "Tray notifications",
        "general",
        "Small pop-up messages for warnings and tips.",
    ),
    (
        "arabic_corrections_enabled",
        "Arabic dialect corrections before translating",
        "corrections",
        "Turns dialect words into standard Arabic first (خليكم → ابقوا) for better translations.",
    ),
    (
        "sound_cues",
        "Sound cues when recording starts/stops",
        "sounds",
        "A short beep so you know GameTalk heard you, even without looking.",
    ),
    (
        "copy_to_clipboard",
        "Copy translations to the clipboard",
        "general",
        "Paste the English yourself into a game's text chat (Ctrl+V). Nothing is typed for you.",
    ),
    (
        "phrase_suggestions",
        "Suggest quick phrases for sentences you repeat",
        "phrases",
        "Say the same thing often? GameTalk suggests putting it on a key.",
    ),
    (
        "quick_text_enabled",
        "Quick text box (type Arabic, get English)",
        "quicktext",
        "A key opens a small box: type Arabic, press Enter, get English for text chat.",
    ),
    (
        "learning_enabled",
        "Learning mode (save my phrasebook)",
        "learning",
        "Keeps the sentences you use on this PC so you can practise them. Off = nothing saved.",
    ),
    (
        "azure_usage_tracking",
        "Azure usage counter and quota warnings",
        "azure",
        "Counts how much of Azure's free monthly quota you've used and warns at 80% and 100%.",
    ),
]
