"""Resiliência HTTP testada contra um servidor local: 429, 5xx, 404, timeout e rate limit."""

from __future__ import annotations

import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
import requests

from pipeline.http_client import HttpClient, PermanentHTTPError, RateLimiter, TransientHTTPError, redact


class _Handler(BaseHTTPRequestHandler):
    hits: dict[str, int] = {}

    def log_message(self, *args: object) -> None:  # silencia o log do servidor de teste
        pass

    def _send(self, status: int, body: bytes = b"{}", headers: dict[str, str] | None = None) -> None:
        self.send_response(status)
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = self.path.split("?")[0]
        count = self.hits[path] = self.hits.get(path, 0) + 1
        if path == "/ok":
            self._send(200, b'{"ok": true}')
        elif path == "/429-depois-ok":
            if count == 1:
                self._send(429, headers={"Retry-After": "1"})
            else:
                self._send(200, b'{"ok": true}')
        elif path == "/503-duas-vezes":
            self._send(503) if count <= 2 else self._send(200, b'{"ok": true}')
        elif path == "/sempre-500":
            self._send(500)
        elif path == "/404":
            self._send(404, b'{"error": "nao existe"}')
        elif path == "/lento":
            time.sleep(1.5)
            self._send(200)


@pytest.fixture(scope="module")
def server() -> str:
    _Handler.hits = {}
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_port}"
    httpd.shutdown()


def make_client(max_retries: int = 3, timeout: float = 5.0) -> HttpClient:
    session = requests.Session()
    session.trust_env = False  # o servidor de teste é local: ignora proxy do ambiente
    return HttpClient("teste", min_interval_s=0, timeout_s=(2.0, timeout), max_retries=max_retries, backoff_factor=0.05, session=session)


def test_sucesso_simples(server: str) -> None:
    client = make_client()
    assert client.get_text(f"{server}/ok") == '{"ok": true}'
    assert client.stats.requests == 1 and client.stats.retries == 0


def test_429_respeita_retry_after_e_recupera(server: str) -> None:
    client = make_client()
    started = time.monotonic()
    assert client.get_text(f"{server}/429-depois-ok") == '{"ok": true}'
    assert time.monotonic() - started >= 1.0  # esperou o Retry-After: 1
    assert client.stats.retries == 1
    assert _Handler.hits["/429-depois-ok"] == 2


def test_503_transitorio_recupera_com_backoff(server: str) -> None:
    client = make_client()
    assert client.get_text(f"{server}/503-duas-vezes") == '{"ok": true}'
    assert client.stats.retries == 2


def test_500_persistente_esgota_retentativas(server: str) -> None:
    client = make_client(max_retries=2)
    with pytest.raises(TransientHTTPError, match="retentativas esgotadas"):
        client.get_text(f"{server}/sempre-500")
    assert _Handler.hits["/sempre-500"] == 3  # 1 tentativa + 2 retentativas


def test_404_e_erro_permanente_sem_retentativa(server: str) -> None:
    client = make_client()
    with pytest.raises(PermanentHTTPError) as error:
        client.get_text(f"{server}/404")
    assert error.value.status_code == 404
    assert _Handler.hits["/404"] == 1


def test_timeout_vira_erro_transitorio(server: str) -> None:
    client = make_client(max_retries=1, timeout=0.3)
    with pytest.raises(TransientHTTPError):
        client.get_text(f"{server}/lento")


def test_falha_de_conexao_vira_erro_transitorio() -> None:
    client = make_client(max_retries=1)
    with pytest.raises(TransientHTTPError):
        client.get_text("http://127.0.0.1:9/fechada")


def test_rate_limiter_espera_o_intervalo_minimo() -> None:
    now = [100.0]
    sleeps: list[float] = []

    def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)
        now[0] += seconds

    limiter = RateLimiter(2.0, clock=lambda: now[0], sleep=fake_sleep)
    limiter.wait()  # primeira chamada não espera
    now[0] += 0.5
    limiter.wait()  # passou 0,5 s: espera 1,5 s
    now[0] += 5.0
    limiter.wait()  # já passou do intervalo: não espera
    assert sleeps == [pytest.approx(1.5)]
    assert limiter.total_wait_s == pytest.approx(1.5)


def test_redact_remove_credenciais() -> None:
    assert redact("https://x/y?latitude=1&apikey=SEGREDO123&z=2") == "https://x/y?latitude=1&apikey=***&z=2"
    assert "SEGREDO" not in redact("erro em token=SEGREDO")


def test_erro_nao_expoe_chave_na_mensagem(server: str) -> None:
    client = make_client()
    with pytest.raises(PermanentHTTPError) as error:
        client.get_text(f"{server}/404", params={"apikey": "SEGREDO123"})
    assert "SEGREDO123" not in str(error.value)
