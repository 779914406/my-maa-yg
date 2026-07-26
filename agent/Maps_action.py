import json  
import re  
from maa.agent.agent_server import AgentServer  
from maa.custom_action import CustomAction  
from maa.context import Context  
  
@AgentServer.custom_action("HeSuNavigateAction")  
class HeSuNavigateAction(CustomAction):  
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:  
        # 1. 解析参数  
        try:  
            param = json.loads(argv.custom_action_param)  
            target = int(param.get("target", 15))  
        except (json.JSONDecodeError, ValueError):  
            target = 15  
          
        # 2. 获取当前截图  
        image = context.tasker.controller.post_screencap().wait().get()  
          
        # 3. 读取当前夜数  
        reco = context.run_recognition("合宿_读取当前夜", image)  
        if not reco or not reco.hit:  
            print("未识别到夜数，重试中...")  
            return True  # 返回 True 让 Pipeline 继续重试  
              
        # 4. 提取数字 - 修正访问方式  
        if reco.best_result:  
            reco_text = reco.best_result.text if hasattr(reco.best_result, 'text') else ""  
        else:  
            reco_text = ""  
              
        match = re.search(r'\d+', reco_text)  
        if not match:  
            print(f"未能从识别结果 '{reco_text}' 中提取到数字，重试中...")  
            return True  
              
        current = int(match.group())  
        print(f"📌 当前: 第{current}夜 / 🎯 目标: 第{target}夜")  
          
        # 5. 智能比大小并点击  
        if current == target:  
            print("✅ 到达目标，进入下一步。")  
            return True  # 到达目标，进入 next  
        elif current < target:  
            print("👉 目标在右，点右箭头")  
            context.run_task("合宿_单次点右")  
            return True  # 继续循环  
        else:  
            print("👈 目标在左，点左箭头")  
            context.run_task("合宿_单次点左")  
            return True  # 继续循环