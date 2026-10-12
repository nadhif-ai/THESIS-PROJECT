"""Versioned character chunking for draft knowledge; historical vectors stay intact."""

import re
from functools import lru_cache

from langchain_core.documents import Document
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)
from pydantic import BaseModel, Field, model_validator
from transformers import AutoTokenizer


class Chunking(BaseModel):
    chunk_size: int = Field(default=1000, ge=400, le=2000)
    chunk_overlap: int = Field(default=100, ge=0, le=400)

    @model_validator(mode="after")
    def overlap_fits(self):
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("Overlap must be smaller than chunk size.")
        return self


LEGACY = {"chunk_size": 1500, "chunk_overlap": 200, "preprocessing": "legacy"}
SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


@lru_cache(maxsize=1)
def tokenizer():
    return AutoTokenizer.from_pretrained(
        "intfloat/multilingual-e5-small", local_files_only=True
    )


def split_document(document, config):
    # Separator-only passages are not business knowledge. Preserve actual prices and units.
    text = re.sub(r"(?m)^[ \t]*[-_*]{3,}[ \t]*$", "", document.page_content)
    sections = MarkdownHeaderTextSplitter(
        headers_to_split_on=[
            ("#", "section_1"),
            ("##", "section_2"),
            ("###", "section_3"),
        ],
        strip_headers=True,
    ).split_text(text)
    result = []
    for section in sections:
        if not any(character.isalnum() for character in section.page_content):
            continue
        headings = [
            section.metadata[key]
            for key in ("section_1", "section_2", "section_3")
            if key in section.metadata
        ]
        prefix = " > ".join(headings)
        prefix = prefix + "\n\n" if prefix else ""
        budget = config.chunk_size - len(prefix)
        if budget <= config.chunk_overlap:
            raise ValueError(
                "A section heading is too long for this chunk configuration."
            )
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=budget,
            chunk_overlap=config.chunk_overlap,
            separators=SEPARATORS,
        )
        for body in splitter.split_text(section.page_content):
            if any(character.isalnum() for character in body):
                result.append(
                    Document(
                        page_content=prefix + body,
                        metadata=dict(document.metadata, **section.metadata),
                    )
                )
    return result


def token_statistics(documents):
    lengths = [
        len(tokenizer().encode("passage: " + doc.page_content, truncation=False))
        for doc in documents
    ]
    return {
        "embedding_token_limit": 512,
        "max_tokens": max(lengths, default=0),
        "over_limit": sum(length > 512 for length in lengths),
    }
