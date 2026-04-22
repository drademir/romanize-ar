"""FastAPI AR→EN romanization microservice.

Pipeline:
  (1) camel-tools MLEDisambiguator → diacritized Arabic  [optional]
  (2) CAMeL ar2phon rule engine → ALA-LC/LOC
  (3) scheme post-process → IJMES/EI3 (or pass-through for ALA-LC)
"""
from __future__ import annotations

import logging
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .disambig import diacritize
from .engine import recompose, translit_simple
from .schemes import apply_scheme

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("romanize-ar")

app = FastAPI(
    title="Romanize-AR",
    description="Arabic → English transliteration (ALA-LC / IJMES / EI3)",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tightened via Traefik/nginx in prod
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

Scheme = Literal["ijmes", "ei3", "ala-lc", "loc", "isnad"]


class RomanizeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10_000)
    scheme: Scheme = "ijmes"
    use_disambig: bool = True


class RomanizeResponse(BaseModel):
    input: str
    output: str
    scheme: str
    disambiguated: bool
    diacritized_input: str | None = None


def _romanize(text: str, scheme: str, use_disambig: bool) -> RomanizeResponse:
    diac: str | None = None
    source = text
    if use_disambig:
        diac = diacritize(text)
        if diac:
            source = diac
    loc_out = translit_simple(source)
    loc_out = recompose(loc_out)
    final = apply_scheme(loc_out, scheme)
    return RomanizeResponse(
        input=text,
        output=final,
        scheme=scheme,
        disambiguated=diac is not None,
        diacritized_input=diac,
    )


@app.get("/", tags=["meta"])
def root() -> dict:
    return {"service": "romanize-ar", "version": "0.1.0", "docs": "/docs"}


@app.get("/health", tags=["meta"])
def health() -> dict:
    from .disambig import _get_disambiguator
    return {
        "status": "ok",
        "disambiguator_loaded": _get_disambiguator() is not None,
    }


@app.get("/api/romanize", response_model=RomanizeResponse, tags=["romanize"])
def romanize_get(
    text: str,
    scheme: Scheme = "ijmes",
    use_disambig: bool = True,
) -> RomanizeResponse:
    if not text.strip():
        raise HTTPException(400, "text cannot be empty")
    return _romanize(text, scheme, use_disambig)


@app.post("/api/romanize", response_model=RomanizeResponse, tags=["romanize"])
def romanize_post(body: RomanizeRequest) -> RomanizeResponse:
    return _romanize(body.text, body.scheme, body.use_disambig)


class BatchRequest(BaseModel):
    items: list[str] = Field(..., max_length=500)
    scheme: Scheme = "ijmes"
    use_disambig: bool = True


class BatchResponse(BaseModel):
    results: list[RomanizeResponse]


@app.post("/api/romanize/batch", response_model=BatchResponse, tags=["romanize"])
def romanize_batch(body: BatchRequest) -> BatchResponse:
    return BatchResponse(
        results=[_romanize(t, body.scheme, body.use_disambig) for t in body.items]
    )
