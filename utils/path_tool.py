"""
为整个工程提供统一的绝对路径
"""

import os

def get_project_root() ->str :
  #当前文件绝对路径
  current_file = os.path.abspath(__file__)
  #获取项目根绝对目录
  current_dir = os.path.dirname(current_file)
  #项目根绝对目录
  project_root = os.path.dirname(current_dir)
  return project_root

def get_abs_path(relative_path:str) -> str :
  #传入相对路径，获取绝对路径
  project_root = get_project_root()
  return os.path.join(project_root,relative_path)
  pass


if __name__ == '__main__':
  res = get_abs_path('')
  print(res)