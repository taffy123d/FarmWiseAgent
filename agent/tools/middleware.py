from langchain.agents.middleware import wrap_tool_call,before_model,dynamic_prompt,ModelRequest
from langchain.agents import AgentState
from langgraph.runtime import Runtime
from langchain.tools.tool_node import ToolCallRequest
from langchain_core.messages import ToolMessage
from typing import Callable
from langgraph.types import Command
from utils.logger_handler import logger
from utils.prompt_loader import load_system_prompts,load_report_prompts
import json
from utils.config_handler import agent_conf

@wrap_tool_call
def monitor_tool(
  request:ToolCallRequest,
  handler:Callable[[ToolCallRequest],ToolMessage|Command]
) -> ToolMessage|Command:
  logger.info(f'[tool_monitor]执行工具:{request.tool_call["name"]}')
  logger.info(f'[tool_monitor]传入参数:{request.tool_call["args"]}')
  try:
    res = handler(request)
    logger.info(f'[tool_monitor]工具 {request.tool_call["name"]} 调用成功!')
    
    #标记
    if request.tool_call["name"] == 'fill_context_for_report':
      request.runtime.context['report'] = True

    return res
  except Exception as e:
    logger.error(f'工具 {request.tool_call["name"]} 调用失败, {str(e)}')
    raise e
  
# =========================================================================================================================

#debug打印messages开关
import ast
MSG_PRINT_SWITCH = agent_conf['debug_print_all_msg']

@before_model
def log_before_model(
  state:AgentState,   #整个AGENT中的状态记录
  runtime:Runtime     #记录了整个执行过程的上下文信息
):
  logger.info(f'[log_before_model]即将调用模型, 带有{len(state["messages"])}条消息')
# ------------------------------------------------------------------------------------------
  if MSG_PRINT_SWITCH:
    try:
      serializable_messages = []
      for msg in state["messages"]:
          # 优先尝试 Pydantic v2 的 model_dump()
          if hasattr(msg, "model_dump"):
              serializable_messages.append(msg.model_dump())
          # 兼容 Pydantic v1 的 dict()
          elif hasattr(msg, "dict"):
              serializable_messages.append(msg.dict())
          # 处理普通 Python 对象
          elif hasattr(msg, "__dict__"):
              # 过滤掉内部私有属性（可选，让日志更干净）
              msg_dict = {k: v for k, v in msg.__dict__.items() if not k.startswith('_')}
              serializable_messages.append(msg_dict)
          else:
              serializable_messages.append(str(msg))
      
      logger.info(
          f"[log_before_model] 完整消息列表:\n"
          f"{json.dumps(serializable_messages, ensure_ascii=False, indent=2)}"
      )
    except Exception as e:
      logger.error(f"[log_before_model] 打印完整消息失败: {str(e)}")
# ------------------------------------------------------------------------------------------
  logger.debug(f'[log_before_model] ({type(state["messages"][-1]).__name__}) : {state["messages"][-1].content.strip()}')
  return None

# =========================================================================================================================

@dynamic_prompt   #每次在生成提示词前调用此函数
def report_prompt_switch(request:ModelRequest):
  is_report = request.runtime.context.get('report',False)
  if is_report:       #True 需要报告生成
    return load_report_prompts()
  return load_system_prompts()
