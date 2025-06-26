from pathlib import Path
import pandas as pd

# Docling imports
from docling.document_converter import DocumentConverter

INPUT_FILE = "sample-data/batch/2206.01062.pdf"
OUTPUT_DIR = "/tmp/export-tables/"

input_file = Path(INPUT_FILE)
output_path = Path(OUTPUT_DIR)
    
output_path.mkdir(parents=True, exist_ok=True)

def main():

    doc_converter = DocumentConverter()

    conv_res = doc_converter.convert(input_file)
    out_file_name = conv_res.input.file.stem
    
    for table_ix, table in enumerate(conv_res.document.tables):
        table_df: pd.DataFrame = table.export_to_dataframe()
        print(f"## Table {table_ix}")
        print(table_df.to_markdown())

        # Save the table as csv
        element_csv_filename = output_path / f"{out_file_name}-table-{table_ix + 1}.csv"
        table_df.to_csv(element_csv_filename)

if __name__ == "__main__":
    main()