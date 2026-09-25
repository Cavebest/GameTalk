import json
import struct

import httpx
import numpy as np
import pytest

from gametalk.azure import (
    AzureClient,
    AzureCredentials,
    AzureError,
    check_connection,
    normalize_region,
    wav_bytes,
)

CREDS = AzureCredentials("sk", "West Europe", "tk", "uaenorth")


def client_with(handler):
    return AzureClient(CREDS, transport=httpx.MockTransport(handler))


def test_wav_header():
    audio = np.array([0.0, 0.5, -1.0, 2.0], np.float32)
    data = wav_bytes(audio)
    assert data[:4] == b"RIFF" and data[8:16] == b"WAVEfmt "
    channels, rate = struct.unpack("<HI", data[22:28])
    assert (channels, rate) == (1, 16000)
    samples = np.frombuffer(data[44:], "<i2")
    assert samples.tolist() == [0, 16383, -32767, 32767]  # clipped


def test_region_normalised():
    assert normalize_region(" West Europe ") == "westeurope"


def test_recognize_success_request_shape():
    seen = {}

    def handler(request: httpx.Request):
        seen["url"] = request.url
        seen["headers"] = request.headers
        seen["body"] = request.content
        return httpx.Response(
            200, json={"RecognitionStatus": "Success", "DisplayText": "خليكم وراي"}
        )

    text = client_with(handler).recognize(np.zeros(1600, np.float32), "ar-SY")
    assert text == "خليكم وراي"
    assert seen["url"].host == "westeurope.stt.speech.microsoft.com"
    assert seen["url"].params["language"] == "ar-SY"
    assert seen["headers"]["Ocp-Apim-Subscription-Key"] == "sk"
    assert seen["headers"]["Content-Type"].startswith("audio/wav")
    assert seen["body"][:4] == b"RIFF"


@pytest.mark.parametrize("status", ["NoMatch", "InitialSilenceTimeout", "BabbleTimeout"])
def test_recognize_no_speech_returns_empty(status):
    c = client_with(lambda r: httpx.Response(200, json={"RecognitionStatus": status}))
    assert c.recognize(np.zeros(1600, np.float32), "ar-SA") == ""


@pytest.mark.parametrize(
    "code, fragment", [(401, "invalid key"), (403, "invalid key"), (429, "quota"), (500, "500")]
)
def test_http_errors_are_friendly(code, fragment):
    c = client_with(lambda r: httpx.Response(code, json={"error": {"message": "x"}}))
    with pytest.raises(AzureError, match=fragment):
        c.recognize(np.zeros(1600, np.float32), "ar-SA")


def test_network_errors_are_friendly():
    def timeout(request):
        raise httpx.ReadTimeout("slow", request=request)

    def offline(request):
        raise httpx.ConnectError("dns", request=request)

    with pytest.raises(AzureError, match="timed out"):
        client_with(timeout).translate("x", "ar", "en")
    with pytest.raises(AzureError, match="Can't reach"):
        client_with(offline).translate("x", "ar", "en")


def test_translate_request_shape():
    seen = {}

    def handler(request: httpx.Request):
        seen["url"] = request.url
        seen["headers"] = request.headers
        seen["json"] = json.loads(request.content)
        return httpx.Response(
            200, json=[{"translations": [{"text": "Stay behind me", "to": "en"}]}]
        )

    out = client_with(handler).translate("خليكم وراي", "ar", "en")
    assert out == "Stay behind me"
    assert seen["url"].host == "api.cognitive.microsofttranslator.com"
    assert seen["url"].params["from"] == "ar" and seen["url"].params["to"] == "en"
    assert seen["headers"]["Ocp-Apim-Subscription-Region"] == "uaenorth"
    assert seen["json"] == [{"Text": "خليكم وراي"}]


def test_translate_global_resource_omits_region_and_autodetects():
    seen = {}

    def handler(request):
        seen["headers"], seen["params"] = request.headers, request.url.params
        return httpx.Response(200, json=[{"translations": [{"text": "Hi"}]}])

    c = AzureClient(
        AzureCredentials(translator_key="tk", translator_region="global"),
        transport=httpx.MockTransport(handler),
    )
    c.translate("مرحبا", None, "en")
    assert "Ocp-Apim-Subscription-Region" not in seen["headers"]
    assert "from" not in seen["params"]


def test_missing_credentials():
    c = AzureClient(AzureCredentials())
    with pytest.raises(AzureError, match="Speech key"):
        c.recognize(np.zeros(10, np.float32), "ar-SA")
    with pytest.raises(AzureError, match="Translator key"):
        c.translate("x", "ar", "en")


def test_credentials_repr_hides_keys():
    assert "sk" not in repr(CREDS) and "tk" not in repr(CREDS)


def test_check_connection_reports_each_service():
    def handler(request):
        if "stt.speech" in request.url.host:
            return httpx.Response(401)
        return httpx.Response(200, json=[{"translations": [{"text": "Hello"}]}])

    results = check_connection(CREDS, transport=httpx.MockTransport(handler))
    assert results[0] == (False, "Azure Speech: invalid key or wrong region.")
    assert results[1][0] is True and "Hello" in results[1][1]


def test_dropped_connection_is_retried_once():
    calls = []

    def handler(request):
        calls.append(1)
        if len(calls) == 1:
            raise httpx.RemoteProtocolError("server closed keep-alive", request=request)
        return httpx.Response(200, json=[{"translations": [{"text": "Hello"}]}])

    assert client_with(handler).translate("مرحبا", "ar", "en") == "Hello"
    assert len(calls) == 2


def test_timeouts_and_repeated_failures_are_not_retried_forever():
    calls = []

    def timeout(request):
        calls.append(1)
        raise httpx.ReadTimeout("slow", request=request)

    with pytest.raises(AzureError, match="timed out"):
        client_with(timeout).translate("x", "ar", "en")
    assert len(calls) == 1  # user is already waiting: no retry

    calls.clear()

    def always_drop(request):
        calls.append(1)
        raise httpx.ConnectError("offline", request=request)

    with pytest.raises(AzureError, match="Can't reach"):
        client_with(always_drop).translate("x", "ar", "en")
    assert len(calls) == 2
