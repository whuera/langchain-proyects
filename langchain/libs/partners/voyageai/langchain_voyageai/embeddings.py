import logging
from typing import Iterable, List, Optional

import voyageai  # type: ignore
from langchain_core.embeddings import Embeddings
from langchain_core.pydantic_v1 import (
    BaseModel,
    Field,
    SecretStr,
    root_validator,
)
from langchain_core.utils import secret_from_env

logger = logging.getLogger(__name__)


class VoyageAIEmbeddings(BaseModel, Embeddings):
    """VoyageAIEmbeddings embedding model.

    Example:
        .. code-block:: python

            from langchain_voyageai import VoyageAIEmbeddings

            model = VoyageAIEmbeddings()
    """

    _client: voyageai.Client = Field(exclude=True)
    _aclient: voyageai.client_async.AsyncClient = Field(exclude=True)
    model: str
    batch_size: int
    show_progress_bar: bool = False
    truncation: Optional[bool] = None
    voyage_api_key: SecretStr = Field(
        alias="api_key",
        default_factory=secret_from_env(
            "VOYAGE_API_KEY",
            error_message="Must set `VOYAGE_API_KEY` environment variable or "
            "pass `api_key` to VoyageAIEmbeddings constructor.",
        ),
    )

    class Config:
        extra = "forbid"
        allow_population_by_field_name = True

    @root_validator(pre=True)
    def default_values(cls, values: dict) -> dict:
        """Set default batch size based on model"""
        model = values.get("model")
        batch_size = values.get("batch_size")
        if batch_size is None:
            values["batch_size"] = 72 if model in ["voyage-2", "voyage-02"] else 7
        return values

    @root_validator(pre=False, skip_on_failure=True)
    def validate_environment(cls, values: dict) -> dict:
        """Validate that VoyageAI credentials exist in environment."""
        api_key_str = values["voyage_api_key"].get_secret_value()
        values["_client"] = voyageai.Client(api_key=api_key_str)
        values["_aclient"] = voyageai.client_async.AsyncClient(api_key=api_key_str)
        return values

    def _get_batch_iterator(self, texts: List[str]) -> Iterable:
        if self.show_progress_bar:
            try:
                from tqdm.auto import tqdm  # type: ignore
            except ImportError as e:
                raise ImportError(
                    "Must have tqdm installed if `show_progress_bar` is set to True. "
                    "Please install with `pip install tqdm`."
                ) from e

            _iter = tqdm(range(0, len(texts), self.batch_size))
        else:
            _iter = range(0, len(texts), self.batch_size)  # type: ignore

        return _iter

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed search docs."""
        embeddings: List[List[float]] = []

        _iter = self._get_batch_iterator(texts)
        for i in _iter:
            embeddings.extend(
                self._client.embed(
                    texts[i : i + self.batch_size],
                    model=self.model,
                    input_type="document",
                    truncation=self.truncation,
                ).embeddings
            )

        return embeddings

    def embed_query(self, text: str) -> List[float]:
        """Embed query text."""
        return self._client.embed(
            [text], model=self.model, input_type="query", truncation=self.truncation
        ).embeddings[0]

    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings: List[List[float]] = []

        _iter = self._get_batch_iterator(texts)
        for i in _iter:
            r = await self._aclient.embed(
                texts[i : i + self.batch_size],
                model=self.model,
                input_type="document",
                truncation=self.truncation,
            )
            embeddings.extend(r.embeddings)

        return embeddings

    async def aembed_query(self, text: str) -> List[float]:
        r = await self._aclient.embed(
            [text],
            model=self.model,
            input_type="query",
            truncation=self.truncation,
        )
        return r.embeddings[0]
