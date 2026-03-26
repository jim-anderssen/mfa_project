import pandas as pd
import eurostat
from utils.load_dataset import load_dataset

# disposal domestic = disposal - import disposal

wasgen = load_dataset("env_wasgen")
wasgen[0]
wasship = pd.read_excel(
    "data/Waste_shipment_data_imports_exports_20250927.xlsx", header=8
)
wasship["European List of Waste code"].value_counts()
