import pandas as pd
import eurostat
import numpy as np
from functools import reduce


# Loads eurostat dataset
def load_dataset(datacode: str, n_datapoints: int = 3):
    """
    Load Eurostat dataset with statistics calculated over recent data only.

    Parameters
    ----------
    datacode : str
        Eurostat dataset code (e.g., 'env_wasgen')
    n_datapoints : int, optional
        Number of most recent data points to use for statistics.
        Since Eurostat waste data is bi-annual, 3 data points = 6 years.
        Default: 3

    Returns
    -------
    dataset : pd.DataFrame
        Dataset with added columns:
        - mean_{code}: Mean over recent data points
        - std_{code}: Standard deviation over recent data points
        - se_{code}: Standard error = std / sqrt(n_actual)
        - n_datapoints: Number of non-null values used
        - years_used: Comma-separated list of years used
    labels : dict
        Dataset labels
    label_descriptions : dict
        Descriptions for each label
    """
    dataset = eurostat.get_data_df(datacode, flags=False)

    try:
        dataset = extract_tonnes_row(dataset)
    except Exception as e:
        print(f"Exception: {e}")
        pass
    try:
        year_cols = dataset.select_dtypes(include="number").columns
        # Sort year columns descending and take only the most recent N data points
        # (bi-annual data: 3 data points = 6 years)
        year_cols_sorted = sorted(year_cols, reverse=True)[:n_datapoints]

        # Calculate statistics over recent data only
        dataset[f"mean_{datacode[4:]}"] = dataset[year_cols_sorted].mean(axis=1)
        dataset[f"std_{datacode[4:]}"] = dataset[year_cols_sorted].std(axis=1)

        # Count actual non-null values per row
        n_actual = dataset[year_cols_sorted].notna().sum(axis=1)
        dataset["n_datapoints"] = n_actual

        # Standard error: SE = std / sqrt(n)
        # Higher SE when fewer data points available
        dataset[f"se_{datacode[4:]}"] = dataset[f"std_{datacode[4:]}"] / np.sqrt(n_actual)

        # Store which years were used for transparency
        # year_cols_sorted contains column names (could be int or str)
        dataset["years_used"] = ", ".join(str(y) for y in sorted(year_cols_sorted))

        # Keep legacy column name for backwards compatibility
        dataset["Number_of_years"] = n_actual
    except Exception as e:
        print(f"Exception: {e}")
    labels = eurostat.get_dic(datacode)
    label_descriptions = {}

    wrong_col = [
        c for c in dataset.select_dtypes(include="object").columns if "\\" in c
    ]
    if wrong_col:
        dataset = dataset.rename(columns={wrong_col[0]: wrong_col[0].split("\\")[0]})

    for col in dataset.select_dtypes(include="object").columns:
        relevant_descriptions = dataset[col].unique()
        try:
            all_descriptions = eurostat.get_dic(datacode, col, frmt="df")  #
            # get only the relevant descirptions and add them to label_description[col]
            label_descriptions[col] = all_descriptions[
                all_descriptions["val"].isin(relevant_descriptions)
            ]
        except Exception as e:
            print(f"Exception: {e}")
    return dataset, labels, label_descriptions


def extend_eurostat_dataset(df_dictionary, cols: list):
    """
    Add explanatory description columns to Eurostat dataset.

    Merges label descriptions into the main dataframe, placing each
    description column directly after its corresponding code column.

    Parameters
    ----------
    df_dictionary : tuple
        Output from load_dataset(): (dataset, labels, label_descriptions)
    cols : list
        Column names to add descriptions for (e.g., ['nace_r2', 'waste', 'geo'])

    Returns
    -------
    pd.DataFrame
        Dataset with added {col}_description columns

    Example
    -------
    >>> dataset, labels, label_descriptions = load_dataset('env_wasgen')
    >>> df = extend_eurostat_dataset((dataset, labels, label_descriptions), ['nace_r2', 'waste', 'geo'])
    """
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


def extract_tonnes_row(df):
    if "T" in df["unit"].unique():
        return df[df["unit"] == "T"]
    else:
        return df


# Loads the shipment data (containing LoW codes) and merges it with EWC-Stat codes
def load_shipment_data_with_EWC_codes():
    wasship_df = pd.read_excel(
        "data/raw/Waste_shipment_data_imports_exports_20250927.xlsx", header=8
    )

    wasship_df.rename(columns={"European List of Waste code": "LoW_Code"}, inplace=True)

    LoW_to_EWC_df = pd.read_csv("data/interim/EWC_LoW_codes.csv", sep=";", dtype=str)
    LoW_to_EWC_df["Middle_Level_Code"] = (
        LoW_to_EWC_df["Middle_Level_Code"]
        .astype(str)
        .str.replace(r"^([1-9])\.", r"0\1.", regex=True)
    )
    LoW_to_EWC_df["LoW_Code"] = LoW_to_EWC_df["LoW_Code"].str.replace(" ", "")

    wasship_df[["Population", "Quantity in kg per capita"]] = wasship_df[
        ["Population", "Quantity in kg per capita"]
    ].apply(pd.to_numeric, errors="coerce")

    return pd.merge(
        wasship_df,
        LoW_to_EWC_df,
        how="inner",
        on="LoW_Code",
    )
