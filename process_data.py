from data import import_excel_sheets

co2_data_sheets = import_excel_sheets("datasets/CO2.xlsx")

fossil_CO2_totals_by_country = co2_data_sheets['fossil_CO2_totals_by_country']
fossil_CO2_per_capita_by_country = co2_data_sheets['fossil_CO2_per_capita_by_countr']
fossil_CO2_by_sector_and_country = co2_data_sheets['fossil_CO2_by_sector_and_countr']




