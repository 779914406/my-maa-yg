import json  
from maa.agent.agent_server import AgentServer  
from maa.custom_action import CustomAction  
from maa.context import Context  
  
  
@AgentServer.custom_action("WuJianCounterAction")  
class WuJianCounterAction(CustomAction):  
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:  
        try:  
            param = json.loads(argv.custom_action_param)  
            count_value = param.get("count", 5)  
  
            if isinstance(count_value, str) and count_value.startswith("$"):  
                node_name = count_value.split(".")[-1]  
                target_count = context.get_hit_count(node_name)  
            else:  
                target_count = int(count_value)  
        except (json.JSONDecodeError, ValueError, AttributeError) as e:  
            print(f"⚠️ 无间鬼蜮参数解析失败: {e}, 使用默认值 5")  
            target_count = 5  
  
        # 新增:负数(如 -1)表示无限模式，永远返回 True，  
        # 结束条件完全交给 pipeline 里已有的 "开启玩法" OCR 检测节点  
        if target_count < 0:  
            current_count = context.get_hit_count(argv.node_name)  
            print(f"无间鬼蜮无限模式，当前已刷次数: {current_count}")  
            return True  
  
        current_count = context.get_hit_count(argv.node_name)  
        print(f"无间鬼蜮当前已刷次数: {current_count} / 目标次数: {target_count}")  
        return current_count <= target_count