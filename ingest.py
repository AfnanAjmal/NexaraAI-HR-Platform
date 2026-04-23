import argparse
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest a PDF into Chroma vector DB.")
    parser.add_argument(
        "--pdf",
        default="data/NexaraAI_Company_Handbook.pdf",
        help="Path to source PDF.",
    )
    parser.add_argument(
        "--persist-dir",
        default="chroma-db",
        help="Directory where Chroma data will be persisted.",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=500,
        help="Chunk size for text splitting.",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=100,
        help="Chunk overlap for text splitting.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    load_dotenv()
    os.environ["ANONYMIZED_TELEMETRY"] = "False"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    if args.chunk_overlap >= args.chunk_size:
        raise ValueError("chunk-overlap must be smaller than chunk-size")

    print(f"Loading PDF: {pdf_path}")
    loader = PyPDFLoader(str(pdf_path))
    documents = loader.load()
    if not documents:
        raise ValueError("No pages were loaded from the PDF")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )
    chunks = splitter.split_documents(documents)
    print(f"Total chunks: {len(chunks)}")

    embedding_model = HuggingFaceEmbeddings(
        model_name="BAAI/bge-small-en-v1.5",
        model_kwargs={"device": "cpu"},
    )

    persist_dir = Path(args.persist_dir)
    persist_dir.mkdir(parents=True, exist_ok=True)

    Chroma.from_documents(
        documents=chunks,
        embedding=embedding_model,
        persist_directory=str(persist_dir),
    )

    print(f"PDF ingested and stored in {persist_dir}/")


if __name__ == "__main__":
    main()