import pandas as pd

def import_excel_sheets(file_path):
    #open file
	xlsx = pd.ExcelFile(file_path)
	data = {sheet: xlsx.parse(sheet) for sheet in xlsx.sheet_names}
	return data

#region load data

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








