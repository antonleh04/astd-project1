import pandas as pd
from data import import_excel_sheets

# 1. Load Data
co2_data_sheets = import_excel_sheets("datasets/CO2.xlsx")

fossil_CO2_totals_by_country = co2_data_sheets['fossil_CO2_totals_by_country']
fossil_CO2_per_capita_by_country = co2_data_sheets['fossil_CO2_per_capita_by_countr']
fossil_CO2_by_sector_and_country = co2_data_sheets['fossil_CO2_by_sector_and_countr']

# datasheet sector
df_sector = fossil_CO2_by_sector_and_country.melt(
    id_vars=['Sector', 'ISOcode', 'Country'], 
    var_name='Year', 
    value_name='CO2'
)
df_sector['Year'] = df_sector['Year'].astype(int)

# datasheet total
df_totals = fossil_CO2_totals_by_country.melt(
    id_vars=['ISOcode', 'Country'], 
    var_name='Year', 
    value_name='CO2'
)
df_totals['Year'] = df_totals['Year'].astype(int)

# datasheet per_capita
df_per_capita = fossil_CO2_per_capita_by_country.melt(
    id_vars=['ISOcode', 'Country'], 
    var_name='Year', 
    value_name='CO2_per_capita'
)
df_per_capita['Year'] = df_per_capita['Year'].astype(int)

# ---------------------------------------------------------
# 5. Check the results
# ---------------------------------------------------------
print("--- Sector Data ---")
print(df_sector.head(3))
print("\n--- Totals Data ---")
print(df_totals.head(3))
print("\n--- Per Capita Data ---")
print(df_per_capita.head(3))