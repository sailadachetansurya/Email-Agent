from pathlib import Path
import json

from rapidfuzz import process, fuzz

import spacy

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


# ============================================================
# GLOBAL MODELS
# ============================================================

nlp = spacy.load("en_core_web_sm")

embedding_model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)


# ============================================================
# FILE SYSTEM TOOLS
# ============================================================

def fs_exact_match_fetch(
    file_name: str,
    root_dir: str = "."
):
    """
    Input:
        file_name

    Output:
        {
            file_content: str,
            status: SUCCESS | NOT_FOUND | FAILED
        }
    """

    try:
        path = Path(root_dir) / file_name

        if not path.exists():
            return {
                "file_content": "",
                "status": "NOT_FOUND"
            }

        return {
            "file_content": path.read_text(
                encoding="utf-8"
            ),
            "status": "SUCCESS"
        }

    except Exception:
        return {
            "file_content": "",
            "status": "FAILED"
        }


def fs_similarity_fetch(
    query_name: str,
    threshold: float = 70,
    root_dir: str = "."
):
    """
    Input:
        query_name

    Output:
        {
            matched_files_list: list[str],
            status: SUCCESS | FAILED
        }
    """

    try:
        files = [
            p.name
            for p in Path(root_dir).rglob("*")
            if p.is_file()
        ]

        matches = process.extract(
            query_name,
            files,
            scorer=fuzz.ratio,
            score_cutoff=threshold
        )

        return {
            "matched_files_list": [
                match[0]
                for match in matches
            ],
            "status": "SUCCESS"
        }

    except Exception:
        return {
            "matched_files_list": [],
            "status": "FAILED"
        }


def fs_read_block(
    source_path: str,
    chunk_size: int = 4096
):
    """
    Memory efficient file reader.

    Usage:
        for block in fs_read_block(...):
            ...
    """

    with open(
        source_path,
        "r",
        encoding="utf-8"
    ) as f:

        while True:

            block = f.read(chunk_size)

            if not block:
                break

            yield block


def fs_write_document(
    target_path: str,
    payload: str,
    mode: str = "write"
):
    """
    mode:
        write
        append
    """

    try:

        Path(target_path).parent.mkdir(
            parents=True,
            exist_ok=True
        )

        file_mode = "w"

        if mode == "append":
            file_mode = "a"

        with open(
            target_path,
            file_mode,
            encoding="utf-8"
        ) as f:

            f.write(payload)

        return True

    except Exception:
        return False


# ============================================================
# TEXT TOOLS
# ============================================================

def text_chunker_extractor(
    raw_text: str,
    chunk_size: int = 1000
):
    """
    Returns:
        {
            chunks: list[str],
            entities: list[dict]
        }
    """

    doc = nlp(raw_text)

    chunks = []
    current_chunk = ""

    for sent in doc.sents:

        sentence = sent.text.strip()

        if (
            len(current_chunk)
            + len(sentence)
            > chunk_size
        ):

            if current_chunk:
                chunks.append(
                    current_chunk.strip()
                )

            current_chunk = sentence

        else:

            current_chunk += (
                " " + sentence
            )

    if current_chunk.strip():
        chunks.append(
            current_chunk.strip()
        )

    entities = []

    for ent in doc.ents:
        entities.append(
            {
                "text": ent.text,
                "label": ent.label_
            }
        )

    return {
        "chunks": chunks,
        "entities": entities
    }


def text_summarizer_core(
    text: str,
    max_sentences: int = 5
):
    """
    Lightweight extractive summary.
    Replace with LLM later if desired.
    """

    doc = nlp(text)

    sentences = list(doc.sents)

    summary = " ".join(
        s.text.strip()
        for s in sentences[:max_sentences]
    )

    return summary


# ============================================================
# VECTOR GRAPH
# ============================================================

def vector_graph_generator(
    chunks,
    threshold=0.65
):
    """
    Semantic similarity graph.
    """

    embeddings = embedding_model.encode(
        chunks,
        normalize_embeddings=True
    )

    similarity_matrix = cosine_similarity(
        embeddings
    )

    graph = {
        "nodes": [],
        "edges": []
    }

    for idx, chunk in enumerate(chunks):

        graph["nodes"].append(
            {
                "id": idx,
                "text": chunk,
                "embedding":
                    embeddings[idx].tolist()
            }
        )

    for i in range(len(chunks)):

        for j in range(i + 1, len(chunks)):

            score = float(
                similarity_matrix[i][j]
            )

            if score >= threshold:

                graph["edges"].append(
                    {
                        "source": i,
                        "target": j,
                        "weight": round(
                            score,
                            4
                        )
                    }
                )

    return graph


# ============================================================
# KNOWLEDGE BASE STORAGE
# ============================================================

def kb_storage_writer(
    summary: str,
    graph_data: dict,
    storage_destination: str
):
    """
    Saves summary + graph.
    """

    try:

        payload = {
            "summary": summary,
            "graph": graph_data
        }

        Path(
            storage_destination
        ).parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            storage_destination,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                payload,
                f,
                indent=2,
                ensure_ascii=False
            )

        return True

    except Exception:
        return False


# ============================================================
# EXAMPLE PIPELINE
# ============================================================

if __name__ == "__main__":

    result = fs_exact_match_fetch(
        "sample.txt"
    )

    if result["status"] == "SUCCESS":

        text = result["file_content"]

        parsed = text_chunker_extractor(
            text,
            chunk_size=1000
        )

        chunks = parsed["chunks"]

        summary = text_summarizer_core(
            text
        )

        graph = vector_graph_generator(
            chunks
        )

        kb_storage_writer(
            summary,
            graph,
            "kb/sample.json"
        )

        print("Done")