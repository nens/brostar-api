import pandas as pd


def convert_excel_to_html(excel_file_path):
    """
    Convert Excel file to HTML for web display

    Args:
        excel_file_path (str): Path to the Excel file

    Returns:
        str: HTML representation of the Excel file
    """
    try:
        # Read all sheets from the Excel file
        excel_file = pd.ExcelFile(excel_file_path)
        sheet_names = excel_file.sheet_names

        html_output = ""

        # Process each sheet
        for sheet_name in sheet_names:
            df = pd.read_excel(excel_file_path, sheet_name=sheet_name)

            # Convert DataFrame to HTML with styling
            sheet_html = df.to_html(
                classes="table table-striped table-bordered table-hover",
                index=False,
                na_rep="",
                border=0,
            )

            # Add sheet name and html to output
            if len(sheet_names) > 1:
                html_output += f"<h3>{sheet_name}</h3>"
            html_output += sheet_html

        return html_output

    except Exception as e:
        return f"<div class='alert alert-danger'>Error converting Excel to HTML: {str(e)}</div>"
