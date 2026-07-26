import json  
from maa.agent.agent_server import AgentServer  
from maa.custom_action import CustomAction  
from maa.context import Context  
  
@AgentServer.custom_action("HeSuCounterAction")  
class HeSuCounterAction(CustomAction):  
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:  
        try:  
            # 正确解析 JSON 参数  
            param = json.loads(argv.custom_action_param)  
            count_value = param.get("count", 5)  
              
            # 处理变量引用  
            if isinstance(count_value, str) and count_value.startswith("$"):  
                # 变量引用：从 context 获取实际值  
                node_name = count_value.split(".")[-1]  
                target_count = context.get_hit_count(node_name)  
            else:  
                # 直接是数字  
                target_count = int(count_value)  
        except (json.JSONDecodeError, ValueError, AttributeError) as e:  
            print(f"⚠️ 参数解析失败: {e}, 使用默认值 5")  
            target_count = 5  
          
        # 获取当前节点的命中次数  
        current_count = context.get_hit_count(argv.node_name)  
        print(f"当前已刷次数: {current_count} / 目标次数: {target_count}")  
          
        # 检查是否达到目标次数  
        return current_count <= target_count  
  
@AgentServer.custom_action("ClearCounterAction")  
class ClearCounterAction(CustomAction):  
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:  
        # 从参数中获取要清除的节点名，或使用当前节点名  
        try:  
            param = json.loads(argv.custom_action_param)  
            node_name = param.get("node_name", argv.node_name)  
        except:  
            node_name = argv.node_name  
          
        context.clear_hit_count(node_name)  
        return True