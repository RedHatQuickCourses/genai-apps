from pathlib import Path

# Docling imports
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TesseractCliOcrOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from docling_core.types.doc import ImageRefMode

INPUT_FILE = "sample-data/custom/doclaynet-paper.pdf"
OUTPUT_DIR = "/tmp/custom-converted"

input_file = Path(INPUT_FILE)
output_path = Path(OUTPUT_DIR)
    
output_path.mkdir(parents=True, exist_ok=True)

def convert_default():
    
    pipeline_options = PdfPipelineOptions()

    doc_converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_options
            )
        }
    )

    conv_results = doc_converter.convert(input_file)
    out_file_name = conv_results.input.file.stem
    conv_results.document.save_as_markdown(
            output_path / f"{out_file_name}-default.md"
        )

def convert_pypdfium_backend():
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = True
    pipeline_options.do_table_structure = True
    pipeline_options.table_structure_options.do_cell_matching = True
    pipeline_options.generate_picture_images = True

    doc_converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_options, backend=PyPdfiumDocumentBackend
            )
        }
    )

    conv_results = doc_converter.convert(input_file)
    out_file_name = conv_results.input.file.stem
    conv_results.document.save_as_markdown(
            output_path / f"{out_file_name}-pypdfium-backend.md",
            image_mode=ImageRefMode.EMBEDDED
        )
    
# Need to do the following for this to work:
    # brew install tesseract leptonica pkg-config
    # TESSDATA_PREFIX=/opt/homebrew/share/tessdata/
    # export "TESSDATA_PREFIX=${TESSDATA_PREFIX}"
    # pip install --no-binary :all: tesserocr==2.8.0
def convert_tesseract_ocr():
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = True
    pipeline_options.do_table_structure = True
    pipeline_options.table_structure_options.do_cell_matching = True
    pipeline_options.generate_picture_images = True
    pipeline_options.ocr_options = TesseractCliOcrOptions(force_full_page_ocr=True)

    doc_converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_options
            )
        }
    )

    conv_results = doc_converter.convert(input_file)
    out_file_name = conv_results.input.file.stem
    conv_results.document.save_as_markdown(
            output_path / f"{out_file_name}-tesseract-ocr.md",
            image_mode=ImageRefMode.EMBEDDED
        )


if __name__ == "__main__":
    #convert_default()
    #convert_pypdfium_backend()
    convert_tesseract_ocr()