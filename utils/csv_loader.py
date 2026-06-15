import pandas as pd

REQUIRED_COLUMNS = {
    "record_id",
    "brand_name",
    "class_type",
    "alcohol_content",
    "net_contents",
    "government_warning",
}

OPTIONAL_COLUMNS = {
    "bottler_producer",
    "country_of_origin",
    "beverage_type",
}


def load_csv(uploaded_file):
    df = pd.read_csv(uploaded_file)
    df.columns = [col.strip().lower() for col in df.columns]

    missing = REQUIRED_COLUMNS - set(df.columns)

    if missing:
        return None, sorted(missing)

    return df, []