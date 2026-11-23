"""Ponta a ponta com o cliente HTTP real contra um servidor local que imita as três APIs.

O servidor devolve um 503 na primeira chamada de cada API e corta as respostas do ONS
em 20 dias, como a API real faz em períodos longos.
"""

from __future__ import annotations

import json
import threading
from datetime import date, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

from conftest import holidays_payload, ons_records, open_meteo_payload
from pipeline import extract
from pipeline import main as pipeline_main
from pipeline.config import load_settings


class _FakeApis(BaseHTTPRequestHandler):
    failed_once: set[str] = set()

    def log_message(self, *args: object) -> None:
        pass

    def _json(self, status: int, payload: object) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        url = urlparse(self.path)
        query = {key: values[0] for key, values in parse_qs(url.query).items()}
        api = url.path.split("/")[1]
        if api not in self.failed_once:  # primeira chamada de cada API falha
            self.failed_once.add(api)
            self._json(503, {})
            return
        if api == "ons":
            start, end = date.fromisoformat(query["dat_inicio"]), date.fromisoformat(query["dat_fim"])
            days = [start + timedelta(days=offset) for offset in range(min((end - start).days + 1, 20))]
            self._json(200, [record for day in days for record in ons_records(query["cod_areacarga"], day)])
        elif api == "meteo":
            self._json(200, open_meteo_payload(date.fromisoformat(query["start_date"]), date.fromisoformat(query["end_date"])))
        else:
            self._json(200, holidays_payload())


def test_pipeline_completo_com_http_real_falhas_e_truncamento(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _FakeApis.failed_once = set()
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), _FakeApis)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{httpd.server_port}"
    monkeypatch.setenv("NO_PROXY", "127.0.0.1")
    monkeypatch.setenv("no_proxy", "127.0.0.1")
    monkeypatch.setattr(extract, "ONS_URL", f"{base}/ons")
    monkeypatch.setattr(extract, "OPEN_METEO_URL", f"{base}/meteo")
    monkeypatch.setattr(extract, "NAGER_URL", f"{base}/nager/{{year}}")
    settings = load_settings(
        {
            "DATA_INICIO": "2026-09-01", "DATA_FIM": "2026-10-31", "AREAS": "PA,SP",
            "RAW_DIR": str(tmp_path / "raw"), "OUTPUT_DIR": str(tmp_path / "output"),
            "ONS_MIN_INTERVAL_S": "0", "OPEN_METEO_MIN_INTERVAL_S": "0", "NAGER_MIN_INTERVAL_S": "0",
            "HTTP_BACKOFF_FACTOR": "0.01",
        }
    )
    try:
        report = pipeline_main.run_pipeline(settings)
    finally:
        httpd.shutdown()

    assert report["status"] == "success", report["erros"]
    extraction = report["extracao"]
    assert all(extraction[api]["retentativas"] >= 1 for api in ("ons", "open_meteo", "nager"))  # o 503 foi superado
    assert extraction["ons"]["registros"] == 2 * 61 * 48  # 2 áreas x 61 dias completos, apesar do corte em 20 dias
    assert extraction["ons"]["requisicoes"] > extraction["ons"]["arquivos_brutos"]  # janelas divididas
    assert report["linhas_por_etapa"]["final"] == 2 * 61 * 24
    assert [(p["ano"], p["mes"], p["linhas"]) for p in report["particoes_gravadas"]] == [(2026, 9, 1440), (2026, 10, 1488)]
    assert report["dataset"] == {"linhas_no_dataset": 2928, "compressao": ["SNAPPY"]}
    checks = {check["check"]: check for check in report["verificacoes"]}
    assert checks["join_cobertura_clima"]["observed"] == 1.0  # inclui as 3 últimas horas (clima com 1 dia a mais)
