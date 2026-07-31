import json  
from maa.agent.agent_server import AgentServer  
from maa.custom_action import CustomAction  
from maa.context import Context  
from maa.pipeline import JRecognitionType, JOCR  
  
  
@AgentServer.custom_action("FindAndClickTab")  
class FindAndClickTab(CustomAction):  
    """  
    通用的横向 Tab 栏查找+点击 Custom 动作。  
    不写死任何商店名，全部通过 custom_action_param 传入，可复用于任意横向 Tab 场景。  
  
    参数 JSON:  
    {  
        "roi": [43, 1099, 547, 61],  
        "order": ["列车商店", "竞技商店", "噩梦商店", "地府商店", "天帝商店"],  
        "target": "天帝商店",  
        "max_steps": 10,  
        "swipe_step": 200,  
        "swipe_y": 1130,  
        "swipe_duration": 300,  
        "post_delay": 400  
    }  
    """  
  
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:  
        param = json.loads(argv.custom_action_param or "{}")  
        roi = param["roi"]  
        order = param["order"]  
        target_text = param["target"]  
        max_steps = param.get("max_steps", 10)  
        swipe_step = param.get("swipe_step", 200)  
        swipe_y = param.get("swipe_y", roi[1] + roi[3] // 2)  
        swipe_duration = param.get("swipe_duration", 300)  
        post_delay = param.get("post_delay", 400)  
  
        if target_text not in order:  
            return False  
        target_index = order.index(target_text)  
  
        controller = context.tasker.controller  
        last_direction = None  
  
        for _ in range(max_steps + 1):  
            image = controller.post_screencap().wait().get()  
            if image is None or image.size == 0:  
                return False  
  
            reco_detail = context.run_recognition_direct(  
                JRecognitionType.OCR,  
                JOCR(expected=order, roi=roi, order_by="Horizontal", only_rec=False),  
                image,  
            )  
  
            visible = []  
            if reco_detail and reco_detail.hit:  
                for result in reco_detail.filtered_results:  
                    text = getattr(result, "text", "")  
                    for i, name in enumerate(order):  
                        if name in text or text in name:  
                            visible.append((i, result.box, name))  
                            break  
  
            hit = next((v for v in visible if v[2] == target_text), None)  
            if hit:  
                box = hit[1]  
                controller.post_click(  
                    box[0] + box[2] // 2, box[1] + box[3] // 2  
                ).wait()  
                return True  
  
            if visible:  
                ref_index, _, _ = min(visible, key=lambda v: abs(v[0] - target_index))  
                direction = "left" if ref_index < target_index else "right"  
            else:  
                direction = last_direction or "left"  
  
            begin_x, end_x = (  
                (roi[0] + roi[2], max(roi[0], roi[0] + roi[2] - swipe_step))  
                if direction == "left"  
                else (roi[0], min(roi[0] + roi[2], roi[0] + swipe_step))  
            )  
            controller.post_swipe(begin_x, swipe_y, end_x, swipe_y, swipe_duration).wait()  
            if post_delay:  
                import time  
                time.sleep(post_delay / 1000.0)  
            last_direction = direction  
  
        return False