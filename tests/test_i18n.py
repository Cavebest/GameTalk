import ast
import pathlib
import re

import pytest

from gametalk import config, google, help, i18n, options
from gametalk.hub import backend
from gametalk.i18n_ar import AR

PKG = pathlib.Path(__file__).resolve().parents[1] / "gametalk"


def _tr_literals() -> set[str]:
    found = set()
    for f in [*PKG.glob("*.py"), *PKG.glob("hub/*.py")]:
        tree = ast.parse(f.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "tr" and node.args:
                arg = node.args[0]
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    found.add(arg.value)
    return found


QML_TEXT = re.compile(r'hub\.tf?\(\s*"((?:[^"\\]|\\.)*)"')


def qml_strings() -> set[str]:
    """Every hub.t("…") / hub.tf("…", …) literal in the Qt Quick interface."""
    found = set()
    for f in (PKG / "hub" / "qml").glob("*.qml"):
        found.update(QML_TEXT.findall(f.read_text(encoding="utf-8")))
    return found


def _labels() -> set[str]:
    out = set()
    for d in (
        config.SPEECH_PROVIDERS,
        config.TRANSLATION_PROVIDERS,
        config.TARGET_LANGUAGES,
        config.SOURCE_LANGUAGES,
        config.AZURE_LOCALES,
        config.TEAM_RECOGNIZERS,
        config.TEAM_TRANSLATORS,
        config.QUICK_TEXT_TRANSLATORS,
        google.MODELS,
        backend.MODEL_NOTES,
        backend.HOTKEY_MODE_LABELS,
        options.DEVICE_LABELS,
        options.MONITOR_LABELS,
        options.POSITION_LABELS,
    ):
        out.update(d.values())
    out.update(label for _, label, _, _ in options.FEATURE_SWITCHES)
    out.update(desc for _, _, _, desc in options.FEATURE_SWITCHES)
    out.discard("العربية")  # already Arabic
    return out


def _error_messages() -> set[str]:
    """User-facing errors raised/emitted in modules (translated where they're displayed)."""
    out = set()
    pattern = re.compile(
        r'(?:Error|failed\.emit)\(\s*(?:job\.tag,\s*|"team",\s*|cfg,\s*)?"([^"{]+)"\s*\)'
    )
    for f in PKG.glob("*.py"):
        out.update(pattern.findall(f.read_text(encoding="utf-8")))
    return {m for m in out if m.endswith((".", "…"))}


@pytest.mark.parametrize("group", ["tr() calls", "labels", "errors", "hub"])
def test_every_ui_string_has_an_arabic_translation(group):
    strings = {
        "tr() calls": _tr_literals,
        "labels": _labels,
        "errors": _error_messages,
        "hub": qml_strings,
    }[group]()
    missing = sorted(s for s in strings if s not in AR)
    assert not missing, f"{len(missing)} strings without Arabic: {missing[:10]}"


def test_translations_keep_placeholders():
    for en, ar in AR.items():
        assert set(re.findall(r"{(\w+)}", en)) == set(re.findall(r"{(\w+)}", ar)), en


def test_tr_switches_language_and_falls_back():
    try:
        i18n.set_language("ar")
        assert i18n.is_rtl()
        assert (
            i18n.tr("Hold {key} while you speak.", key="F9")
            == i18n.RLM + "اضغط F9 مع الاستمرار أثناء الكلام."
        )
        assert i18n.tr("some brand-new string") == "some brand-new string"
        i18n.set_language("en")
        assert i18n.tr("Save") == "Save" and not i18n.is_rtl()
        assert i18n.set_language("auto") in ("ar", "en")
    finally:
        i18n.set_language("en")


def test_help_has_both_languages_for_every_topic():
    for key, (t_en, t_ar, s_en, s_ar, b_en, b_ar) in help.TOPICS.items():
        assert all((t_en, t_ar, s_en, s_ar, b_en, b_ar)), key
        assert any("؀" <= ch <= "ۿ" for ch in t_ar + s_ar + b_ar), key
    # every "?" in the main window opens an existing help topic
    topics = set()
    for f in (PKG / "hub" / "qml").glob("*.qml"):
        text = f.read_text(encoding="utf-8")
        topics.update(re.findall(r'(?:helpTopic|topic): "(\w+)"', text))
        topics.update(re.findall(r'openHelp\("(\w+)"\)', text))
    topics.update(t for _, _, t, _ in options.FEATURE_SWITCHES)
    assert topics and not topics - set(help.TOPICS), topics - set(help.TOPICS)
