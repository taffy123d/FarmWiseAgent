"""
总结服务 用户提问 搜索参考资料
将提问和参考资料提交给模型 让模型总结回复
"""
from rag.vector_store import VectorStoreService
from utils.prompt_loader import load_rag_prompts
from langchain_core.prompts import PromptTemplate
from model.factory import chat_model
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document

class RagSummarizeService(object):
  def __init__(self):
    self.vector_store = VectorStoreService()
    self.retriever = self.vector_store.get_retriver()
    self.prompt_text = load_rag_prompts()
    self.prompt_template = PromptTemplate.from_template(self.prompt_text)
    self.model = chat_model
    self.chain = self._init_chain()

  def _init_chain(self):
    return (self.prompt_template | self.model | StrOutputParser())
  
  def retriever_docs(self,query:str) -> list[Document]:
    return self.retriever.invoke(query)
  
  def rag_summarize(self,query:str) -> str:
    context_docs = self.retriever_docs(query)
    context = ''
    cnt = 0
    for doc in context_docs :
      cnt+=1
      # context += f'[参考资料{cnt}](参考元数据:{doc.metadata}):\n {doc.page_content}\n'
      context += f'[参考资料{cnt}]:\n {doc.page_content}\n'
    return self.chain.invoke(
        {
          'input':query,
          'context':context
        }
      )
    

if __name__ == '__main__':
  rags = RagSummarizeService()
  s = rags.rag_summarize('华南地区5月播种小麦 建议 气候要求 广州')
  print(s)