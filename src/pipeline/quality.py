"""Validações automatizadas de qualidade: schema, null ratio, unicidade, intervalos e JOIN.

Cada verificação tem severidade: ``error`` bloqueia a publicação do dataset;
``warning`` é registrada no relatório e não bloqueia.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import duckdb

KEY_COLUMNS: tuple[str, ...] = ("cod_areacarga", "hora_utc")


@dataclass(frozen=True)
class ColumnSpec:
    """Contrato de uma coluna do dataset final."""

    name: str
    dtype: str
    max_null_ratio: float = 0.0
    minimum: float | None = None
    maximum: float | None = None
    range_severity: str = "error"


# Contrato do dataset final. Limites de intervalo são regras deste projeto:
# clima = faixa fisicamente plausível; carga = o dicionário do ONS admite valor
# negativo em val_cargaglobal, por isso o intervalo da carga é só um aviso.
CONTRACT: tuple[ColumnSpec, ...] = (
    ColumnSpec("cod_areacarga", "VARCHAR"),
    ColumnSpec("nome_area", "VARCHAR"),
    ColumnSpec("uf", "VARCHAR"),
    ColumnSpec("dat_referencia", "DATE"),
    ColumnSpec("hora_utc", "TIMESTAMP"),
    ColumnSpec("carga_media_mw", "DOUBLE", minimum=0, maximum=100_000, range_severity="warning"),
    ColumnSpec("carga_max_mw", "DOUBLE", minimum=0, maximum=100_000, range_severity="warning"),
    ColumnSpec("carga_mmgd_media_mw", "DOUBLE", max_null_ratio=0.05, minimum=0, maximum=100_000),
    ColumnSpec("qtd_intervalos", "INTEGER", minimum=1, maximum=2),
    ColumnSpec("temperatura_c", "DOUBLE", max_null_ratio=0.05, minimum=-20, maximum=55),
    ColumnSpec("umidade_relativa_pct", "DOUBLE", max_null_ratio=0.05, minimum=0, maximum=100),
    ColumnSpec("sensacao_termica_c", "DOUBLE", max_null_ratio=0.05, minimum=-30, maximum=65),
    ColumnSpec("precipitacao_mm", "DOUBLE", max_null_ratio=0.05, minimum=0, maximum=500),
    ColumnSpec("clima_disponivel", "BOOLEAN"),
    ColumnSpec("eh_feriado", "BOOLEAN"),
    ColumnSpec("nome_feriado", "VARCHAR", max_null_ratio=1.0),
    ColumnSpec("dia_semana", "INTEGER", minimum=1, maximum=7),
    ColumnSpec("eh_fim_de_semana", "BOOLEAN"),
    ColumnSpec("participacao_mmgd_pct", "DOUBLE", max_null_ratio=0.05, minimum=0, maximum=100, range_severity="warning"),
    ColumnSpec("variacao_carga_d1_pct", "DOUBLE", max_null_ratio=1.0),
    ColumnSpec("din_atualizacao_ons", "TIMESTAMP", max_null_ratio=1.0),
    ColumnSpec("ano", "INTEGER", minimum=2016, maximum=2100),
    ColumnSpec("mes", "INTEGER", minimum=1, maximum=12),
)


@dataclass
class CheckResult:
    check: str
    dimension: str
    severity: str
    passed: bool
    observed: Any
    expected: Any
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _scalar(con: duckdb.DuckDBPyConnection, sql: str) -> Any:
    row = con.execute(sql).fetchone()
    return row[0] if row else None


def check_schema(con: duckdb.DuckDBPyConnection, table: str) -> CheckResult:
    actual = {row[0]: row[1] for row in con.execute(f"DESCRIBE {table}").fetchall()}
    expected = {spec.name: spec.dtype for spec in CONTRACT}
    missing = sorted(set(expected) - set(actual))
    unexpected = sorted(set(actual) - set(expected))
    wrong_type = sorted(
        f"{name}: {actual[name]} (esperado {dtype})"
        for name, dtype in expected.items()
        if name in actual and actual[name] != dtype
    )
    problems = {"ausentes": missing, "inesperadas": unexpected, "tipo_divergente": wrong_type}
    passed = not (missing or unexpected or wrong_type)
    return CheckResult(
        "schema_contrato", "schema", "error", passed,
        observed=f"{len(actual)} colunas", expected=f"{len(expected)} colunas do contrato",
        detail="" if passed else str(problems),
    )


def null_ratios(con: duckdb.DuckDBPyConnection, table: str, columns: list[str]) -> dict[str, float]:
    total = _scalar(con, f"SELECT count(*) FROM {table}") or 0
    if total == 0:
        return {column: 0.0 for column in columns}
    expressions = ", ".join(f'count(*) FILTER (WHERE "{column}" IS NULL)' for column in columns)
    row = con.execute(f"SELECT {expressions} FROM {table}").fetchone()
    assert row is not None
    return {column: round(nulls / total, 6) for column, nulls in zip(columns, row)}


def check_nulls(ratios: dict[str, float]) -> list[CheckResult]:
    results = []
    for spec in CONTRACT:
        if spec.name not in ratios:
            continue
        ratio = ratios[spec.name]
        results.append(
            CheckResult(
                f"null_ratio:{spec.name}", "nulos",
                "error" if spec.max_null_ratio == 0 else "warning",
                ratio <= spec.max_null_ratio, observed=ratio, expected=f"<= {spec.max_null_ratio}",
            )
        )
    return results


def check_uniqueness(con: duckdb.DuckDBPyConnection, table: str) -> CheckResult:
    keys = ", ".join(KEY_COLUMNS)
    duplicated = _scalar(
        con, f"SELECT count(*) FROM (SELECT {keys} FROM {table} GROUP BY {keys} HAVING count(*) > 1)"
    )
    return CheckResult(
        "unicidade_chave", "unicidade", "error", duplicated == 0,
        observed=duplicated, expected=0, detail=f"chave: ({keys})",
    )


def check_ranges(con: duckdb.DuckDBPyConnection, table: str, available: set[str]) -> list[CheckResult]:
    results = []
    for spec in CONTRACT:
        if spec.minimum is None or spec.maximum is None or spec.name not in available:
            continue
        violations = _scalar(
            con,
            f'SELECT count(*) FROM {table} WHERE "{spec.name}" IS NOT NULL '
            f'AND ("{spec.name}" < {spec.minimum} OR "{spec.name}" > {spec.maximum})',
        )
        results.append(
            CheckResult(
                f"intervalo:{spec.name}", "intervalo", spec.range_severity, violations == 0,
                observed=violations, expected=0, detail=f"[{spec.minimum}, {spec.maximum}]",
            )
        )
    return results


def check_join_and_volume(
    con: duckdb.DuckDBPyConnection, table: str, expected_areas: list[str]
) -> list[CheckResult]:
    total = _scalar(con, f"SELECT count(*) FROM {table}") or 0
    results = [CheckResult("volume_nao_vazio", "volume", "error", total > 0, observed=total, expected="> 0")]

    hours_before_join = _scalar(
        con, "SELECT count(*) FROM carga_horaria WHERE cod_areacarga IN (SELECT cod_areacarga FROM dim_areas)"
    )
    results.append(
        CheckResult(
            "join_sem_multiplicacao", "join", "error", total == hours_before_join,
            observed=total, expected=hours_before_join, detail="linhas finais = horas de carga antes do JOIN",
        )
    )
    weather_ratio = (_scalar(con, f"SELECT count(*) FILTER (WHERE clima_disponivel) FROM {table}") or 0) / max(total, 1)
    results.append(
        CheckResult(
            "join_cobertura_clima", "join", "warning", weather_ratio >= 0.95,
            observed=round(weather_ratio, 6), expected=">= 0.95", detail="fração das horas com clima correspondente",
        )
    )
    present = {row[0] for row in con.execute(f"SELECT DISTINCT cod_areacarga FROM {table}").fetchall()}
    missing_areas = sorted(set(expected_areas) - present)
    results.append(
        CheckResult(
            "areas_solicitadas_presentes", "completude", "warning", not missing_areas,
            observed=len(present), expected=len(expected_areas), detail=f"ausentes: {missing_areas}" if missing_areas else "",
        )
    )
    incomplete_days = _scalar(
        con,
        f"SELECT count(*) FROM (SELECT cod_areacarga, dat_referencia FROM {table} "
        "GROUP BY ALL HAVING count(*) <> 24 OR min(qtd_intervalos) < 2)",
    )
    results.append(
        CheckResult(
            "dias_com_24_horas_completas", "completude", "warning", incomplete_days == 0,
            observed=incomplete_days, expected=0, detail="pares (área, dia) sem 24 horas ou com hora de 1 intervalo",
        )
    )
    return results


def run_quality_checks(
    con: duckdb.DuckDBPyConnection, table: str, expected_areas: list[str]
) -> tuple[list[CheckResult], dict[str, float]]:
    """Executa todas as verificações; devolve os resultados e o null ratio por coluna."""
    actual_columns = [row[0] for row in con.execute(f"DESCRIBE {table}").fetchall()]
    ratios = null_ratios(con, table, actual_columns)
    schema = check_schema(con, table)
    results = [schema] + check_nulls(ratios)
    if not schema.passed:
        # Com o schema fora do contrato, as demais regras (que dependem de nome e
        # tipo das colunas) não são confiáveis: a falha de schema já bloqueia.
        return results, ratios
    results.append(check_uniqueness(con, table))
    results += check_ranges(con, table, set(actual_columns))
    results += check_join_and_volume(con, table, expected_areas)
    return results, ratios


def has_blocking_failure(results: list[CheckResult]) -> bool:
    return any(not result.passed and result.severity == "error" for result in results)
