import pandas as pd
import xlsxwriter
import csv_amplitude_audit

# Load data
filtered = pd.read_csv("filtered_event_list.csv").fillna("")  # blank out NULLs
summary = pd.read_csv("event_tag_audit_summary.csv")
pillar = pd.read_csv("pillar_leader_dashboard.csv")
category = pd.read_csv("category_by_pillar_breakdown.csv")

# Create workbook
workbook = xlsxwriter.Workbook("Amplitude_Event_Audit_Dashboard.xlsx", {
    'nan_inf_to_errors': True
})

# Create worksheets
ws_summary = workbook.add_worksheet("Event Summary")
ws_pillar = workbook.add_worksheet("Pillar Dashboard")
ws_category = workbook.add_worksheet("Category Breakdown")
ws_filtered = workbook.add_worksheet("Filtered Events")

# Write DataFrames to Excel
def write_df(sheet, df):
    for row_idx, row in enumerate([df.columns.tolist()] + df.values.tolist()):
        for col_idx, val in enumerate(row):
            val = "" if pd.isna(val) else val
            sheet.write(row_idx, col_idx, val)

write_df(ws_summary, summary)
write_df(ws_pillar, pillar)
write_df(ws_category, category)
write_df(ws_filtered, filtered)

# Create pillar-level charts using % PM Complete, % QA Pass, % QA Tagging Missing
def add_column_chart(sheet, title, df, column_name, start_row=1, insert_cell='N2'):
    """
    Adds a column chart to the sheet using the specified column in df.
    """
    col_index = df.columns.get_loc(column_name)
    category_index = df.columns.get_loc("Pillar")  # Always use "Pillar" as x-axis
    chart = workbook.add_chart({'type': 'column'})

    chart.add_series({
        'name':       title,
        'categories': [sheet.get_name(), start_row, category_index, start_row + len(df) - 1, category_index],
        'values':     [sheet.get_name(), start_row, col_index, start_row + len(df) - 1, col_index],
    })

    chart.set_title({'name': title})
    chart.set_y_axis({'name': '%'})
    chart.set_legend({'none': True})
    sheet.insert_chart(insert_cell, chart)


add_column_chart(ws_pillar, '% PM Complete', pillar, '% PM Complete', insert_cell='N2')
add_column_chart(ws_pillar, '% QA Pass', pillar, '% QA Pass', insert_cell='N18')
add_column_chart(ws_pillar, '% QA Tagging Missing', pillar, '% QA Tagging Missing', insert_cell='N34')


# Pie chart: Event Volume by Pillar
pie_chart = workbook.add_chart({'type': 'pie'})
pie_chart.add_series({
    'name': 'Event Volume by Pillar',
    'categories': ['Pillar Dashboard', 1, 0, len(pillar), 0],
    'values': ['Pillar Dashboard', 1, 1, len(pillar), 1]
})
pie_chart.set_title({'name': 'Event Distribution'})
ws_pillar.insert_chart('N50', pie_chart)

# QA Pass vs Fail replaced with % QA Pass already above

# Category-level dashboards per pillar
pillars = ['Core', 'Extension', 'Platform']
for p in pillars:
    df = category[category['Pillar'] == p]
    if df.empty:
        continue
    sheet = workbook.add_worksheet(p)
    write_df(sheet, df)

    add_column_chart(sheet, f'{p} - % PM Complete', df, '% PM Complete', insert_cell='N2')
    add_column_chart(sheet, f'{p} - % QA Pass', df, '% QA Pass', insert_cell='N18')
    add_column_chart(sheet, f'{p} - % QA Tagging Missing', df, '% QA Tagging Missing', insert_cell='N34')


    # Pie chart: Event volume by category
    pie = workbook.add_chart({'type': 'pie'})
    pie.add_series({
        'name': f'{p} - Event Volume',
        'categories': [p, 1, 1, len(df), 1],
        'values': [p, 1, 2, len(df), 2]
    })
    pie.set_title({'name': f'{p} - Event Volume'})
    sheet.insert_chart('N50', pie)

workbook.close()
print("✅ Excel file 'Amplitude_Event_Audit_Dashboard.xlsx' created successfully.")