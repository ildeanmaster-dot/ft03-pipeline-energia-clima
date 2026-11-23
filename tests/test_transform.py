"""SQL: desaninhamento (UNNEST) e as cinco transformações, com entrada e saída conhecidas."""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import duckdb
import pytest

from conftest import AREAS_FILE, SQL_DIR, ons_records, open_meteo_payload, write_envelope
from pipeline.transform import FINAL_TABLE, run_transformations


def run(con: duckdb.DuckDBPyConnection, raw_dir: Path) -> dict[str, int]:
    return run_transformations(con, raw_dir, AREAS_FILE, SQL_DIR)


def test_unnest_ons_array_de_registros_vira_linhas(con: duckdb.DuckDBPyConnection, raw_dir: Path) -> None:
    counts = run(con, raw_dir)
    assert counts["ons_arquivos_brutos"] == 2  # 2 arquivos (PA, SP), cada um com um array
    assert counts["ons_registros_apos_unnest"] == 2 * 2 * 48
    columns = [row[0] for row in con.execute("DESCRIBE stg_ons").fetchall()]
    assert {"cod_areacarga", "din_referenciautc", "val_cargaglobal"} <= set(columns)


def test_unnest_clima_arrays_paralelos_viram_uma_linha_por_hora(con: duckdb.DuckDBPyConnection, raw_dir: Path) -> None:
    counts = run(con, raw_dir)
    assert counts["clima_horas_apos_unnest"] == 2 * 72
    row = con.execute(
        "SELECT time_txt, temperature_2m, relative_humidity_2m FROM stg_clima "
        "WHERE cod_areacarga = 'PA' AND time_txt = '2026-10-11T05:00'"
    ).fetchone()
    assert row == ("2026-10-11T05:00", pytest.approx(28.5), 70.0)  # valores da mesma posição dos arrays


def test_unnest_feriados_preserva_nacional_com_counties_nulo(con: duckdb.DuckDBPyConnection, raw_dir: Path) -> None:
    counts = run(con, raw_dir)
    assert counts["feriados_apos_unnest"] == 4
    # 2 nacionais (counties NULL -> 1 linha cada) + 1 regional com 1 UF + 1 regional com 2 UFs
    assert counts["feriados_uf_apos_unnest"] == 5
    assert con.execute("SELECT count(*) FROM stg_feriados_uf WHERE county IS NULL").fetchone() == (2,)


def test_t1_tipos_e_datas(con: duckdb.DuckDBPyConnection, raw_dir: Path) -> None:
    run(con, raw_dir)
    types = {row[0]: row[1] for row in con.execute("DESCRIBE t1_ons").fetchall()}
    assert types["dat_referencia"] == "DATE" and types["din_referencia_utc"] == "TIMESTAMP"
    assert con.execute("SELECT min(din_referencia_utc) FROM t1_ons").fetchone() == (datetime(2026, 10, 11, 3, 30),)
    assert {row[0]: row[1] for row in con.execute("DESCRIBE t1_clima").fetchall()}["hora_utc"] == "TIMESTAMP"


def test_t2_nulos_registro_sem_carga_e_rejeitado_e_contado(con: duckdb.DuckDBPyConnection, raw_dir: Path) -> None:
    path = raw_dir / "ons" / "PA_2026-10-11_2026-10-12.json"
    envelope = json.loads(path.read_text(encoding="utf-8"))
    envelope["payload"][0]["val_cargaglobal"] = None  # 03:30Z do dia 11
    envelope["payload"][1]["din_referenciautc"] = "data-invalida"
    path.write_text(json.dumps(envelope), encoding="utf-8")
    counts = run(con, raw_dir)
    assert counts["ons_rejeitados_por_nulo"] == 2
    reasons = {row[0] for row in con.execute("SELECT motivo_rejeicao FROM rejeitados_ons").fetchall()}
    assert reasons == {"carga_global_nula", "instante_invalido"}
    # a hora 03:00Z perdeu os dois intervalos: não aparece (não é preenchida por suposição)
    assert con.execute(
        f"SELECT count(*) FROM {FINAL_TABLE} WHERE cod_areacarga = 'PA' AND hora_utc = TIMESTAMP '2026-10-11 03:00:00'"
    ).fetchone() == (0,)


def test_t2_clima_nulo_e_preservado_e_sinalizado(con: duckdb.DuckDBPyConnection, raw_dir: Path) -> None:
    path = raw_dir / "open_meteo" / "PA_2026-10-11_2026-10-12.json"
    envelope = json.loads(path.read_text(encoding="utf-8"))
    envelope["payload"]["hourly"]["temperature_2m"][5] = None  # 2026-10-11T05:00
    path.write_text(json.dumps(envelope), encoding="utf-8")
    run(con, raw_dir)
    row = con.execute(
        f"SELECT temperatura_c, clima_disponivel, carga_media_mw FROM {FINAL_TABLE} "
        "WHERE cod_areacarga = 'PA' AND hora_utc = TIMESTAMP '2026-10-11 05:00:00'"
    ).fetchone()
    assert row is not None and row[0] is None and row[1] is False and row[2] is not None


def test_t3_deduplicacao_vence_o_registro_mais_recente(con: duckdb.DuckDBPyConnection, raw_dir: Path) -> None:
    # segundo arquivo repete o dia 11 de PA com atualização mais nova e carga diferente
    newer = ons_records("PA", date(2026, 10, 11), base_load=5000.0, updated="2026-11-05T00:00:00.000Z")
    write_envelope(raw_dir / "ons" / "PA_2026-10-11_2026-10-11.json", {"cod_areacarga": "PA", "dat_inicio": "2026-10-11", "dat_fim": "2026-10-11"}, newer)
    counts = run(con, raw_dir)
    assert counts["ons_registros_apos_unnest"] == 2 * 2 * 48 + 48
    assert counts["ons_apos_deduplicacao"] == 2 * 2 * 48
    assert con.execute(
        f"SELECT carga_media_mw FROM {FINAL_TABLE} WHERE cod_areacarga = 'PA' AND hora_utc = TIMESTAMP '2026-10-11 03:00:00'"
    ).fetchone() == (pytest.approx(5000.5),)


def test_t3_clima_repetido_vence_a_extracao_mais_recente(con: duckdb.DuckDBPyConnection, raw_dir: Path) -> None:
    # segundo arquivo repete o dia 11 de PA, extraído depois e com temperatura MENOR:
    # vence pela data de extração, nunca pelo valor medido
    newer = raw_dir / "open_meteo" / "PA_2026-10-11_2026-10-11.json"
    meta = {"cod_areacarga": "PA", "latitude_solicitada": -3.98, "longitude_solicitada": -53.07,
            "dat_inicio": "2026-10-11", "dat_fim": "2026-10-11", "extraido_em": "2026-11-20T08:00:00+00:00"}
    newer.write_text(json.dumps({"meta": meta, "payload": open_meteo_payload(date(2026, 10, 11), date(2026, 10, 11), temperature=10.0)}), encoding="utf-8")
    counts = run(con, raw_dir)
    assert counts["clima_horas_apos_unnest"] == 2 * 72 + 24
    assert counts["clima_apos_deduplicacao"] == 2 * 72
    assert con.execute(
        f"SELECT temperatura_c FROM {FINAL_TABLE} WHERE cod_areacarga = 'PA' AND hora_utc = TIMESTAMP '2026-10-11 05:00:00'"
    ).fetchone() == (pytest.approx(10.5),)


def test_agregacao_meia_hora_para_hora_cheia(con: duckdb.DuckDBPyConnection, raw_dir: Path) -> None:
    counts = run(con, raw_dir)
    assert counts["ons_horas_agregadas"] == 2 * 2 * 24
    # 03:30Z (1000) e 04:00Z (1001) formam a hora 03:00Z
    row = con.execute(
        f"SELECT carga_media_mw, carga_max_mw, qtd_intervalos, dat_referencia FROM {FINAL_TABLE} "
        "WHERE cod_areacarga = 'PA' AND hora_utc = TIMESTAMP '2026-10-11 03:00:00'"
    ).fetchone()
    assert row == (pytest.approx(1000.5), 1001.0, 2, date(2026, 10, 11))
    # a última hora do dia de referência 11 é 02:00Z do dia 12
    assert con.execute(
        f"SELECT max(hora_utc) FROM {FINAL_TABLE} WHERE dat_referencia = DATE '2026-10-11'"
    ).fetchone() == (datetime(2026, 10, 12, 2, 0),)


def test_t4_join_nao_multiplica_linhas_e_cruza_clima_e_feriado(con: duckdb.DuckDBPyConnection, raw_dir: Path) -> None:
    counts = run(con, raw_dir)
    assert counts["apos_join"] == counts["ons_horas_agregadas"] == counts["final"]
    assert con.execute(f"SELECT count(*) FROM {FINAL_TABLE} WHERE NOT clima_disponivel").fetchone() == (0,)
    holiday = dict(
        con.execute(
            f"SELECT uf, any_value(nome_feriado) FROM {FINAL_TABLE} "
            "WHERE dat_referencia = DATE '2026-10-12' AND eh_feriado GROUP BY uf"
        ).fetchall()
    )
    assert holiday == {
        "PA": "Nossa Senhora Aparecida",
        "SP": "Feriado estadual fictício de teste / Nossa Senhora Aparecida",  # 2 feriados, 1 linha
    }
    assert con.execute(f"SELECT count(*) FROM {FINAL_TABLE} WHERE dat_referencia = DATE '2026-10-11' AND eh_feriado").fetchone() == (0,)
    # feriado de tipo não público (28/10, 'Optional') fica fora
    assert con.execute("SELECT count(*) FROM t3_feriados WHERE data_feriado = DATE '2026-10-28'").fetchone() == (0,)


def test_t4_area_sem_clima_continua_no_resultado(con: duckdb.DuckDBPyConnection, raw_dir: Path) -> None:
    (raw_dir / "open_meteo" / "SP_2026-10-11_2026-10-12.json").unlink()
    counts = run(con, raw_dir)
    assert counts["final"] == 2 * 2 * 24
    assert con.execute(
        f"SELECT count(*) FROM {FINAL_TABLE} WHERE cod_areacarga = 'SP' AND NOT clima_disponivel AND temperatura_c IS NULL"
    ).fetchone() == (48,)


def test_t5_metricas_derivadas(con: duckdb.DuckDBPyConnection, raw_dir: Path) -> None:
    run(con, raw_dir)
    first = con.execute(
        f"SELECT participacao_mmgd_pct, variacao_carga_d1_pct, dia_semana, eh_fim_de_semana, ano, mes FROM {FINAL_TABLE} "
        "WHERE cod_areacarga = 'PA' AND hora_utc = TIMESTAMP '2026-10-11 03:00:00'"
    ).fetchone()
    # 11/10/2026 é domingo; sem dia anterior, a variação é NULL (não zero)
    assert first == (pytest.approx(100 * 10 / 1000.5), None, 7, True, 2026, 10)
    next_day = con.execute(
        f"SELECT variacao_carga_d1_pct, dia_semana, eh_fim_de_semana FROM {FINAL_TABLE} "
        "WHERE cod_areacarga = 'PA' AND hora_utc = TIMESTAMP '2026-10-12 03:00:00'"
    ).fetchone()
    assert next_day == (pytest.approx(0.0), 1, False)  # mesma carga do dia anterior


def test_amostras_reais_das_apis_passam_pelo_sql(con: duckdb.DuckDBPyConnection, tmp_path: Path) -> None:
    """Respostas reais capturadas em 12/11/2026 (tests/fixtures) com resultado conferido à mão."""
    fixtures = Path(__file__).parent / "fixtures"
    raw = tmp_path / "raw"
    load = lambda name: json.loads((fixtures / name).read_text(encoding="utf-8"))["payload"]  # noqa: E731
    write_envelope(raw / "ons" / "PA.json", {"cod_areacarga": "PA", "dat_inicio": "2026-10-11", "dat_fim": "2026-10-11"}, load("ons_amostra_real.json"))
    write_envelope(raw / "open_meteo" / "PA.json", {"cod_areacarga": "PA", "latitude_solicitada": -3.9812, "longitude_solicitada": -53.072, "dat_inicio": "2026-10-11", "dat_fim": "2026-10-11"}, load("open_meteo_amostra_real.json"))
    write_envelope(raw / "nager" / "BR_2026.json", {"ano": 2026, "pais": "BR"}, load("nager_amostra_real.json"))
    counts = run(con, raw)
    assert counts["ons_registros_apos_unnest"] == 6 and counts["clima_horas_apos_unnest"] == 24
    rows = con.execute(
        f"SELECT hour(hora_utc), carga_media_mw, temperatura_c, umidade_relativa_pct, participacao_mmgd_pct FROM {FINAL_TABLE} ORDER BY 1"
    ).fetchall()
    assert rows == [
        (3, pytest.approx((4140.3345 + 4129.3213) / 2), 26.4, 73.0, pytest.approx(100 * 0.02 / 4134.8279)),
        (4, pytest.approx((4092.3135 + 4058.3997) / 2), 25.7, 76.0, pytest.approx(100 * 0.02 / 4075.3566)),
        # 15:00 UTC = meio-dia em Brasília: a geração distribuída atende ~32% da carga
        (15, pytest.approx((3832.8232 + 3830.812) / 2), 33.4, 47.0, pytest.approx(32.19, abs=0.01)),
    ]
