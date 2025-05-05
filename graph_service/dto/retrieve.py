from datetime import datetime, timezone  # Importando datetime para trabalhar com data e hora, incluindo conversões de fuso horário
from typing import Literal  # Literal é usado para restringir valores possíveis para um campo (como uma lista de strings fixas)

from pydantic import BaseModel, Field  # BaseModel e Field são usados para criar classes de modelos de dados validados

# DTO para realizar uma pesquisa simples (não centrada em nenhum nó específico)
class SearchQuery(BaseModel):
    group_ids: list[str] | None = Field(
        None, description='The group ids for the memories to search'  # IDs dos grupos (memórias) para filtrar a pesquisa
    )
    query: str  # A consulta de pesquisa (termo ou frase)
    max_facts: int = Field(default=10, description='The maximum number of facts to retrieve')  # O número máximo de fatos a serem retornados

# DTO para realizar uma pesquisa centrada em um nó específico (utiliza o campo `center_node_uuid` para foco)
class CenteredSearchQuery(SearchQuery):
    center_node_uuid: str = Field(..., description='The UUID of the focal node for graph-based reranking')  # UUID do nó central, usado para reranqueamento

# DTO para representar o resultado de um fato, com informações sobre validade e criação
class FactResult(BaseModel):
    uuid: str  # Identificador único do fato
    name: str  # Nome do fato
    fact: str  # O fato em si, como uma string
    valid_at: datetime | None  # Data e hora em que o fato foi validado, caso tenha
    invalid_at: datetime | None  # Data e hora em que o fato foi invalidado, caso tenha
    created_at: datetime  # Data e hora de criação do fato
    expired_at: datetime | None  # Data de expiração do fato, caso tenha

    class Config:
        json_encoders = {datetime: lambda v: v.astimezone(timezone.utc).isoformat()}  # Converte objetos datetime para formato ISO 8601 com fuso horário UTC

# DTO para a resposta de uma pesquisa, contendo uma lista de `FactResult`
class SearchResults(BaseModel):
    facts: list[FactResult]  # Lista de fatos encontrados

# DTO para a rota `advanced_search` (pesquisa avançada, apenas com receitas de tipo EDGE)
class AdvancedSearchRequest(BaseModel):
    query: str = Field(..., description="The search query to execute")  # A consulta de pesquisa
    max_facts: int = Field(default=10, description="Maximum number of facts to retrieve")  # O número máximo de fatos a serem retornados
    group_ids: list[str] | None = Field(
        None, description="Group IDs (namespaces) to search in"  # IDs dos grupos (namespace) para filtrar a pesquisa
    )
    # Limita a pesquisa a apenas as receitas de EDGE
    recipe: Literal[
        'EDGE_HYBRID_SEARCH_RRF',
        'EDGE_HYBRID_SEARCH_MMR',
        'EDGE_HYBRID_SEARCH_NODE_DISTANCE',
        'EDGE_HYBRID_SEARCH_EPISODE_MENTIONS',
        'EDGE_HYBRID_SEARCH_CROSS_ENCODER'
    ] = Field(..., description="Predefined search configuration (SearchConfig recipe)")  # Receita de pesquisa específica para EDGE

# DTO para a rota `advanced_search_v2` (pesquisa avançada, apenas com receitas COMBINED, que envolvem tanto EDGE quanto NODE)
class AdvancedSearchV2Request(BaseModel):
    query: str = Field(..., description="The search query to execute")  # A consulta de pesquisa
    max_facts: int = Field(default=10, description="Maximum number of facts to retrieve")  # O número máximo de fatos a serem retornados
    group_ids: list[str] | None = Field(
        None, description="Group IDs (namespaces) to search in"  # IDs dos grupos (namespace) para filtrar a pesquisa
    )
    # Limita a pesquisa a apenas as receitas COMBINED, que envolvem tanto EDGE quanto NODE
    recipe: Literal[
        'COMBINED_HYBRID_SEARCH_RRF',
        'COMBINED_HYBRID_SEARCH_MMR',
        'COMBINED_HYBRID_SEARCH_CROSS_ENCODER'
    ] = Field(..., description="Predefined search configuration (SearchConfig recipe)")  # Receita de pesquisa combinada (EDGE + NODE)

# DTO para representar um nó (com atributos e rótulos)
class NodeResult(BaseModel):
    uuid: str  # Identificador único do nó
    name: str  # Nome do nó
    summary: str | None  # Resumo opcional do nó
    labels: list[str]  # Lista de rótulos (tags) associadas ao nó
    created_at: datetime  # Data e hora de criação do nó
    attributes: dict[str, str] | None = None  # Atributos adicionais do nó, opcional

# DTO para a resposta de uma pesquisa avançada v2, contendo tanto fatos quanto nós
class AdvancedSearchV2Response(BaseModel):
    facts: list[FactResult]  # Lista de fatos encontrados
    nodes: list[NodeResult]  # Lista de nós encontrados
