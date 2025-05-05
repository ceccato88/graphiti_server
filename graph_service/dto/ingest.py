from pydantic import BaseModel, Field  # Importando BaseModel e Field do Pydantic para definir os DTOs (Data Transfer Objects)
from datetime import datetime  # Importando datetime para trabalhar com datas e horas

from graph_service.dto.common import Message  # Importando o DTO Message, que provavelmente é utilizado para a estrutura de mensagem

# DTO para adicionar um episódio de texto
class AddTextEpisodeRequest(BaseModel):
    group_id: str = Field(..., description='The group id of the episode')  # ID do grupo ao qual o episódio pertence
    name: str = Field(..., description='The name of the episode')  # Nome do episódio
    content: str = Field(..., description='The textual content to add')  # Conteúdo do episódio (texto)
    source_description: str = Field(default='Text content', description='Description of the content source')  # Descrição da origem do conteúdo
    reference_time: datetime = Field(..., description='Reference timestamp for the episode')  # Marca temporal para o episódio (data e hora)

# DTO para adicionar um episódio de conversa
class AddConversationEpisodeRequest(BaseModel):
    group_id: str = Field(..., description='The group id of the conversation episode')
    name: str = Field(..., description='The name of the episode')
    messages: list[Message] = Field(..., description='The list of messages in the conversation')
    source_description: str = Field(default='Conversation', description='Description of the source')
    reference_time: datetime = Field(..., description='Reference timestamp for the episode')
    
# DTO para adicionar um episódio de documento
class AddDocumentRequest(BaseModel):
    group_id: str = Field(..., description='The group id of the document')  # ID do grupo ao qual o documento pertence
    name: str = Field(..., description='The base name of the document (used for each part)')  # Nome base do documento (utilizado para cada parte)
    content: str = Field(..., description='The full textual content of the document')  # Conteúdo completo do documento
    source_description: str = Field(default='Document ingestion', description='Description of the document source')  # Descrição da origem do documento
    reference_time: datetime = Field(..., description='Timestamp for the document ingestion')  # Marca temporal para a ingestão do documento (data e hora)
