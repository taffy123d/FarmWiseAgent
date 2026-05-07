from .config_handler import prompts_conf
from .path_tool import get_abs_path
from .logger_handler import logger

def load_system_prompts():
  try:
    system_prompt_path = get_abs_path( prompts_conf['main_prompt_path'] )
  except KeyError as e:
    logger.error(f'[load_system_prompt]prompts.yml中main_prompt_path项未配置')
    raise e
  try:
    return open(system_prompt_path,'r',encoding='utf-8').read()
  except Exception as e:
    logger.error(f'[load_system_prompt]解析系统提示词出错 {str(e)}')
    raise e

def load_rag_prompts():
  try:
    rag_prompt_path = get_abs_path( prompts_conf['rag_summarize_prompt_path'] )
  except KeyError as e:
    logger.error(f'[load_rag_prompt]prompts.yml中rag_summarize_prompt_path项未配置')
    raise e
  try:
    return open(rag_prompt_path,'r',encoding='utf-8').read()
  except Exception as e:
    logger.error(f'[load_rag_prompt]解析rag_summarize提示词出错 {str(e)}')
    raise e

def load_report_prompts():
  try:
    report_prompt_path = get_abs_path( prompts_conf['report_prompt_path'] )
  except KeyError as e:
    logger.error(f'[load_report_prompt]prompts.yml中report_prompt_path项未配置')
    raise e
  try:
    return open(report_prompt_path,'r',encoding='utf-8').read()
  except Exception as e:
    logger.error(f'[load_report_prompt]解析report提示词出错 {str(e)}')
    raise e

if __name__ == '__main__':
  a = load_system_prompts()
  b = load_rag_prompts()
  c = load_report_prompts()
  # print(a)
  # print(b)
  print(c)