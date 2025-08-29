import json
import pandas as pd

def load_data():
    with open("../data/nofluff_jobs_extended_930_jobs.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    # Create DataFrame object
    df = pd.DataFrame(data)

    return df
