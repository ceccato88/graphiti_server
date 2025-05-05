import asyncio  # Para operações assíncronas e gerenciamento de tarefas paralelas
import os  # Para acessar variáveis de ambiente, como o token da API
from datetime import datetime  # Para manipulação de data e hora, como a marcação de tempo para os episódios
from contextlib import asynccontextmanager  # Para criar um gerenciador de contexto assíncrono
from typing import Optional  # Para definir tipos opcionais

# Importações do FastAPI e outras dependências
from fastapi import APIRouter, FastAPI, Depends, Header, HTTPException, status  # FastAPI e dependências para criar rotas e manipular cabeçalhos HTTP
from graphiti_core.nodes import EpisodeType  # Define os tipos de episódio (ex: mensagens, texto, etc.) no Graphiti
from graphiti_core.utils.maintenance.graph_data_operations import clear_data  # Função para limpar dados no Graphiti

# Importando DTOs (Data Transfer Objects) para validação dos dados de entrada
from graph_service.dto import (
    AddTextEpisodeRequest,  # DTO para adicionar episódio de texto
    AddConversationEpisodeRequest,  # DTO para adicionar episódio de conversa
    AddDocumentRequest,  # Novo DTO para adicionar documentos
    Result,  # Classe para formatar a resposta da API
)
from graph_service.zep_graphiti import ZepGraphitiDep  # Dependência para interação com o Graphiti (provavelmente o driver da base de dados)

# === Autenticação ===
api_token = os.getenv("API_TOKEN")  # Obtendo o token da API a partir das variáveis de ambiente

def verify_token(authorization: Optional[str] = Header(None)):  # Função para verificar o token de autenticação nas requisições
    if not authorization or not authorization.startswith("Bearer "):  # Verifica se o cabeçalho contém o token
        raise HTTPException(status_code=401, detail="Token ausente ou inválido.")  # Se não estiver presente ou válido, lança erro 401
    token = authorization.split(" ")[1]  # Extrai o token do cabeçalho 'Bearer {token}'
    if token != api_token:  # Verifica se o token fornecido corresponde ao token esperado
        raise HTTPException(status_code=403, detail="Token não autorizado.")  # Se o token não for válido, lança erro 403

# === Worker Assíncrono ===
class AsyncWorker:  # Classe que gerencia tarefas assíncronas em segundo plano (para processamento em background)
    def __init__(self):  # Inicializa a classe
        self.queue = asyncio.Queue()  # Fila assíncrona para armazenar tarefas
        self.task = None  # Inicializa a variável task, que armazenará a tarefa em segundo plano

    async def worker(self):  # Função do worker para processar as tarefas da fila
        while True:  # Enquanto o worker estiver rodando
            try:
                job = await self.queue.get()  # Pega a próxima tarefa da fila
                await job()  # Executa a tarefa
            except asyncio.CancelledError:  # Caso o worker seja cancelado
                break  # Encerra o loop

    async def start(self):  # Função para iniciar o worker
        self.task = asyncio.create_task(self.worker())  # Cria e inicia a tarefa assíncrona

    async def stop(self):  # Função para parar o worker
        if self.task:  # Verifica se o worker está rodando
            self.task.cancel()  # Cancela a tarefa
            await self.task  # Aguarda a finalização da tarefa
        while not self.queue.empty():  # Enquanto a fila não estiver vazia
            self.queue.get_nowait()  # Remove todas as tarefas restantes da fila sem executá-las

async_worker = AsyncWorker()  # Criação de uma instância do worker assíncrono

@asynccontextmanager  # Gerenciador de contexto assíncrono, utilizado para garantir que o worker seja iniciado e parado corretamente
async def lifespan(_: FastAPI):  # Função que será usada para iniciar o worker no início e parar no final
    await async_worker.start()  # Inicia o worker
    yield  # Permite que a aplicação FastAPI seja executada enquanto o worker estiver ativo
    await async_worker.stop()  # Para o worker quando a aplicação for finalizada

# === Definição das Rotas da API (FastAPI Router) ===
router = APIRouter(  # Criação de um router para organizar as rotas da API
    lifespan=lifespan,  # A função de gerenciamento de contexto será aplicada aqui
    dependencies=[Depends(verify_token)]  # Aplica a verificação de token em todas as rotas
)

# Rota para adicionar um episódio de conversa
@router.post('/conversation', status_code=status.HTTP_201_CREATED)
async def add_conversation(request: AddConversationEpisodeRequest, graphiti: ZepGraphitiDep):
    # Converte a lista de mensagens da conversa em um formato string, incluindo o timestamp
    conversation_text = "\n".join(
        f"{m.role}({m.role_type}): {m.content} (Timestamp: {m.timestamp.isoformat()})"  # Agora cada mensagem inclui o timestamp
        for m in request.messages  # Itera sobre cada mensagem para formatar a string
    )
    
    # Adiciona o episódio ao Graphiti
    await graphiti.add_episode(
        name=request.name,
        episode_body=conversation_text,
        source=EpisodeType.message,
        source_description=request.source_description,
        reference_time=request.reference_time,
        group_id=request.group_id,
    )

    # Retorna uma resposta de sucesso
    return Result(message='Conversation episode added successfully', success=True)  
# Rota para adicionar um episódio de texto
@router.post('/text', status_code=status.HTTP_201_CREATED)
async def add_text_episode(request: AddTextEpisodeRequest, graphiti: ZepGraphitiDep):
    await graphiti.add_episode(  # Adiciona o episódio ao Graphiti
        name=request.name,
        episode_body=request.content,  # O corpo do episódio é o conteúdo de texto
        source=EpisodeType.text,  # Define que o episódio é do tipo "text"
        source_description=request.source_description,  # Descrição da fonte
        reference_time=request.reference_time,  # Tempo de referência para o episódio
        group_id=request.group_id,  # ID do grupo
    )
    return Result(message='Text episode added successfully', success=True)  # Retorna uma resposta de sucesso

# Rota para adicionar um episódio de documento
@router.post('/document', status_code=status.HTTP_201_CREATED)
async def add_document(request: AddDocumentRequest, graphiti: ZepGraphitiDep):
    def dividir_em_partes(texto: str, limite: int = 5000) -> list[str]:  # Função para dividir o documento em partes menores
        return [texto[i:i + limite] for i in range(0, len(texto), limite)]  # Divide o texto em partes de no máximo 5000 caracteres

    partes = dividir_em_partes(request.content)  # Divide o conteúdo do documento em partes

    for i, parte in enumerate(partes):  # Para cada parte do documento
        await graphiti.add_episode(  # Adiciona cada parte como um episódio
            name=f'{request.name} - Parte {i + 1}',  # Nome do episódio com o número da parte
            episode_body=parte,  # Corpo do episódio é o conteúdo da parte
            source=EpisodeType.text,  # Define que o episódio é do tipo "text"
            source_description=request.source_description,  # Descrição da fonte
            reference_time=request.reference_time,  # Tempo de referência para o episódio
            group_id=request.group_id,  # ID do grupo
        )

    return Result(  # Retorna uma resposta de sucesso
        message=f'{len(partes)} partes do documento adicionadas com sucesso ao grupo {request.group_id}.',
        success=True,
    )

# Rota para deletar um grupo
@router.delete('/group/{group_id}', status_code=status.HTTP_200_OK)
async def delete_group(group_id: str, graphiti: ZepGraphitiDep):
    await graphiti.delete_group(group_id)  # Deleta o grupo do Graphiti
    return Result(message='Group deleted', success=True)  # Retorna uma resposta de sucesso

# Rota para limpar os dados
@router.post('/clear', status_code=status.HTTP_200_OK)
async def clear(graphiti: ZepGraphitiDep):
    await clear_data(graphiti.driver)  # Limpa os dados do Graphiti
    await graphiti.build_indices_and_constraints()  # Reconstrói os índices e restrições no Graphiti
    return Result(message='Graph cleared', success=True)  # Retorna uma resposta de sucesso
