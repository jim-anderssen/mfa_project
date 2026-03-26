from functools import reduce


def extend_eurostat_dataset(df_dictionary, cols: list):
    """Add explanatory description to columns of waste dataset collected via the Eurostat API"""
    for col in cols:
        df_dictionary[2][col].rename(
            columns={"val": col, "descr": f"{col}_description"}, inplace=True
        )

    tables = [df_dictionary[0]] + [df_dictionary[2][col] for col in cols]

    df = reduce(lambda left, right: left.merge(right, how="inner"), tables)

    for col in cols:
        description_col = df.pop(f"{col}_description")
        df.insert(df.columns.get_loc(col) + 1, f"{col}_description", description_col)

    return df
