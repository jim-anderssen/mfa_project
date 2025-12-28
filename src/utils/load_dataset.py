import pandas as pd
import eurostat


def load_dataset(datacode: str):
    dataset = eurostat.get_data_df(datacode, flags=False)

    try:
        dataset = extract_tonnes_row(dataset)
    except Exception as e:
        print(f"Exception: {e}")
        pass
    try:
        dataset[f"mean_{datacode[4:]}"] = dataset.select_dtypes(include="number").mean(
            axis=1
        )
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


def extract_tonnes_row(df):
    if "T" in df["unit"].unique():
        return df[df["unit"] == "T"]
    else:
        return df
