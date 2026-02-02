import pandas as pd

def import_excel_sheets(file_path):
    #open file
	xlsx = pd.ExcelFile(file_path)
	data = {sheet: xlsx.parse(sheet) for sheet in xlsx.sheet_names}
	return data






