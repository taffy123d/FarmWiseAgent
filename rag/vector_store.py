from langchain_chroma import Chroma
from utils.config_handler import chroma_conf
from model.factory import embedding_model
from langchain_text_splitters import RecursiveCharacterTextSplitter
from utils.path_tool import get_abs_path
from utils.file_handler import txt_loader,pdf_loader,listdir_with_allowed_type,get_file_md5_hex
from utils.logger_handler import logger
from langchain_core.documents import Document

import os

class VectorStoreService:
  def __init__(self):
    self.vector_store = Chroma(
      collection_name = chroma_conf['collection_name'],
      embedding_function = embedding_model,
      persist_directory = get_abs_path(chroma_conf['persist_directory'])
    )
    self.spliter = RecursiveCharacterTextSplitter(
      chunk_size = chroma_conf['chunk_size'],
      chunk_overlap = chroma_conf['chunk_overlap'],
      separators = chroma_conf['separators'],
      length_function = len
    )

  def get_retriver(self):
    return self.vector_store.as_retriever(search_kwargs={'k':chroma_conf['k']})
  
  def load_document(self):
    """
    从数据文件夹内读取数据文件，转为向量存入向量库
    MD5去重
    """
    def check_md5_hex(md5_for_check:str) -> bool:
      if not os.path.exists(get_abs_path(chroma_conf['md5_hex_store']) ):
        open( get_abs_path(chroma_conf['md5_hex_store']) ,'w' ,encoding='utf-8' ).close
        return False
      with open(get_abs_path(chroma_conf['md5_hex_store']),'r',encoding='utf-8') as file:
        for line in file.readlines():
          line = line.strip()
          if line == md5_for_check:
            return True
        return False
      
    def save_md5_hex(md5_for_check:str):
      with open(get_abs_path(chroma_conf['md5_hex_store']),'a',encoding='utf-8') as file:
        file.write(md5_for_check + '\n')

    def get_file_documents(read_path : str):
      if read_path.endswith('txt'):
        return txt_loader(read_path)
      if read_path.endswith('pdf'):
        return pdf_loader(read_path)
      return []

    allowed_file_path = listdir_with_allowed_type(
      get_abs_path(chroma_conf['data_path']),
      tuple(chroma_conf['allow_knowledge_file_type'])
    )
    for path in allowed_file_path:
      md5_hex = get_file_md5_hex(path)
      if check_md5_hex(md5_hex):
        logger.info( f'[加载知识库]{path}内容已存在于知识库,跳过' )
        continue
      try:
        docunments:list[Document] = get_file_documents(path)
        if not docunments:
          logger.warning(f'[加载知识库]{path}内没有有效内容,跳过')
          continue
        split_document:list[Document] = self.spliter.split_documents(docunments)
        if not split_document:
          logger.warning(f'[加载知识库]{path}分片后没有有效文本内容,跳过')
          continue
        self.vector_store.add_documents(split_document)

        save_md5_hex(md5_hex)
        logger.info(f'[加载知识库]{path}内容加载成功!')

      except Exception as e:
        #exc_info=True会记录详细报错堆栈
        logger.error(f'[加载知识库]{path}加载失败:{str(e)}',exc_info=True)

if __name__ == '__main__':
  vs = VectorStoreService()
  vs.load_document()
  retriever = vs.get_retriver()
  res = retriever.invoke('迷路')
  for it in res:
    print(it.page_content)
    print('='*30)