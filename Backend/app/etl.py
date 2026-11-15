
from pathlib import Path

import pandas as pd


TEMPERATURE_FACTORS = {
    "k": "K",
    "kelvin": "K",
    "c": "C",
    "°c": "C",
    "celsius": "C",
    "f": "F",
    "°f": "F",
    "fahrenheit": "F",
}

PRESSURE_UNITS = {
    "kpa": "kpa",
    "pa": "pa",
    "bar": "bar",
    "atm": "atm",
    "psi": "psi",
}


def temperature_to_kelvin(value, unit):
    """Converter uma temperatura para Kelvin."""

    if pd.isna(value):
        return None

    unit = str(unit).strip().lower()

    if unit not in TEMPERATURE_FACTORS:
        raise ValueError(f"Unidade de temperatura desconhecida: {unit}")

    normalized = TEMPERATURE_FACTORS[unit]

    if normalized == "K":
        result = float(value)
    elif normalized == "C":
        result = float(value) + 273.15
    else:
        result = (float(value) - 32) * 5 / 9 + 273.15

    if result < 0:
        raise ValueError("Temperatura inferior ao zero absoluto.")

    return result


def pressure_to_kpa(value, unit):
    """Converter uma pressão para kPa."""

    if pd.isna(value):
        return None

    unit = str(unit).strip().lower()

    if unit not in PRESSURE_UNITS:
        raise ValueError(f"Unidade de pressão desconhecida: {unit}")

    factors = {
        "kpa": 1,
        "pa": 0.001,
        "bar": 100,
        "atm": 101.325,
        "psi": 6.894757,
    }

    return float(value) * factors[unit]


def mark_outliers(df, column):
    """
    Identificar valores suspeitos através do intervalo interquartil.
    Não remove nenhuma medição.
    """

    if column not in df.columns:
        return pd.Series(False, index=df.index)

    values = pd.to_numeric(df[column], errors="coerce")

    valid = values.dropna()

    if len(valid) < 4:
        return pd.Series(False, index=df.index)

    q1 = valid.quantile(0.25)
    q3 = valid.quantile(0.75)
    iqr = q3 - q1

    lower = q1 - (1.5 * iqr)
    upper = q3 + (1.5 * iqr)

    return (values < lower) | (values > upper)


def process_telemetry_csv(
    file_path,
    output_path=None,
    remove_outliers=False,
):
    """
    Ler, limpar e padronizar um CSV de telemetria.

    Colunas esperadas:
    time_s
    flame_temperature
    temperature_unit
    pressure
    pressure_unit
    burning_rate_mm_s
    soot_emission

    As colunas de pressão e temperatura são opcionais.
    Quando existem valores nessas colunas, as respectivas
    unidades também são obrigatórias.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Ficheiro não encontrado: {path}")

    df = pd.read_csv(path)

    # Uniformizar nomes das colunas.
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    # Uniformizar valores nulos.
    df = df.replace(
        ["", "NA", "N/A", "NULL", "null", "None", "-"],
        pd.NA
    )

    # Converter colunas numéricas.
    numeric_columns = [
        "time_s",
        "flame_temperature",
        "pressure",
        "burning_rate_mm_s",
        "soot_emission",
    ]

    for column in numeric_columns:
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    # Converter temperatura para Kelvin.
    if "flame_temperature" in df.columns:

        if "temperature_unit" not in df.columns:
            raise ValueError(
                "O CSV precisa da coluna temperature_unit "
                "para converter temperaturas."
            )

        df["flame_temperature_k"] = df.apply(
            lambda row: temperature_to_kelvin(
                row["flame_temperature"],
                row["temperature_unit"],
            ),
            axis=1,
        )

    # Converter pressão para kPa.
    if "pressure" in df.columns:

        if "pressure_unit" not in df.columns:
            raise ValueError(
                "O CSV precisa da coluna pressure_unit "
                "para converter pressões."
            )

        df["pressure_kpa"] = df.apply(
            lambda row: pressure_to_kpa(
                row["pressure"],
                row["pressure_unit"],
            ),
            axis=1,
        )

    # Sinalizar valores suspeitos.
    outlier_columns = [
        "flame_temperature_k",
        "pressure_kpa",
        "burning_rate_mm_s",
        "soot_emission",
    ]

    flags = pd.Series(False, index=df.index)

    for column in outlier_columns:
        flags = flags | mark_outliers(df, column)

    df["is_outlier"] = flags

    # Valores negativos em grandezas que não devem ser negativos.
    physical_checks = {
        "time_s": "tempo negativo",
        "flame_temperature_k": "temperatura inválida",
        "pressure_kpa": "pressão negativa",
        "burning_rate_mm_s": "taxa de queima negativa",
        "soot_emission": "emissão negativa",
    }

    df["quality_flags"] = ""

    for column, message in physical_checks.items():
        if column in df.columns:
            invalid = df[column] < 0

            df.loc[invalid, "quality_flags"] = (
                df.loc[invalid, "quality_flags"]
                .apply(
                    lambda current: (
                        f"{current}; {message}".strip("; ")
                    )
                )
            )

    if "is_outlier" in df.columns:
        df.loc[df["is_outlier"], "quality_flags"] = (
            df.loc[df["is_outlier"], "quality_flags"]
            .apply(
                lambda current: (
                    f"{current}; possível outlier".strip("; ")
                )
            )
        )

    # Remoção apenas quando expressamente solicitada.
    if remove_outliers:
        df = df[~df["is_outlier"]].copy()

    # Guardar o resultado, se solicitado.
    if output_path:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output, index=False)

    return df
