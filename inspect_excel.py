import pandas as pd

try:
    xlsx = pd.ExcelFile("datasets/CO2.xlsx")
    print("Sheet names:", xlsx.sheet_names)
    for sheet in xlsx.sheet_names:
        df = xlsx.parse(sheet)
        print(f"\nSheet: {sheet}")
        print("Columns:", df.columns.tolist())
        print("Head:")
        print(df.head())
except Exception as e:
    print(f"Error: {e}")
