from pathlib import Path

# Docling imports
from docling.backend.docling_parse_v4_backend import DoclingParseV4DocumentBackend
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.doc import ImageRefMode

INPUT_DIR = "sample-data/batch"
OUTPUT_DIR = "/tmp/batch-converted"

def main():
    input_path = Path(INPUT_DIR)
    output_path = Path(OUTPUT_DIR)
    
    output_path.mkdir(parents=True, exist_ok=True)

    input_doc_paths: list[Path] = list(input_path.glob("*.pdf"))

    pipeline_options = PdfPipelineOptions()
    pipeline_options.generate_page_images = True

    doc_converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_options, backend=DoclingParseV4DocumentBackend
            )
        }
    )

    conv_results = doc_converter.convert_all(
        input_doc_paths,
        raises_on_error=False,
    )

    for conv_res in conv_results:
        out_file_name = conv_res.input.file.stem

        conv_res.document.save_as_markdown(
            output_path / f"{out_file_name}.md", 
            image_mode=ImageRefMode.PLACEHOLDER
        )

if __name__ == "__main__":
    main()