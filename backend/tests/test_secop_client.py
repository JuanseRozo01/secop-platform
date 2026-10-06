import httpx
import pytest

from app.modules.secop.client import SecopClient
from app.modules.secop.exceptions import SecopBadResponseError, SecopUnavailableError

pytestmark = pytest.mark.anyio


def make_client(handler, **kw):
    sleeps: list[float] = []

    async def fake_sleep(s: float) -> None:
        sleeps.append(s)

    client = SecopClient(
        "https://example.test/resource/",
        transport=httpx.MockTransport(handler),
        sleep=fake_sleep,
        backoff=0.5,
        **kw,
    )
    return client, sleeps


async def test_success_builds_url_params_and_token_header():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = request.url
        seen["token"] = request.headers.get("X-App-Token")
        return httpx.Response(200, json=[{"id_del_proceso": "A"}, "basura"])

    client, _ = make_client(handler, app_token="tok123")
    rows = await client.query("p6dx-8zbt", {"$limit": "5", "$q": "aseo"})
    assert rows == [{"id_del_proceso": "A"}]
    assert seen["url"].path == "/resource/p6dx-8zbt.json"
    assert seen["url"].params["$limit"] == "5" and seen["url"].params["$q"] == "aseo"
    assert seen["token"] == "tok123"
    await client.aclose()


async def test_retries_on_503_then_succeeds_with_exponential_backoff():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        return httpx.Response(503) if calls["n"] < 3 else httpx.Response(200, json=[])

    client, sleeps = make_client(handler, max_retries=3)
    assert await client.query("x", {}) == []
    assert calls["n"] == 3
    assert sleeps == [0.5, 1.0]


async def test_429_honors_retry_after():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(429, headers={"Retry-After": "7"})
        return httpx.Response(200, json=[])

    client, sleeps = make_client(handler)
    await client.query("x", {})
    assert sleeps == [7.0]


async def test_gives_up_after_max_retries_with_unavailable():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        return httpx.Response(500)

    client, sleeps = make_client(handler, max_retries=2)
    with pytest.raises(SecopUnavailableError) as exc:
        await client.query("x", {})
    assert exc.value.status_code == 503
    assert calls["n"] == 3 and len(sleeps) == 2


async def test_timeout_is_retried_and_then_unavailable():
    def handler(request):
        raise httpx.ConnectTimeout("lento", request=request)

    client, _ = make_client(handler, max_retries=1)
    with pytest.raises(SecopUnavailableError):
        await client.query("x", {})


async def test_400_is_not_retried_and_maps_to_bad_gateway():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        return httpx.Response(400, json={"message": "query.soql.no-such-column"})

    client, sleeps = make_client(handler)
    with pytest.raises(SecopBadResponseError) as exc:
        await client.query("x", {})
    assert exc.value.status_code == 502
    assert calls["n"] == 1 and sleeps == []


@pytest.mark.parametrize("body", [b"<html>", b'{"error": true}'])
async def test_invalid_payloads_are_rejected(body):
    client, _ = make_client(lambda r: httpx.Response(200, content=body))
    with pytest.raises(SecopBadResponseError):
        await client.query("x", {})
