import os
import json

# langchain imports
from langchain_core.prompts import PromptTemplate
from langchain_docling.loader import ExportType
from langchain_docling import DoclingLoader
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_milvus import Milvus
from langchain_ollama import OllamaLLM
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

# docling imports
from docling.chunking import HybridChunker

# Need to set this env var to prevent thread deadlocks
os.environ["TOKENIZERS_PARALLELISM"] = "false"

FILE_PATH = ["sample-data/docling-rpt.pdf"] 
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
INFERENCE_MODEL="granite3.3:2b"
EXPORT_TYPE = ExportType.DOC_CHUNKS

QUESTION = "What AI models are provided by Docling?"

PROMPT = PromptTemplate.from_template(
    "Context information is below.\n---------------------\n{context}\n---------------------\n"
    "Given the context information and no prior knowledge, answer the query.\n"
    "Query: {input}\nAnswer:\n",
)

TOP_K = 3
MILVUS_URI = "/tmp/docstore.db"

def main():

    # convert PDF to smaller chunks of text
    loader = DoclingLoader(
        file_path=FILE_PATH,
        export_type=EXPORT_TYPE,
        chunker=HybridChunker(tokenizer=EMBEDDING_MODEL),
    )

    docs = loader.load()

    # Convert chunks into Vector embeddings
    embedding = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    # Store embeddings in Milvus Vector DB

    vectorstore = Milvus.from_documents(
        documents=docs,
        embedding=embedding,
        collection_name="rag_demo",
        connection_args={"uri": MILVUS_URI},
        drop_old=True
    )


    llm = OllamaLLM(
        model=INFERENCE_MODEL
    )

    # retrieve stored docs
    retriever = vectorstore.as_retriever(search_kwargs={"k": TOP_K})

    question_answer_chain = create_stuff_documents_chain(llm, PROMPT)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)
    resp_dict = rag_chain.invoke({"input": QUESTION})

    clipped_answer = clip_text(resp_dict["answer"], threshold=500)
    print("\n")
    print(f"Question:\n{resp_dict['input']}\n\nAnswer:\n{clipped_answer}")
    for i, doc in enumerate(resp_dict["context"]):
        print()
        print(f"Source {i + 1}:")
        print(f"  text: {json.dumps(clip_text(doc.page_content, threshold=350))}")
        for key in doc.metadata:
            if key != "pk":
                val = doc.metadata.get(key)
                clipped_val = clip_text(val) if isinstance(val, str) else val
                print(f"  {key}: {clipped_val}")

def clip_text(text, threshold=100):
    return f"{text[:threshold]}..." if len(text) > threshold else text

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

if __name__ == "__main__":
    main()