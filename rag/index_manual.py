from __future__ import annotations

import argparse
import hashlib
import os
import shutil
from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANUAL_PATH = (
    PROJECT_ROOT
    / "data"
    / "Manual"
    / "prusa3d_manual_core_one_l_101_en.pdf"
)
PERSIST_DIRECTORY = PROJECT_ROOT / "data" / "Store" / "chroma"
COLLECTION_NAME = "prusa-core-one-l-manual"

EQUIPMENT_MODEL = "PRUSA_CORE_ONE_L"
MANUAL_VERSION = "1.01"
EMBEDDING_MODEL = "text-embedding-3-large"
CHUNK_SIZE = 1500
CHUNK_OVERLAP = 200


def load_and_split_manual():
    if not MANUAL_PATH.exists():
        raise FileNotFoundError(f"Manual not found: {MANUAL_PATH}")

    loader = PyPDFLoader(str(MANUAL_PATH))
    pages = loader.load()

    for page in pages:
        zero_based_page = int(page.metadata.get("page", 0))
        page.metadata.update(
            {
                "source": MANUAL_PATH.name,
                "equipment_model": EQUIPMENT_MODEL,
                "manual_version": MANUAL_VERSION,
                "page_number": zero_based_page + 1,
            }
        )

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    chunks = text_splitter.split_documents(pages)

    for chunk_index, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = chunk_index

    return pages, chunks


def make_chunk_id(chunk) -> str:
    identity = "|".join(
        [
            chunk.metadata["source"],
            str(chunk.metadata["page_number"]),
            str(chunk.metadata["chunk_index"]),
            chunk.page_content,
        ]
    )
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:20]
    return f"{EQUIPMENT_MODEL.lower()}-{digest}"


def build_index(rebuild: bool = False) -> Chroma:
    load_dotenv(PROJECT_ROOT / ".env")

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY is missing. Add it to the project .env file."
        )

    if rebuild and PERSIST_DIRECTORY.exists():
        shutil.rmtree(PERSIST_DIRECTORY)

    PERSIST_DIRECTORY.mkdir(parents=True, exist_ok=True)
    pages, chunks = load_and_split_manual()

    embedding = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    database = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embedding,
        persist_directory=str(PERSIST_DIRECTORY),
        collection_metadata={"hnsw:space": "cosine"},
    )

    chunk_ids = [make_chunk_id(chunk) for chunk in chunks]
    for chunk, chunk_id in zip(chunks, chunk_ids):
        chunk.metadata["chunk_id"] = chunk_id

    database.add_documents(documents=chunks, ids=chunk_ids)

    print(f"Manual: {MANUAL_PATH.name}")
    print(f"Pages loaded: {len(pages)}")
    print(f"Chunks indexed: {len(chunks)}")
    print(f"Embedding model: {EMBEDDING_MODEL}")
    print(f"Collection: {COLLECTION_NAME}")
    print(f"Local store: {PERSIST_DIRECTORY}")

    return database


def search_example(database: Chroma, query: str, k: int = 4) -> None:
    print(f"\nQuery: {query}")
    results = database.similarity_search_with_relevance_scores(query, k=k)

    for rank, (document, score) in enumerate(results, 1):
        metadata = document.metadata
        preview = " ".join(document.page_content.split())[:240]
        print(
            f"[{rank}] score={score:.4f} "
            f"page={metadata.get('page_number')} "
            f"chunk={metadata.get('chunk_index')}"
        )
        print(f"    {preview}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Index the Prusa CORE One L manual into local Chroma."
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Delete the existing local Chroma store before indexing.",
    )
    parser.add_argument(
        "--query",
        help="Run one similarity search after indexing.",
    )
    parser.add_argument(
        "--k",
        type=int,
        default=4,
        help="Number of chunks returned by --query. Default: 4.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not 1 <= args.k <= 20:
        raise ValueError("k must be between 1 and 20")

    database = build_index(rebuild=args.rebuild)
    if args.query:
        search_example(database, args.query, args.k)


if __name__ == "__main__":
    main()
