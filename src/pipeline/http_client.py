"""Cliente HTTP único do pipeline: controle de taxa, retentativas e erros classificados.

Controle de taxa e retentativa são mecanismos separados:
- ``RateLimiter`` evita exceder a frequência de chamadas (prevenção);
- ``urllib3.util.Retry`` trata as falhas transitórias que ocorrem mesmo assim
  (429/5xx, timeout, queda de conexão), com backoff exponencial, jitter e
  respeito ao cabeçalho ``Retry-After``.
"""

from __future__ import annotations

import logging
import re
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

logger = logging.getLogger(__name__)

RETRY_STATUS: tuple[int, ...] = (429, 500, 502, 503, 504)
_SECRET_PARAM = re.compile(r"(?i)\b(apikey|api_key|token|key|access_token)=([^&\s]+)")


class HttpError(Exception):
    """Erro de requisição HTTP."""


class TransientHTTPError(HttpError):
    """Falha transitória que persistiu após todas as retentativas."""


class PermanentHTTPError(HttpError):
    """Erro que não adianta repetir (4xx diferente de 429)."""

    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.status_code = status_code


def redact(text: str) -> str:
    """Remove valores de credenciais de uma URL ou mensagem antes de registrar em log."""
    return _SECRET_PARAM.sub(lambda match: f"{match.group(1)}=***", text)


class RateLimiter:
    """Garante um intervalo mínimo entre chamadas consecutivas."""

    def __init__(
        self,
        min_interval_s: float,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._min_interval_s = min_interval_s
        self._clock = clock
        self._sleep = sleep
        self._last_call: float | None = None
        self.total_wait_s = 0.0

    def wait(self) -> None:
        now = self._clock()
        if self._last_call is not None:
            remaining = self._min_interval_s - (now - self._last_call)
            if remaining > 0:
                self._sleep(remaining)
                self.total_wait_s += remaining
                now = self._clock()
        self._last_call = now


@dataclass
class HttpStats:
    requests: int = 0
    retries: int = 0
    bytes_received: int = 0


def build_retry(max_retries: int, backoff_factor: float) -> Retry:
    return Retry(
        total=max_retries,
        connect=max_retries,
        read=max_retries,
        status=max_retries,
        backoff_factor=backoff_factor,
        backoff_jitter=0.5,
        backoff_max=60,
        status_forcelist=RETRY_STATUS,
        allowed_methods=frozenset({"GET"}),
        respect_retry_after_header=True,
        retry_after_max=120,
        raise_on_status=True,
    )


class HttpClient:
    """GET com timeout explícito, limite de taxa por API e retentativas limitadas."""

    def __init__(
        self,
        name: str,
        *,
        min_interval_s: float,
        timeout_s: tuple[float, float],
        max_retries: int,
        backoff_factor: float,
        session: requests.Session | None = None,
        rate_limiter: RateLimiter | None = None,
    ) -> None:
        self.name = name
        self._timeout_s = timeout_s
        self._limiter = rate_limiter or RateLimiter(min_interval_s)
        self._session = session or requests.Session()
        adapter = HTTPAdapter(max_retries=build_retry(max_retries, backoff_factor))
        self._session.mount("https://", adapter)
        self._session.mount("http://", adapter)
        self._session.headers.update({"Accept": "application/json", "User-Agent": "ft03-pipeline/1.0"})
        self.stats = HttpStats()

    @property
    def rate_limit_wait_s(self) -> float:
        return self._limiter.total_wait_s

    def get_text(self, url: str, params: Mapping[str, str] | None = None) -> str:
        """Faz um GET e devolve o corpo como texto; levanta erro classificado em falha."""
        self._limiter.wait()
        self.stats.requests += 1
        safe_url = redact(requests.Request("GET", url, params=params).prepare().url or url)
        try:
            response = self._session.get(url, params=params, timeout=self._timeout_s)
        except requests.exceptions.RetryError as exc:
            raise TransientHTTPError(
                f"[{self.name}] retentativas esgotadas em {safe_url}: {redact(str(exc))}"
            ) from exc
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
            raise TransientHTTPError(
                f"[{self.name}] timeout ou falha de conexão em {safe_url}: {redact(str(exc))}"
            ) from exc
        except requests.exceptions.RequestException as exc:
            raise HttpError(f"[{self.name}] falha na requisição {safe_url}: {redact(str(exc))}") from exc

        history = getattr(getattr(response.raw, "retries", None), "history", ()) or ()
        self.stats.retries += len(history)
        self.stats.bytes_received += len(response.content)

        if 400 <= response.status_code < 500:
            snippet = redact(response.text[:300])
            raise PermanentHTTPError(
                f"[{self.name}] HTTP {response.status_code} em {safe_url}: {snippet}",
                status_code=response.status_code,
            )
        if response.status_code >= 500:
            raise TransientHTTPError(f"[{self.name}] HTTP {response.status_code} em {safe_url}")
        if history:
            logger.warning("[%s] sucesso após %d retentativa(s): %s", self.name, len(history), safe_url)
        response.encoding = response.encoding or "utf-8"
        return response.text
