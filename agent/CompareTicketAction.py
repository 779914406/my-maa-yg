import re, json  
from maa.custom_action import CustomAction  
from maa.context import Context  
from maa.agent.agent_server import AgentServer  
  
  
@AgentServer.custom_action("CompareTicketAction")  
class CompareTicketAction(CustomAction):  
    """  
    ...(注释省略)...  
    """  
  
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:  
        param = json.loads(argv.custom_action_param or "{}")  
  
        balance_roi = param.get("balance_roi")  
        cost_roi = param.get("cost_roi")  
        pattern = param.get("pattern", r"(\d+)")  
        success_next = param.get("success_next", [])  
        fail_next = param.get("fail_next", [])  
  
        print(f"[CompareTicketAction] node={argv.node_name} param={param}")  
  
        if not balance_roi or not cost_roi:  
            print("[CompareTicketAction] balance_roi 或 cost_roi 缺失，动作失败")  
            return False  # 两个 roi 都必填，缺一不可  
  
        image = context.tasker.controller.cached_image  
  
        balance = self._read_number(context, argv.node_name + "_balance", image, balance_roi, pattern)  
        cost = self._read_number(context, argv.node_name + "_cost", image, cost_roi, pattern)  
  
        print(f"[CompareTicketAction] balance={balance}, cost={cost}")  
  
        if balance is None or cost is None:  
            # 任意一个没识别到数字，保守起见走失败分支  
            print("[CompareTicketAction] OCR 未识别到数字，走 fail_next")  
            context.override_next(argv.node_name, fail_next)  
            return True  
  
        if balance >= cost:  
            print(f"[CompareTicketAction] balance({balance}) >= cost({cost})，走 success_next: {success_next}")  
            context.override_next(argv.node_name, success_next)  
        else:  
            print(f"[CompareTicketAction] balance({balance}) < cost({cost})，走 fail_next: {fail_next}")  
            context.override_next(argv.node_name, fail_next)  
  
        return True  
  
    def _read_number(self, context, entry_name, image, roi, pattern):  
        reco_detail = context.run_recognition(  
            entry_name,  
            image,  
            pipeline_override={  
                entry_name: {  
                    "recognition": "OCR",  
                    "roi": roi,  
                }  
            },  
        )  
        if not reco_detail or not reco_detail.hit:  
            print(f"[CompareTicketAction] {entry_name} OCR 未命中, roi={roi}")  
            return None  
  
        match = re.search(pattern, reco_detail.best_result.text)  
        if not match:  
            print(f"[CompareTicketAction] {entry_name} 文本 '{reco_detail.best_result.text}' 未匹配到 pattern={pattern}")  
            return None  
  
        value = int(match.group(1))  
        print(f"[CompareTicketAction] {entry_name} 识别到文本='{reco_detail.best_result.text}' 解析数字={value}")  
        return value