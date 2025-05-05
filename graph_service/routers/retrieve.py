from datetime import datetime, timezone  # Para trabalhar com data e hora, incluindo fusos horários
from typing import Optional  # Para utilizar tipos opcionais (como campos que podem ser None)

# Importando as dependências do FastAPI para criação de rotas
from fastapi import APIRouter, status, Depends, Header, HTTPException  # FastAPI para criação das rotas da API

# Importando os DTOs necessários para as consultas e respostas da API
from pydantic import BaseModel, Field  # Pydantic para a criação de modelos de dados e validações

from graph_service.dto import (
    SearchQuery,  # DTO para uma consulta simples
    CenteredSearchQuery,  # DTO para uma consulta centrada em um nó
    SearchResults,  # DTO para os resultados de uma pesquisa
    AdvancedSearchRequest,  # DTO para busca avançada com receitas de EDGE
    AdvancedSearchV2Request,  # DTO para busca avançada com receitas COMBINADAS (EDGE + NODE)
    AdvancedSearchV2Response,  # Resposta para busca avançada com receitas COMBINADAS
    FactResult,  # DTO para representar os fatos encontrados em uma pesquisa
    NodeResult,  # DTO para representar os nós encontrados em uma pesquisa avançada v2
)
from graph_service.zep_graphiti import ZepGraphitiDep, get_fact_result_from_edge  # Dependência para interação com Graphiti
from graphiti_core.search import search_config_recipes  # Importando as receitas de busca configuradas

# === Auth ===
import os  # Para acessar variáveis de ambiente (como o token da API)

# Obtendo o token da API a partir da variável de ambiente
api_token = os.getenv("API_TOKEN")

# Função para verificar o token de autenticação nas requisições
def verify_token(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):  # Verifica se o token foi enviado no cabeçalho
        raise HTTPException(status_code=401, detail="Token ausente ou inválido.")  # Se não, lança erro 401
    token = authorization.split(" ")[1]  # Extrai o token do cabeçalho 'Bearer {token}'
    if token != api_token:  # Verifica se o token corresponde ao token esperado
        raise HTTPException(status_code=403, detail="Token não autorizado.")  # Se não, lança erro 403

# === Router ===
# Criando o roteador para as rotas da API, incluindo a verificação de token em todas as rotas
router = APIRouter(
    prefix="/retrieve",  # Prefixo para todas as rotas desta API
    dependencies=[Depends(verify_token)],  # Aplica a verificação do token em todas as rotas
)

# Rota para realizar uma busca avançada (somente receitas de EDGE)
@router.post('/search/advanced', status_code=status.HTTP_200_OK)
async def advanced_search(query: AdvancedSearchRequest, graphiti: ZepGraphitiDep):
    config = getattr(search_config_recipes, query.recipe)  # Obtém a configuração de pesquisa com base na receita fornecida
    results = await graphiti._search(
        query=query.query,  # A consulta de pesquisa
        group_ids=query.group_ids,  # IDs dos grupos (opcional para filtrar a pesquisa)
        config=config,  # Configuração da pesquisa
    )
    facts = [get_fact_result_from_edge(edge) for edge in results.edges]  # Obtém os resultados dos fatos
    return SearchResults(facts=facts)  # Retorna os resultados encontrados

# Rota para realizar uma busca avançada v2 (somente receitas COMBINADAS - EDGE + NODE)
@router.post('/search/advanced-v2', status_code=status.HTTP_200_OK)
async def advanced_search_v2(query: AdvancedSearchV2Request, graphiti: ZepGraphitiDep):  # Recebe a nova estrutura de pesquisa v2
    config = getattr(search_config_recipes, query.recipe).model_copy(deep=True)  # Cria uma cópia da configuração para a pesquisa
    config.limit = query.max_facts  # Limita a quantidade de fatos retornados

    results = await graphiti._search(
        query=query.query,  # A consulta de pesquisa
        group_ids=query.group_ids,  # IDs dos grupos (opcional)
        config=config,  # Configuração da pesquisa
    )

    # Obtém os fatos a partir dos resultados das arestas
    facts = [get_fact_result_from_edge(edge) for edge in results.edges]
    # Obtém os nós dos resultados e cria uma lista de NodeResult
    nodes = [
        NodeResult(
            uuid=node.uuid,  # ID único do nó
            name=node.name,  # Nome do nó
            summary=node.summary,  # Resumo opcional do nó
            created_at=node.created_at,  # Data de criação do nó
            labels=list(node.labels) if isinstance(node.labels, (list, tuple)) else [],  # Rótulos do nó
            attributes={  # Atributos adicionais do nó, se existirem
                k: str(v) for k, v in (node.attributes or {}).items()
            } if hasattr(node, "attributes") and node.attributes else None,
        )
        for node in results.nodes  # Itera sobre todos os nós encontrados
    ]
    return AdvancedSearchV2Response(facts=facts, nodes=nodes)  # Retorna tanto os fatos quanto os nós encontrados

# Rota para realizar uma busca normal (simples) sem foco em receitas avançadas
@router.post('/search', status_code=status.HTTP_200_OK)
async def search(query: SearchQuery, graphiti: ZepGraphitiDep):
    relevant_edges = await graphiti.search(
        group_ids=query.group_ids,  # IDs dos grupos (opcional)
        query=query.query,  # A consulta de pesquisa
        num_results=query.max_facts,  # O número máximo de resultados a serem retornados
    )
    facts = [get_fact_result_from_edge(edge) for edge in relevant_edges]  # Obtém os fatos dos resultados das arestas
    return SearchResults(facts=facts)  # Retorna os fatos encontrados

# Rota para realizar uma busca centrada em um nó específico (para reranqueamento)
@router.post('/search/centered', status_code=status.HTTP_200_OK)
async def search_centered(
    query: CenteredSearchQuery,  # A consulta centrada em um nó específico
    graphiti: ZepGraphitiDep,  # Dependência do Graphiti
):
    results = await graphiti.search(
        query=query.query,  # A consulta de pesquisa
        group_ids=query.group_ids,  # IDs dos grupos (opcional)
        num_results=query.max_facts,  # O número máximo de resultados a serem retornados
        center_node_uuid=query.center_node_uuid,  # O UUID do nó central para reranqueamento
    )
    facts = [get_fact_result_from_edge(edge) for edge in results]  # Obtém os fatos das arestas dos resultados
    return SearchResults(facts=facts)  # Retorna os resultados encontrados

# Rota para obter episódios de um determinado grupo
@router.get('/episodes/{group_id}', status_code=status.HTTP_200_OK)
async def get_episodes(group_id: str, last_n: int, graphiti: ZepGraphitiDep):
    # Recupera episódios com base no ID do grupo e no número de episódios solicitados
    episodes = await graphiti.retrieve_episodes(
        group_ids=[group_id],  # IDs dos grupos
        last_n=last_n,  # Número de episódios a serem recuperados
        reference_time=datetime.now(timezone.utc),  # Marca temporal atual (em UTC)
    )
    return episodes  # Retorna os episódios encontrados
