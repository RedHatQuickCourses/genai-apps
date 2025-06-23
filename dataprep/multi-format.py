from pathlib import Path

from docling.document_converter import DocumentConverter
from docling_core.types.doc import ImageRefMode

INPUT_DIR = "sample-data/multi-format"
OUTPUT_DIR = "/tmp/multi-converted"

def main():
    input_path = Path(INPUT_DIR)
    output_path = Path(OUTPUT_DIR)
    allowed_extensions = ["*.pdf", "*.docx", "*.xlsx", "*.pptx", "*.csv", "*.asciidoc"]

    output_path.mkdir(parents=True, exist_ok=True)

    input_doc_paths: list[Path] = []

    for ext in allowed_extensions:
        input_doc_paths.extend(input_path.glob(ext))

    doc_converter = DocumentConverter()

    conv_results = doc_converter.convert_all(
        input_doc_paths,
        raises_on_error=False,
    )

    for conv_res in conv_results:
        out_file_name = conv_res.input.file.stem

        conv_res.document.save_as_json(
            output_path / f"{out_file_name}.json", 
            image_mode=ImageRefMode.PLACEHOLDER
        )

if __name__ == "__main__":
    main()