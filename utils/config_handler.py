"""
配置文件
yaml
k:v
"""
import yaml
from .path_tool import get_abs_path

def load_rag_config(
    config_path:str = get_abs_path('config/rag.yml'),
    enconding: str = 'utf-8'
    ):
  with open(config_path,'r',encoding=enconding) as file:
    return yaml.load(file,Loader=yaml.FullLoader)


def load_chroma_config(
    config_path:str = get_abs_path('config/chroma.yml'),
    enconding: str = 'utf-8'
    ):
  with open(config_path,'r',encoding=enconding) as file:
    return yaml.load(file,Loader=yaml.FullLoader)


def load_prompts_config(
    config_path:str = get_abs_path('config/prompts.yml'),
    enconding: str = 'utf-8'
    ):
  with open(config_path,'r',encoding=enconding) as file:
    return yaml.load(file,Loader=yaml.FullLoader)


def load_agent_config(
    config_path:str = get_abs_path('config/agent.yml'),
    enconding: str = 'utf-8'
    ):
  with open(config_path,'r',encoding=enconding) as file:
    return yaml.load(file,Loader=yaml.FullLoader)

rag_conf = load_rag_config()
chroma_conf = load_chroma_config()
prompts_conf = load_prompts_config()
agent_conf = load_agent_config()

if __name__ == '__main__':
  res = rag_conf['chat_model_name']
  print(type(res))
  print(res)