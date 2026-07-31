import cv2  
import numpy as np  
from maa.agent.agent_server import AgentServer  
from maa.custom_recognition import CustomRecognition  
from maa.context import Context  
  
@AgentServer.custom_recognition("CheckRedDot")  
class CheckRedDot(CustomRecognition):  
    def analyze(  
        self,  
        context: Context,  
        argv: CustomRecognition.AnalyzeArg,  
    ) -> CustomRecognition.AnalyzeResult:  
        x, y, w, h = argv.roi  
        region = argv.image[y:y+h, x:x+w]  # BGR  
        hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)  
  
        # 红色在 HSV 环两端，需要两段区间  
        lower1 = np.array([0, 120, 100])  
        upper1 = np.array([8, 255, 255])  
        lower2 = np.array([172, 120, 100])  
        upper2 = np.array([180, 255, 255])  
        mask = cv2.inRange(hsv, lower1, upper1) | cv2.inRange(hsv, lower2, upper2)  
  
        count = int(cv2.countNonZero(mask))  
        detail = {"red_pixel_count": count}  
  
        if count >= 20:  # 阈值按实际红点大小调整  
            return CustomRecognition.AnalyzeResult(box=(x, y, w, h), detail=detail)  
        return None  # 没有红点，识别失败，走 next 的下一个候选（"关掉界面"）