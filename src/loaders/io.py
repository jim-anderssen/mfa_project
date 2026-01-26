"""
io.py

All functions related to reading and writing data.
NO cleaning, NO feature engineering, NO plotting.
"""

from pathlib import Path
import pandas as pd
import eurostat


# Define base data folders once
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # src/loaders/io.py -> project root
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"


# ---------- Loading functions ----------


def load_csv(filename, folder="raw"):
    """
    Load a CSV file from the data directory.

    Parameters
    ----------
    filename : str
        Name of the CSV file (e.g. "sales.csv")
    folder : str
        Either "raw" or "processed"

    Returns
    -------
    pandas.DataFrame
    """
    path = _get_path(filename, folder)
    return pd.read_csv(path)


def load_excel(filename, sheet_name=0, folder="raw"):
    """
    Load an Excel file from the data directory.
    """
    path = _get_path(filename, folder)
    return pd.read_excel(path, sheet_name=sheet_name)


def load_dataset(datacode: str):
    """Loads eurostat dataset"""
    dataset = eurostat.get_data_df(datacode, flags=False)

    labels = eurostat.get_dic(datacode)
    label_descriptions = {}

    wrong_col = [
        c for c in dataset.select_dtypes(include="object").columns if "\\" in c
    ]
    if wrong_col:
        dataset = dataset.rename(columns={wrong_col[0]: wrong_col[0].split("\\")[0]})

    for col in dataset.select_dtypes(include="object").columns:
        print(col[0])
        if col[0] in "1234567890":
            continue
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


# ---------- Saving functions ----------


def save_csv(df, filename, folder="processed", index=False):
    """
    Save a DataFrame to the data directory.
    """
    path = _get_path(filename, folder)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=index)


# ---------- Internal helpers ----------


def _get_path(filename, folder):
    """
    Build a full path inside the data directory.
    """
    if folder == "raw":
        return RAW_DIR / filename
    elif folder == "processed":
        return PROCESSED_DIR / filename
    else:
        raise ValueError("folder must be 'raw' or 'processed'")
