from pathlib import Path

# Docling imports
from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
from transformers import AutoTokenizer
from docling.document_converter import DocumentConverter
from docling.chunking import HybridChunker

EMBED_MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
MAX_TOKENS = 200

input_file = Path("sample-data/pg2680.html")

doc_converter = DocumentConverter()
doc = doc_converter.convert(source=input_file).document

def default_chunker():

    chunker = HybridChunker()
    chunk_iter = chunker.chunk(dl_doc=doc)

    for i, chunk in enumerate(chunk_iter):
        print(f"=== Chunk #{i} ===")
        enriched_text = chunker.contextualize(chunk=chunk)
        print(f"Chunk Text:\n{f'{enriched_text}'!r}")
        print()

def customized_chunker():
    tokenizer = HuggingFaceTokenizer(
        tokenizer=AutoTokenizer.from_pretrained(EMBED_MODEL_ID),
        max_tokens=MAX_TOKENS
    )

    chunker = HybridChunker(
        tokenizer=tokenizer,
        merge_peers=True,
    )

    chunk_iter = chunker.chunk(dl_doc=doc)
    chunks = list(chunk_iter)

    for i, chunk in enumerate(chunks):
        print(f"=== Chunk #{i} ===")

        ser_txt = chunker.contextualize(chunk=chunk)
        ser_tokens = tokenizer.count_tokens(ser_txt)
        print(f"Chunk contains ({ser_tokens} tokens):\n{ser_txt!r}")

        print()
    
if __name__ == "__main__":
    default_chunker()
    #customized_chunker()