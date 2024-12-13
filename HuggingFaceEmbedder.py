from typing import Iterable, List
from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType
from graphiti_core.embedder.client import EmbedderClient, EmbedderConfig
from datetime import datetime
from sentence_transformers import SentenceTransformer, util

DEFAULT_EMBEDDING_MODEL = 'dunzhang/stella_en_1.5B_v5'


class HuggingFaceEmbedderConfig(EmbedderConfig):
    # embedding_model: EmbeddingModel | str = DEFAULT_EMBEDDING_MODEL
    embedding_model: str = DEFAULT_EMBEDDING_MODEL
    api_key: str | None = None
    base_url: str | None = None


class HuggingFaceEmbedder(EmbedderClient):
    """
    HuggingFace Embedder Client
    """

    def __init__(self, config: HuggingFaceEmbedderConfig | None = None):
        if config is None:
            config = HuggingFaceEmbedderConfig()
        self.config = config
        self.model = SentenceTransformer( config.embedding_model )
        #self.client = AsyncOpenAI(api_key=config.api_key, base_url=config.base_url)

    async def create(
            self, input: str | List[str] | Iterable[int] | Iterable[Iterable[int]]
    ) -> list[float]:
        print( f'embbed this: {input}' )
        embeddings = self.model.encode( input )
        print( f'type of embbeding: {type(embeddings)}' )
        print( f'type of embbeding shape: {type(embeddings.shape)}' )
        print( f'embbeding to return: {embeddings.shape}' )
        return embeddings.shape
        #return self.model.encode( input ).shape
        # result = await self.client.embeddings.create(input=input, model=self.config.embedding_model)
        # return result.data[0].embedding[: self.config.embedding_dim]

