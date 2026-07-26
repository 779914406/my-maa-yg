import cv2  
import numpy as np  
import time  
from maa.agent.agent_server import AgentServer  
from maa.custom_action import CustomAction  
  
@AgentServer.custom_action("ClaimRewardAct")  
class ClaimRewardAct(CustomAction):  
    def run(self, context, argv: CustomAction.RunArgv) -> bool:  
        print("[CustomAction] 开始执行每日签到与累计奖励判定...")  
  
        blank_x, blank_y = 387, 1200  # 空白区域坐标（用于关闭弹窗）  
  
        # 1. 点击"每日签到"按钮  
        context.tasker.controller.post_click(315, 1084).wait()  
        time.sleep(1.0)  
          
        # 点一下空白处，关掉可能出现的日签到奖励弹窗  
        context.tasker.controller.post_click(blank_x, blank_y).wait()  
        time.sleep(0.8)  
  
        # 2. 定义 4 个累计奖励节点的点击坐标与检测 ROI (x, y, w, h)
        cum_nodes = [  
            {"day": "7天",  "click": (213, 312), "roi": (180, 280, 65, 65)},  
            {"day": "14天", "click": (343, 314), "roi": (310, 280, 65, 65)},  
            {"day": "21天", "click": (474, 310), "roi": (440, 280, 65, 65)},  
            {"day": "30天", "click": (605, 312), "roi": (570, 280, 65, 65)},  
        ]  
  
        # 3. 逐个检测与处理  
        for node in cum_nodes:  
            # 获取最新截图  
            image = context.tasker.controller.post_screencap().wait().get()  
  
            # 绿对勾识别（已领过的直接 skip）  
            if self.has_green_checkmark(image, node["roi"]):  
                print(f"[CustomAction] {node['day']} 已有绿对勾（已领过），跳过！")  
                continue  
  
            # 未领取的，执行点击并关闭弹窗  
            print(f"[CustomAction] {node['day']} 未领取，执行点击！")  
            cx, cy = node["click"]  
            context.tasker.controller.post_click(cx, cy).wait()  
            time.sleep(1.2)  
  
            # 点击空白处关闭奖励弹窗  
            context.tasker.controller.post_click(blank_x, blank_y).wait()  
            time.sleep(0.8)  
  
        # 4. 动态调整任务流，继续跳转到"精彩活动返回主线"  
        context.override_next(argv.node_name, ["精彩活动返回主线"])  
          
        return True  
  
    def has_green_checkmark(self, img_bgr, roi) -> bool:  
        """根据 ROI 内的亮绿色像素数量判断是否包含绿色对勾"""  
        if img_bgr is None:  
            return False  
  
        x, y, w, h = roi  
        crop = img_bgr[y : y + h, x : x + w]  
  
        # 转 HSV 色域精准匹配绿色  
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)  
        lower_green = np.array([35, 80, 80])  
        upper_green = np.array([85, 255, 255])  
  
        mask = cv2.inRange(hsv, lower_green, upper_green)  
        green_pixel_count = cv2.countNonZero(mask)  
  
        # 绿色像素大于阈值即认为已打勾  
        return green_pixel_count > 40