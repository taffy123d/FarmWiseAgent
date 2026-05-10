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

# Monkey-patch: include reasoning_content in API requests for multi-turn conversations.
# DeepSeek requires reasoning_content from previous assistant messages to be passed back,
# but BaseChatOpenAI._convert_message_to_dict does not include it.
_original_get_request_payload = chat_model._get_request_payload

def _patched_get_request_payload(self, input_, *, stop=None, **kwargs):
    payload = _original_get_request_payload(input_, stop=stop, **kwargs)
    if hasattr(input_, '__iter__') and not isinstance(input_, (str, dict)):
        payload_msgs = payload.get("messages", [])
        for i, msg in enumerate(input_):
            if (hasattr(msg, 'additional_kwargs')
                    and msg.additional_kwargs.get("reasoning_content")
                    and i < len(payload_msgs)
                    and payload_msgs[i].get("role") == "assistant"):
                payload_msgs[i]["reasoning_content"] = msg.additional_kwargs["reasoning_content"]
    return payload

chat_model._get_request_payload = _patched_get_request_payload.__get__(chat_model, type(chat_model))