from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context

@AgentServer.custom_action("ClickDynamicInviteAction")
class ClickDynamicInviteAction(CustomAction):
    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> bool:
        print("\n---------------- [CustomAction 触发] ----------------")

        # 1. 获取识别结果
        rec_detail = None
        for attr_name in ["reco_detail", "rec_detail", "reco_result"]:
            if hasattr(argv, attr_name) and getattr(argv, attr_name):
                rec_detail = getattr(argv, attr_name)
                print(f"💡 成功在 argv.{attr_name} 获取到识别数据")
                break

        if not rec_detail and hasattr(argv, "box") and argv.box:
            rec_detail = argv

        if not rec_detail:
            print("❌ 错误: 未能获取到识别结果")
            return False

        try:
            # 2. 提取识别框 (box)
            box = getattr(rec_detail, "box", rec_detail)
            print(f"🔍 识别框数据 (box): {box}")

            # 解析 Y 轴坐标与高度
            if hasattr(box, "y") and hasattr(box, "height"):
                y, h = box.y, box.height
            elif isinstance(box, (list, tuple)) and len(box) >= 4:
                y, h = box[1], box[3]
            elif hasattr(box, "y") and hasattr(box, "h"):
                y, h = box.y, box.h
            else:
                print("❌ 错误: 无法提取 Y 轴坐标")
                return False

            # 3. 计算最终点击坐标
            center_y = y + (h / 2)
            target_y = int(center_y + 50)  # 垂直微调
            target_x = 580                 # 右侧“邀请”按钮中心 X 坐标

            # 🚨【新增部分】安全边界防护判断 🚨
            MAX_Y_LIMIT = 870  # 安全线，超过 870 说明按钮露不全或被底部面板挡住
            if target_y > MAX_Y_LIMIT:
                print(f"⚠️ 提示: 算出的坐标 Y={target_y} 超过安全范围 ({MAX_Y_LIMIT})，按钮未露全！")
                print("🔄 放弃本次点击，返回 False 触发 JSON 中的 on_error (滑动列表)...")
                print("---------------------------------------------------\n")
                return False

            print(f"🎯 坐标计算成功: 文字Y={y}, 高度={h} -> 点击目标: ({target_x}, {target_y})")

            # 4. 执行点击 (自动兼容 MAA Controller 的 post_click 方法)
            controller = None
            if hasattr(context, "tasker") and hasattr(context.tasker, "controller"):
                controller = context.tasker.controller
            elif hasattr(context, "controller"):
                controller = context.controller

            clicked = False
            # 尝试 controller 上的点击 API
            if controller:
                for method_name in ["post_click", "click", "click_point"]:
                    if hasattr(controller, method_name):
                        getattr(controller, method_name)(target_x, target_y)
                        print(f"✅ 通过 Controller.{method_name}({target_x}, {target_y}) 发送点击成功！")
                        clicked = True
                        break

            # 备用：尝试 context 本身的点击 API
            if not clicked:
                for method_name in ["post_click", "click"]:
                    if hasattr(context, method_name):
                        getattr(context, method_name)(target_x, target_y)
                        print(f"✅ 通过 Context.{method_name}({target_x}, {target_y}) 发送点击成功！")
                        clicked = True
                        break

            if not clicked:
                print("❌ 错误: 未能找到有效的点击 API")
                return False

            print("---------------------------------------------------\n")
            return True

        except Exception as e:
            print(f"❌ 运行发生异常: {e}")
            return False
