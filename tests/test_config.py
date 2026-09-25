import json

from gametalk.config import (
    NEVER_HIDE,
    ConfigStore,
    Profile,
    Settings,
    settings_from_dict,
    validate,
)


def test_defaults():
    s = validate(Settings())
    assert s.profile.hotkey == "F9"
    assert s.profile.hotkey_mode == "push"
    assert s.profile.model == "small"
    assert s.profile.display_seconds == 4
    assert "Medic" in s.profile.vocabulary


def test_round_trip(tmp_path):
    store = ConfigStore(tmp_path / "config.json")
    s = validate(Settings())
    s.profile.hotkey = "Mouse5"
    s.profile.display_seconds = NEVER_HIDE
    s.profile.background_opacity = 0.5
    s.overlay.corner_radius = 4
    s.profiles.append(Profile(name="CS2", exe_names=["cs2.exe"], model="medium"))
    assert store.save(s)
    loaded = store.load()
    assert loaded == s
    assert loaded.find_profile("CS2").model == "medium"


def test_missing_file_gives_defaults(tmp_path):
    assert ConfigStore(tmp_path / "nope.json").load() == validate(Settings())


def test_corrupt_file_is_backed_up(tmp_path):
    path = tmp_path / "config.json"
    path.write_text("{not json", encoding="utf-8")
    s = ConfigStore(path).load()
    assert s == validate(Settings())
    assert (tmp_path / "config.json.bak").exists()


def test_wrong_types_and_unknown_keys_fall_back():
    data = {
        "enabled": "yes",
        "bogus": 1,
        "overlay": {"max_width": "wide", "background_opacity": 3},
        "profiles": [{"name": "A", "font_size": 999, "hotkey_mode": "weird", "vocabulary": [1]}],
        "active_profile": "missing",
    }
    s = settings_from_dict(data)
    assert s.enabled is True
    p = s.profile
    assert p.max_width == 640  # "wide" rejected
    assert p.background_opacity == 1.0  # 3 migrated from the old global value, then clamped
    assert p.name == "A" and s.active_profile == "A"
    assert p.font_size == 48
    assert p.hotkey_mode == "push"
    assert "Medic" in p.vocabulary


def test_duration_clamped_but_never_hide_kept():
    s = settings_from_dict({"profiles": [{"display_seconds": 99}, {"name": "B"}]})
    assert s.profiles[0].display_seconds == 15
    s = settings_from_dict({"profiles": [{"display_seconds": NEVER_HIDE}]})
    assert s.profile.display_seconds == NEVER_HIDE


def test_duplicate_profiles_dropped_and_exe_normalised():
    s = settings_from_dict(
        {"profiles": [{"name": "X", "exe_names": [" CS2.EXE ", ""]}, {"name": "X"}]}
    )
    assert len(s.profiles) == 1
    assert s.profile.exe_names == ["cs2.exe"]


def test_saved_json_is_readable(tmp_path):
    store = ConfigStore(tmp_path / "c.json")
    store.save(validate(Settings()))
    data = json.loads((tmp_path / "c.json").read_text(encoding="utf-8"))
    assert data["profiles"][0]["hotkey"] == "F9"


def test_old_global_overlay_values_migrate_into_every_profile():
    old = {
        "overlay": {"max_width": 900, "background_opacity": 0.4, "text_opacity": 0.8},
        "profiles": [{"name": "Default"}, {"name": "CS2", "max_width": 500}],
    }
    s = settings_from_dict(old)
    d, cs2 = s.profiles
    assert (d.max_width, d.background_opacity, d.text_opacity) == (900, 0.4, 0.8)
    assert cs2.max_width == 500  # a profile's own value wins
    assert cs2.background_opacity == 0.4


def test_profiles_do_not_share_overlay_settings():
    s = validate(Settings())
    s.profiles.append(Profile(name="Game"))
    s.find_profile("Game").max_width = 400
    s.find_profile("Game").vocabulary.append("Rotate")
    assert s.find_profile("Default").max_width == 640
    assert "Rotate" not in s.find_profile("Default").vocabulary


def test_vocabulary_is_cleaned_not_rewritten():
    from gametalk.config import MAX_VOCABULARY, clean_vocabulary

    assert clean_vocabulary(["  Medic ", "medic", "MEDIC", "Fall   back", "", "x" * 41]) == [
        "Medic",
        "Fall back",
    ]
    assert clean_vocabulary(["خط الدفاع", "B-site"]) == ["خط الدفاع", "B-site"]  # Arabic intact
    assert len(clean_vocabulary([f"w{i}" for i in range(200)])) == MAX_VOCABULARY
    s = settings_from_dict({"profiles": [{"vocabulary_enabled": False}]})
    assert s.profile.vocabulary_enabled is False
