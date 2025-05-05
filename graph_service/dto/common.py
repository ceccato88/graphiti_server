from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

class Result(BaseModel):
    message: str
    success: bool

class Message(BaseModel):
    content: str = Field(..., description='The content of the message')  # Conteúdo da mensagem, obrigatório
    uuid: str | None = Field(default=None, description='The uuid of the message (optional)')  # UUID da mensagem, opcional
    name: str = Field(default='', description='The name of the episodic node for the message (optional)')  # Nome da mensagem, opcional
    role_type: Literal['user', 'assistant', 'system'] = Field(..., description='The role type of the message (user, assistant or system)')  # Tipo de papel, obrigatório
    role: str | None = Field(description='The custom role of the message to be used alongside role_type (user name, bot name, etc.)')  # Papel (ex: user, bot), opcional
    timestamp: datetime = Field(..., description='The timestamp of the message (ISO 8601 format)')  # Timestamp agora é obrigatório
    source_description: str = Field(default='', description='The description of the source of the message')  # Descrição da origem da mensagem
