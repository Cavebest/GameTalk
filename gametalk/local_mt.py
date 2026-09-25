# Copyright (c) 2026 Shkour Bashtawi (github.com/ShkourBashtawi). MIT License.
"""Offline text translation (no internet needed): English -> Arabic for teammate subtitles,
Arabic -> English for the quick text window.

OPUS-MT en-ar (Helsinki-NLP, Apache-2.0) converted for CTranslate2, which GameTalk already
uses for Whisper. It runs on the CPU (int8, ~5 ms per sentence) so the GPU stays free for the
game. Downloaded once (~160 MB) the first time the feature is used.
"""

from __future__ import annotations

import logging
import os

log = logging.getLogger(__name__)

EN_AR = "ooeoeo/opus-mt-en-ar-ct2-float16"
AR_EN = "ooeoeo/opus-mt-ar-en-ct2-float16"
MODEL_REPO = EN_AR


class LocalTranslatorError(Exception):
    """User-presentable failure."""


class LocalTranslator:
    def __init__(self, repo: str = EN_AR):
        self.repo = repo
        self._translator = None
        self._src = None
        self._tgt = None

    @property
    def loaded(self) -> bool:
        return self._translator is not None

    def load(self, on_status=lambda s: None) -> None:
        if self._translator is not None:
            return
        try:
            import ctranslate2
            import sentencepiece as spm
            from huggingface_hub import snapshot_download
        except ImportError as e:
            raise LocalTranslatorError("Offline translator isn't installed.") from e
        try:
            path = snapshot_download(self.repo, local_files_only=True)
        except Exception:
            on_status("Downloading offline translator…")
            try:
                path = snapshot_download(self.repo)
            except Exception as e:
                raise LocalTranslatorError(
                    "Offline translator couldn't be downloaded. Connect to the internet once."
                ) from e
        try:
            self._src = spm.SentencePieceProcessor(model_file=os.path.join(path, "source.spm"))
            self._tgt = spm.SentencePieceProcessor(model_file=os.path.join(path, "target.spm"))
            self._translator = ctranslate2.Translator(
                path, device="cpu", compute_type="int8", inter_threads=1, intra_threads=2
            )
        except Exception as e:
            self._translator = None
            raise LocalTranslatorError("Offline translator couldn't be loaded.") from e
        log.info("Offline translator loaded (%s)", "ar->en" if self.repo == AR_EN else "en->ar")

    def unload(self) -> None:
        self._translator = self._src = self._tgt = None

    def translate(self, text: str) -> str:
        self.load()
        # Marian models need the explicit end-of-sentence token, or they repeat forever.
        tokens = self._src.encode(text, out_type=str)[:400] + ["</s>"]
        result = self._translator.translate_batch(
            [tokens], beam_size=2, max_decoding_length=160, repetition_penalty=1.1
        )
        return self._tgt.decode(result[0].hypotheses[0]).strip()
