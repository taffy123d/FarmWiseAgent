from langchain.agents import create_agent
from langchain_core.messages import AIMessage
from model.factory import chat_model
from utils.prompt_loader import load_system_prompts
from .tools.agent_tools import (
  rag_summarize,get_weather,get_location,get_current_date,get_user_id,fill_context_for_report,ddsearch
)
from .tools.middleware import  (
 monitor_tool,log_before_model,report_prompt_switch 
)


tools = [rag_summarize,get_weather,get_location,get_current_date,get_user_id,fill_context_for_report,ddsearch]
middleware = [monitor_tool,log_before_model,report_prompt_switch]

class ReactAgent:
  def __init__(self):
    self.agent = create_agent(
      model=chat_model,
      system_prompt=load_system_prompts(),
      tools=tools,
      middleware=middleware
    )
  def execute_stream(self,messages:list[dict]):
    input_dict = {'messages': messages}
    for chunk in self.agent.stream(input_dict,stream_mode='values',context={'report':False}): #context即为提示词切换标记
      latest_message = chunk['messages'][-1]
      if isinstance(latest_message, AIMessage) and latest_message.content:
        msg_type = "thinking" if getattr(latest_message, 'tool_calls', []) else "final"
        item = {
          "type": msg_type,
          "chunk": latest_message.content.strip()+'\n'
        }
        if latest_message.additional_kwargs.get("reasoning_content"):
          item["reasoning_content"] = latest_message.additional_kwargs["reasoning_content"]
        yield item

  def execute_invoke(self,messages:list[dict]) ->str :
    input_dict = {'messages': messages}
    res = self.agent.invoke(input_dict)
    return res["output"]

if __name__ == '__main__':
  agent = ReactAgent()
  messages = []
  while True:
    q = input('input: ')
    if q == 'quit':
      print('exit...')
      break
    messages.append({'role':'user','content':q})
    for item in agent.execute_stream(messages):
      print(item['chunk'],end='',flush=True)
