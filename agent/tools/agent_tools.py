from langchain_core.tools import tool
from pydantic import BaseModel, Field  # 用于工具参数严格校验
from rag.rag_service import RagSummarizeService
from .Weather.weather import get2_weather
from .Location.location import get2_location
import json
from utils.config_handler import agent_conf
from utils.path_tool import get_abs_path
from utils.logger_handler import logger
import os
from datetime import date
from langchain_community.tools import DuckDuckGoSearchRun


# =========================================================================================================================

ddsearch = DuckDuckGoSearchRun()

# =========================================================================================================================

rag = RagSummarizeService()

@tool(description='''
   - 核心能力：入参为query（检索词），从向量库检索 农作物 专业知识，收割播种建议，病虫害防治等相关专业知识
   - 出参：字符串类型的专业资料内容，包含与检索词匹配的解答、建议及知识点；
   - 使用场景：当回答用户问题需要补充 农作物 的专业信息、现有常识无法精准解答时调用；
   - 调用规则：必须传入纯文本字符串类型的query参数，参数为贴合用户问题的核心检索词。
''')
def rag_summarize(query:str)->str:
  return rag.rag_summarize(query)

# =========================================================================================================================

class cityNameInput(BaseModel):
   city:str = Field(description='需要查询天气的城市名字')
@tool(description='''
   - 核心能力：入参为city（城市名），获取指定城市的实时天气、空气湿度、降雨概率等核心环境信息；
   - 出参：字符串类型的环境信息，包含城市对应的实时天气相关数据；
   - 使用场景：仅实时环境适配场景下，已通过get_user_location获取用户城市后，调用此工具获取对应天气信息；非该场景严禁调用；
   - 调用规则：必须传入纯文本字符串类型的city参数，参数为标准的城市名称。
''',
    args_schema=cityNameInput)
def get_weather(city:str) -> str:
   return get2_weather(city)

# =========================================================================================================================


@tool(description='''
   - 核心能力：入参为city（城市名），获取指定城市的实时天气、空气湿度、降雨概率等核心环境信息；
   - 出参：字符串类型的环境信息，包含城市对应的实时天气相关数据；
   - 使用场景：仅实时环境适配场景下，已通过get_user_location获取用户城市后，调用此工具获取对应天气信息；非该场景严禁调用；
   - 调用规则：必须传入纯文本字符串类型的city参数，参数为标准的城市名称。
''')
def get_location():
  res_json = json.dumps( get2_location(),ensure_ascii=False )
  return str(res_json)

# =========================================================================================================================


@tool(description='''
   - 核心能力：无入参，精准获取当前发起请求的用户唯一标识（ID字符串），ID格式为数字字符串（如"1001"）；
   - 出参：字符串类型的用户ID（如"1002"）；
   - 使用场景：当需要基于「当前用户的ID」检索其专属使用记录、生成个性化使用报告时，如未知用户ID可先调用此工具获取用户ID，再进行后续操作；
   - 调用规则：无需传入任何参数，直接触发调用即可。
''')
def get_user_id() -> str:
   return agent_conf['user_id']

# =========================================================================================================================

@tool(description='''
    获取当前日期(年-月-日),以字符串形式返回,无输入参数 
      ''')
def get_current_date() -> str:
  return date.today()

# =========================================================================================================================
external_data = {}

def generate_external_data():

  if not external_data:
    external_data_path = get_abs_path(agent_conf['external_data_path'])
    if not os.path.exists(external_data_path):
      raise FileNotFoundError(f'{external_data_path}文件不存在!')
    with open (external_data_path,'r',encoding='utf-8') as file:
      for line in file.readlines()[1:]:
        arr:list[str] = line.strip().split(',')
        user_id:str = arr[0].replace('"','')
        location:str = arr[1].replace('"','')
        weather:str = arr[2].replace('"','')
        kind:str = arr[3].replace('"','')
        cmt:str = arr[4].replace('"','')
        time:str = arr[5].replace('"','')
        if user_id not in external_data:
          external_data[user_id] = {}
        external_data[user_id][time]={
          "地理位置":location,
          "当日天气及气温":weather,
          "农作物类别":kind,
          "建议":cmt
        }

class fetch_external_data_Input(BaseModel):
   user_id:str = Field(description='用户ID')
   month:str = Field(description='年月 严格遵循"YYYY-MM"格式，如"2025-03"')

@tool(
      description='''
    从外部系统中检索指定用户在指定月份(年月)的 农作物收割播种建议 记录,以字符串形式返回,若未检索到则返回空字符串
   - 核心能力：入参为user_id（用户ID）和month（月份），检索指定用户在指定月份的完整记录；
   - 出参：字符串类型的结构化使用记录，包含["用户ID","地理位置","当日天气及气温","农作物类别","建议","时间"] 等核心报告数据；
   - 使用场景：当需要为用户生成报告时，如未知用户ID或月份信息，可先通过get_user_id/get_current_month或用户指定获取入参，再调用此工具；
   - 调用规则：必须同时传入纯文本字符串类型的user_id和month参数，user_id为数字字符串，month严格遵循"YYYY-MM"格式。
    '''
      ,args_schema=fetch_external_data_Input
    )
def fetch_external_data(user_id:str , month:str):
  generate_external_data()
  try:
    return external_data[user_id][month]
  except KeyError:
    logger.warning(f'[fetch_external_data]未检索到{user_id}在{month}的使用记录')
    return ''
  pass

# =========================================================================================================================

@tool(description='''
    无入参无返回值,调用后触发中间件自动为报告生成的场景动态注入上下文信息,为后续切换提示词提通上下文信息
  - 核心能力：无入参，调用后触发中间件自动为报告生成场景动态注入上下文信息，为后续提示词切换提供上下文支撑；
   - 出参：无返回值，仅完成上下文注入的底层操作；
   - 使用场景：仅当明确识别出用户核心意图为「生成/查询个人使用报告」（如“生成我的6月使用报告”，“查一下我的使用记录”）时，优先调用此工具；非报告生成场景严禁调用；
   - 调用规则：
     1. 无需传入任何参数，直接触发调用即可；
     2. 禁用场景：用户仅咨询非报告类需求时，绝对不调用此工具。    
  ''')
def fill_context_for_report():
  logger.info(f'[fill_context_for_report]已调用')
  return '[fill_context_for_report]已调用'

# =========================================================================================================================

