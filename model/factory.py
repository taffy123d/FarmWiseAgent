from abc import ABC,abstractmethod
from typing import Optional
from langchain_core.embeddings import Embeddings
from langchain.chat_models import BaseChatModel
from utils.config_handler import rag_conf
from langchain.chat_models import init_chat_model
from langchain_community.embeddings import DashScopeEmbeddings

from dotenv import load_dotenv
load_dotenv()
import os


class BaseModelFactory(ABC):
  @abstractmethod
  def generator(self) -> Optional[Embeddings | BaseChatModel]:
    pass

class ChatModelFactory(BaseModelFactory):
  def generator(self) -> Optional[Embeddings | BaseChatModel]:
    return init_chat_model(model = rag_conf['chat_model_name'])

class EmbeddingsFactory(BaseModelFactory):
  def generator(self) -> Optional[Embeddings | BaseChatModel]:
    return DashScopeEmbeddings(model=rag_conf['embedding_model_name'])

  

chat_model = ChatModelFactory().generator()
embedding_model = EmbeddingsFactory().generator()