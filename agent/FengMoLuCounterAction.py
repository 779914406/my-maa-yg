import json  
from maa.agent.agent_server import AgentServer  
from maa.custom_action import CustomAction  
from maa.context import Context  
  
@AgentServer.custom_action("FengMoLuCounterAction")
class FengMoLuCounterAction(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        try:
            # 解析 JSON 参数中的 count 值
            param = json.loads(argv.custom_action_param)
            count_value = param.get("count", 5)
            
            if isinstance(count_value, str) and count_value.startswith("$"):
                node_name = count_value.split(".")[-1]
                target_count = context.get_hit_count(node_name)
            else:
                target_count = int(count_value)
        except (json.JSONDecodeError, ValueError, AttributeError) as e:
            print(f"⚠️ 封魔录参数解析失败: {e}, 使用默认值 5")
            target_count = 5
        
        # 获取拦截节点当前的命中次数[cite: 1]
        current_count = context.get_hit_count(argv.node_name)
        print(f"封魔录当前已刷次数: {current_count} / 目标次数: {target_count}")
        
        # 如果当前次数小于等于目标次数，返回 True（继续执行）；否则返回 False（触发 on_error 退出）[cite: 1]
        return current_count <= target_count