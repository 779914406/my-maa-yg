import json  
import re  
import cv2  
from maa.agent.agent_server import AgentServer  
from maa.context import Context  
from maa.custom_action import CustomAction  


@AgentServer.custom_action("ReadCurrencyBalance")    
class ReadCurrencyBalance(CustomAction):    
    """专门负责在进入商店时/购买后读取并记录余额"""    
  
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:    
        print(f"\n==================== [DEBUG] 开始读取商店余额: {argv.node_name} ====================")    
  
        try:    
            params = json.loads(argv.custom_action_param) if argv.custom_action_param else {}    
        except json.JSONDecodeError:    
            params = {}    
  
        balance_roi = params.get("roi", [75, 85, 120, 50])    
  
        image = context.tasker.controller.post_screencap().wait().get()    
  
        reco_result = context.run_recognition(    
            "OCR",    
            image,    
            pipeline_override={    
                "OCR": {    
                    "recognition": "OCR",    
                    "roi": balance_roi,    
                    "expected": [".*"]    
                }    
            }    
        )    
  
        raw_text = ""    
        if reco_result and hasattr(reco_result, "best_result") and reco_result.best_result:    
            raw_text = str(reco_result.best_result.text)    
  
        cleaned_text = raw_text.strip().replace(" ", "")    
        multiplier = 10000 if ("万" in cleaned_text or "w" in cleaned_text.lower()) else 1    
        cleaned_text = cleaned_text.replace("万", "").replace("w", "").replace("W", "")    
  
        match = re.search(r"\d+(\.\d+)?", cleaned_text)    
        if match:    
            balance = int(float(match.group()) * multiplier)    
            context.set_anchor("CurrencyBalance", str(balance))    
            print(f"[DEBUG] ✅ 成功读取并记录钱包余额: {balance}")    
        else:    
            print(f"[DEBUG] ❌ 余额文本解析失败 ('{raw_text}')，默认设为 0")    
            context.set_anchor("CurrencyBalance", "0")    
  
        print("=====================================================================\n")    
        return True    
  
  
@AgentServer.custom_action("CheckShopBalance")  
class CheckShopBalance(CustomAction):  
    """通过 OCR 判断商品是否已售完/余额是否够买一个，然后决定是否进入购买节点"""  
  
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:  
        print(f"\n==================== [DEBUG] 开始检测商品节点: {argv.node_name} ====================")  
  
        try:  
            params = json.loads(argv.custom_action_param) if argv.custom_action_param else {}  
        except json.JSONDecodeError:  
            params = {}  
  
        next_node = params.get("next_node", "")  
        price_roi = params.get("price_roi", [])  
  
        if not price_roi:  
            print(f"[DEBUG] 未配置 price_roi, 跳过检查")  
            return True  
  
        balance_str = context.get_anchor("CurrencyBalance")  
        balance = int(balance_str) if balance_str else 0  
  
        image = context.tasker.controller.post_screencap().wait().get()  
  
        price_reco = context.run_recognition(  
            "OCR",  
            image,  
            pipeline_override={  
                "OCR": {  
                    "recognition": "OCR",  
                    "roi": price_roi,  
                    "expected": [".*"]  
                }  
            }  
        )  
  
        if not price_reco or not hasattr(price_reco, "best_result") or not price_reco.best_result:  
            print(f"[DEBUG] 未识别到任何内容，跳过")  
            return True  
  
        raw_text = str(price_reco.best_result.text).strip()  
        print(f"[DEBUG] 识别到文本: '{raw_text}'")  
  
        if any(keyword in raw_text for keyword in ["已售完", "售罄", "已售", "罄", "Sold Out"]):  
            print(f"【商店判定】[{argv.node_name}] OCR识别到已售完文本, 跳过。")  
            return True  
  
        match = re.search(r"\d+", raw_text)  
        if not match:  
            print(f"【商店判定】[{argv.node_name}] 未识别到价格数字 (原文: '{raw_text}')，跳过。")  
            return True  
  
        unit_price = int(match.group())  
        print(f"[DEBUG] 单价: {unit_price}, 余额: {balance}")  
  
        if unit_price <= 0 or balance < unit_price:  
            print(f"【商店判定】[{argv.node_name}] 余额不足, 跳过。")  
            return True  
  
        print(f"【商店判定】[{argv.node_name}] 余额足够，进入购买节点: {next_node}")  
        if next_node:  
            context.override_next(argv.node_name, [next_node])  
  
        return True

    

@AgentServer.custom_action("CheckFinalPrice")
class CheckFinalPrice(CustomAction):
    """专门在点击 MAX 后，二次校验弹窗内的实际总价，防止超出钱包余额"""
    
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        print(f"\n==================== [DEBUG] 开始检测弹窗最终价格: {argv.node_name} ====================")
        
        try:
            params = json.loads(argv.custom_action_param) if argv.custom_action_param else {}
        except json.JSONDecodeError:
            params = {}
            
        price_roi = params.get("price_roi", [])
        buy_node = params.get("buy_node", "")
        close_node = params.get("close_node", "")
        
        if not price_roi:
            print(f"[DEBUG] 未配置 price_roi,跳过最终价格检查")
            return True
            
        balance_str = context.get_anchor("CurrencyBalance")
        balance = int(balance_str) if balance_str else 0
        
        image = context.tasker.controller.post_screencap().wait().get()
        
        price_reco = context.run_recognition(
            "OCR",
            image,
            pipeline_override={
                "OCR": {
                    "recognition": "OCR",
                    "roi": price_roi,
                    "expected": [".*"]
                }
            }
        )
        
        if not price_reco or not hasattr(price_reco, "best_result") or not price_reco.best_result:
            print(f"[DEBUG] 弹窗内未识别到总价文本，默认关闭弹窗")
            if close_node:
                context.override_next(argv.node_name, [close_node])
            return True
            
        raw_text = str(price_reco.best_result.text).strip()
        print(f"[DEBUG] 弹窗识别到文本: '{raw_text}'")
        
        match = re.search(r"\d+", raw_text)
        if not match:
            print(f"【商店判定】[{argv.node_name}] 未识别到总价数字 (原文: '{raw_text}')，关闭弹窗。")
            if close_node:
                context.override_next(argv.node_name, [close_node])
            return True
            
        total_price = int(match.group())
        print(f"[DEBUG] 钱包余额: {balance}, 弹窗实际总价: {total_price}")
        
        if balance >= total_price:
            print(f"【商店判定】[{argv.node_name}] 余额充足，执行购买节点: {buy_node}")
            if buy_node:
                context.override_next(argv.node_name, [buy_node])
        else:
            print(f"【商店判定】[{argv.node_name}] 余额不足实际总价！关闭弹窗。")
            if close_node:
                context.override_next(argv.node_name, [close_node])
                
        print("=====================================================================\n")
        return True