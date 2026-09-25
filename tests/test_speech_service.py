import time

import numpy as np

from gametalk.speech import EngineConfig, Job, SpeechService
from gametalk.translate import TranslationRequest


def test_stale_ready_from_a_superseded_load_is_ignored(qapp):
    svc = SpeechService()
    try:
        ready = []
        svc.ready.connect(lambda s, n: ready.append(s))
        svc.config, svc.loading = EngineConfig("medium"), True
        svc._on_ready(EngineConfig("small"), "small on CUDA", "")  # old request finishing
        assert svc.loading and not svc.loaded and ready == []
        svc._on_ready(EngineConfig("medium"), "medium on CUDA", "")
        assert svc.loaded and ready == ["medium on CUDA"]
    finally:
        svc.shutdown()


def test_shutdown_reports_a_busy_worker_instead_of_crashing(qapp, monkeypatch):
    import gametalk.speech as sp

    monkeypatch.setattr(sp, "run_pipeline", lambda *a, **k: time.sleep(1.5))
    svc = SpeechService()
    svc.process(Job(np.zeros(16000, np.float32), TranslationRequest("ar")))
    qapp.processEvents()
    time.sleep(0.2)
    assert svc.shutdown(timeout_ms=200) is False  # caller then exits the process cleanly
    svc._thread.wait(3000)  # let the fake job finish so the test process stays healthy


def test_jobs_queued_after_shutdown_are_skipped(qapp, monkeypatch):
    import gametalk.speech as sp

    ran = []
    monkeypatch.setattr(sp, "run_pipeline", lambda *a, **k: ran.append(1))
    svc = SpeechService()
    svc._worker.cancelled.set()
    svc._worker.process(Job(np.zeros(10, np.float32), TranslationRequest("ar")))
    assert ran == []
    assert svc.shutdown() is True
