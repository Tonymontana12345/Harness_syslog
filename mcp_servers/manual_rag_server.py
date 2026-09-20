from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from mcp.server import MCPServer


SERVER_NAME = "manual-rag"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
PERSIST_DIRECTORY = PROJECT_ROOT / "data" / "Store" / "chroma"
COLLECTION_NAME = "prusa-core-one-l-manual"
EMBEDDING_MODEL = "text-embedding-3-large"
QUERY_REWRITE_MODEL = "gpt-4o-mini"

KEYWORD_DICTIONARY = [
    "FAN_RPM_LOW -> fan suddenly slows down or stops, fan-related error",
    "HOTEND_FAN -> heatsink fan on the print head",
    "HOTEND_FAN_RPM -> heatsink fan RPM",
    "PRINT_FAN -> print fan",
    "PRINT_FAN_RPM -> print fan RPM",
    "SAFETY_STOP -> printer stops and displays a fan-related error",
    "COREONE-L-01 -> Prusa CORE One L",
]

load_dotenv(PROJECT_ROOT / ".env")
mcp = MCPServer(SERVER_NAME)


def _require_openai_api_key() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY is missing. Add it to the project .env file "
            "or export it before starting Claude Code."
        )


@lru_cache(maxsize=1)
def _get_embedding() -> OpenAIEmbeddings:
    _require_openai_api_key()
    return OpenAIEmbeddings(model=EMBEDDING_MODEL)


@lru_cache(maxsize=1)
def _get_database() -> Chroma:
    database_file = PERSIST_DIRECTORY / "chroma.sqlite3"
    if not database_file.exists():
        raise FileNotFoundError(
            "Local Chroma index was not found. Run "
            "'python rag/index_manual.py --rebuild' first."
        )

    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=_get_embedding(),
        persist_directory=str(PERSIST_DIRECTORY),
    )


@lru_cache(maxsize=1)
def _get_dictionary_chain():
    _require_openai_api_key()
    prompt = ChatPromptTemplate.from_template(
        """
Use the equipment terminology dictionary to rewrite the user's query for
retrieval from the Prusa CORE One L manual.

Preserve error codes, measured values, and the equipment model. Expand log
field names into the matching manual terminology. If no rewrite is needed,
return the original query. Return only the rewritten query.

Dictionary:
{dictionary}

Query:
{question}
""".strip()
    )
    llm = ChatOpenAI(model=QUERY_REWRITE_MODEL, temperature=0)
    return prompt | llm | StrOutputParser()


def rewrite_query(query: str) -> str:
    if not query.strip():
        raise ValueError("query must not be empty")

    return (
        _get_dictionary_chain()
        .invoke({"question": query, "dictionary": "\n".join(KEYWORD_DICTIONARY)})
        .strip()
    )


def search_manual_index(
    query: str,
    equipment_model: str = "PRUSA_CORE_ONE_L",
    k: int = 4,
    use_dictionary: bool = True,
) -> dict[str, Any]:
    if not query.strip():
        raise ValueError("query must not be empty")
    if not 1 <= k <= 10:
        raise ValueError("k must be between 1 and 10")

    rewritten_query = rewrite_query(query) if use_dictionary else query.strip()
    database = _get_database()
    documents = database.similarity_search_with_relevance_scores(
        rewritten_query,
        k=k,
        filter={"equipment_model": equipment_model},
    )

    results = []
    for rank, (document, score) in enumerate(documents, 1):
        metadata = document.metadata
        results.append(
            {
                "rank": rank,
                "score": round(float(score), 6),
                "chunk_id": metadata.get("chunk_id") or getattr(document, "id", None),
                "content": document.page_content,
                "source": metadata.get("source"),
                "page_number": metadata.get("page_number"),
                "chunk_index": metadata.get("chunk_index"),
                "equipment_model": metadata.get("equipment_model"),
                "manual_version": metadata.get("manual_version"),
            }
        )

    return {
        "original_query": query,
        "rewritten_query": rewritten_query,
        "equipment_model": equipment_model,
        "result_count": len(results),
        "results": results,
    }


@mcp.tool()
def search_manual(
    query: str,
    equipment_model: str = "PRUSA_CORE_ONE_L",
    k: int = 4,
    use_dictionary: bool = True,
) -> dict[str, Any]:
    """Search the local equipment manual vector store.

    Args:
        query: Error code, log fields, or observed equipment symptoms.
        equipment_model: Manual metadata filter for the equipment model.
        k: Number of relevant manual chunks to return, from 1 to 10.
        use_dictionary: Rewrite log terminology into manual terminology first.
    """
    return search_manual_index(query, equipment_model, k, use_dictionary)


if __name__ == "__main__":
    mcp.run(transport="stdio")
