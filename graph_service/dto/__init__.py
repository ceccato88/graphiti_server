# Importando classes e funções de outros módulos do projeto

# Importando os DTOs de mensagens e resultados, usados em diversas partes do código
from .common import Message, Result  

# Importando os DTOs relacionados ao processo de ingestão de episódios (texto, conversa, documento)
from .ingest import (
    AddTextEpisodeRequest,  # DTO para adicionar um episódio de texto
    AddConversationEpisodeRequest,  # DTO para adicionar um episódio de conversa
    AddDocumentRequest,  # Novo import para adicionar documentos como episódios
)

# Importando os DTOs relacionados à pesquisa e seus resultados
from .retrieve import (
    FactResult,  # Representa os resultados de um fato encontrado em uma pesquisa
    SearchQuery,  # DTO para uma consulta de pesquisa simples
    CenteredSearchQuery,  # DTO para pesquisa centrada em um nó específico
    AdvancedSearchRequest,  # DTO para pesquisa avançada com receitas de EDGE
    AdvancedSearchV2Request,  # DTO para pesquisa avançada com receitas COMBINADAS (EDGE + NODE)
    SearchResults,  # Representa os resultados de uma pesquisa (fatos encontrados)
    AdvancedSearchV2Response,  # Representa a resposta para a pesquisa avançada v2 (contém fatos e nós)
    NodeResult,  # Representa os resultados de nós encontrados em uma pesquisa avançada v2
)

# __all__ define o que será exposto ao importar este módulo
# Todos os elementos listados aqui poderão ser acessados diretamente ao importar o módulo
__all__ = [
    'SearchQuery',  # Expondo o DTO SearchQuery para pesquisas simples
    'CenteredSearchQuery',  # Expondo o DTO para pesquisa centrada em um nó
    'AdvancedSearchRequest',  # Expondo o DTO para pesquisa avançada com receitas de EDGE
    'AdvancedSearchV2Request',  # Expondo o DTO para pesquisa avançada com receitas COMBINADAS (EDGE + NODE)
    'Message',  # Expondo o DTO Message, usado nas mensagens de conversa
    'AddTextEpisodeRequest',  # Expondo o DTO para adicionar episódio de texto
    'AddConversationEpisodeRequest',  # Expondo o DTO para adicionar episódio de conversa
    'AddDocumentRequest',  # Expondo o DTO para adicionar documentos como episódios
    'SearchResults',  # Expondo o DTO que representa os resultados da pesquisa (fatos encontrados)
    'FactResult',  # Expondo o DTO que representa os fatos encontrados em uma pesquisa
    'Result',  # Expondo o DTO para resultados gerais, como resposta de sucesso
    'AdvancedSearchV2Response',  # Expondo o DTO de resposta para a pesquisa avançada v2 (fatos e nós)
    'NodeResult',  # Expondo o DTO para nós encontrados na pesquisa avançada v2
]
