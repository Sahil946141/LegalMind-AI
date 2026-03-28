from pathlib import Path
import logging
from langchain_community.document_loaders import PyPDFLoader, UnstructuredWordDocumentLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("ingest")


def load_document(file_path: str):
    path = Path(file_path)
    if not path.exists():
        log.warning(f"[LOAD] file not found: {file_path}")
        return []

    if path.suffix.lower() == ".pdf":
        docs = PyPDFLoader(str(path)).load()
    elif path.suffix.lower() in [".docx", ".doc"]:
        docs = UnstructuredWordDocumentLoader(str(path)).load()
    else:
        log.warning(f"[LOAD] unsupported type: {path.suffix}")
        return []

    for d in docs:
        d.metadata["filename"] = path.name

    log.info(f"[LOAD] loaded_pages/docs={len(docs)} filename={path.name}")
    return docs


def chunk_documents(docs, chunk_size: int = 850, chunk_overlap: int = 120):
    """
    Splits docs into chunks with GLOBAL stable chunk_index.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ".", " "],
    )

    chunks = []
    chunk_counter = 0

    for doc in docs:
        parts = splitter.split_documents([doc])
        for ch in parts:
            ch.metadata["chunk_index"] = chunk_counter
            chunk_counter += 1
        chunks.extend(parts)

    log.info(f"[CHUNK] produced_chunks={len(chunks)} chunk_size={chunk_size} overlap={chunk_overlap}")
    return chunks