import os
from pkg.plugin.context import register, handler, BasePlugin, EventContext
from pkg.plugin.events import PersonNormalMessageReceived, GroupNormalMessageReceived
from pkg.platform.types import *

BLACKLIST_FILE = "blacklist.txt"
GROUP_BLACKLIST_FILE = "group_blacklist.txt"
ADMIN_FILE = "admin_list.txt"
AI_STATUS_FILE = "ai_status.txt"  # 用于保存 AI 开启/关闭状态

@register(name="黑名单管理插件", description="管理黑名单", version="1.5", author="牢大WSakurairo")
class BlacklistPlugin(BasePlugin):
    def __init__(self, host):
        self.host = host
        # 如果文件不存在，则创建空文件
        for file in [BLACKLIST_FILE, GROUP_BLACKLIST_FILE, ADMIN_FILE, AI_STATUS_FILE]:
            if not os.path.exists(file):
                with open(file, "w", encoding="utf-8") as f:
                    if file == AI_STATUS_FILE:
                        f.write("on")  # 默认 AI 是开启状态
                    else:
                        f.write("")

    def load_blacklist(self) -> list[int]:
        """加载用户黑名单"""
        try:
            with open(BLACKLIST_FILE, "r", encoding="utf-8") as f:
                return [int(line.strip()) for line in f.readlines() if line.strip()]
        except Exception as e:
            self.ap.logger.error(f"加载黑名单失败: {e}")
            return []

    def save_blacklist(self, blacklist: list[int]):
        """保存用户黑名单"""
        try:
            with open(BLACKLIST_FILE, "w", encoding="utf-8") as f:
                f.writelines([f"{user_id}\n" for user_id in blacklist])
        except Exception as e:
            self.ap.logger.error(f"保存黑名单失败: {e}")

    def load_group_blacklist(self) -> list[int]:
        """加载群黑名单"""
        try:
            with open(GROUP_BLACKLIST_FILE, "r", encoding="utf-8") as f:
                return [int(line.strip()) for line in f.readlines() if line.strip()]
        except Exception as e:
            self.ap.logger.error(f"加载群黑名单失败: {e}")
            return []

    def save_group_blacklist(self, group_blacklist: list[int]):
        """保存群黑名单"""
        try:
            with open(GROUP_BLACKLIST_FILE, "w", encoding="utf-8") as f:
                f.writelines([f"{group_id}\n" for group_id in group_blacklist])
        except Exception as e:
            self.ap.logger.error(f"保存群黑名单失败: {e}")

    def load_admins(self) -> list[int]:
        """加载管理员列表"""
        try:
            with open(ADMIN_FILE, "r", encoding="utf-8") as f:
                return [int(line.strip()) for line in f.readlines() if line.strip()]
        except Exception as e:
            self.ap.logger.error(f"加载管理员列表失败: {e}")
            return []

    def load_ai_status(self) -> str:
        """加载 AI 状态"""
        try:
            with open(AI_STATUS_FILE, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception as e:
            self.ap.logger.error(f"加载 AI 状态失败: {e}")
            return "on"  # 默认返回开启状态

    def save_ai_status(self, status: str):
        """保存 AI 状态"""
        try:
            with open(AI_STATUS_FILE, "w", encoding="utf-8") as f:
                f.write(status)
        except Exception as e:
            self.ap.logger.error(f"保存 AI 状态失败: {e}")

    async def is_admin(self, sender_id: int) -> bool:
        """判断是否为管理员"""
        admin_ids = self.load_admins()
        return sender_id in admin_ids

    async def handle_blacklist(self, ctx: EventContext, sender_id: int):
        """处理用户黑名单逻辑"""
        blacklist = self.load_blacklist()
        if sender_id in blacklist:
            await ctx.reply([Plain("❌ 你已在黑名单之中。")])
            ctx.prevent_default()
            return True
        return False

    async def handle_group_blacklist(self, ctx: EventContext, group_id: int):
        """处理群黑名单逻辑"""
        group_blacklist = self.load_group_blacklist()
        if group_id in group_blacklist:
            self.ap.logger.info(f"屏蔽的群消息被拒绝处理，群ID: {group_id}")
            ctx.prevent_default()
            return True
        return False

    async def handle_ai_status(self, ctx: EventContext, sender_id: int):
        """处理 AI 状态逻辑"""
        ai_status = self.load_ai_status()
        if ai_status == "off" and not await self.is_admin(sender_id):
            await ctx.reply([Plain("🤖 AI测试中....")])
            ctx.prevent_default()
            return True
        return False

    @handler(GroupNormalMessageReceived)
    async def handle_group_message(self, ctx: EventContext):
        """处理群聊普通消息"""
        event = ctx.event
        sender_id = int(event.sender_id)
        group_id = int(event.launcher_id)  # 使用 launcher_id 作为群 ID

        # 检查群黑名单
        if await self.handle_group_blacklist(ctx, group_id):
            return

        # 检查 AI 状态
        if await self.handle_ai_status(ctx, sender_id):
            return

        # 检查用户黑名单
        if await self.handle_blacklist(ctx, sender_id):
            return

        message_text = event.text_message.strip()

        if message_text in ["设置", "帮助"]:
            # 美化帮助信息
            help_message = (
                "🌟 **黑名单管理插件使用说明** 🌟\n\n"
                "📌 **命令列表**：\n"
                "1️⃣ `设置 黑名单 <用户ID>` - 将用户添加到黑名单（仅管理员可用）\n"
                "2️⃣ `设置 移除黑名单 <用户ID>` - 从黑名单中移除用户（仅管理员可用）\n"
                "3️⃣ `设置 查看黑名单` - 查看当前黑名单（仅管理员可用）\n"
                "4️⃣ `设置 群黑名单 <群ID>` - 将群添加到群黑名单（仅管理员可用）\n"
                "5️⃣ `设置 移除群黑名单 <群ID>` - 从群黑名单中移除群（仅管理员可用）\n"
                "6️⃣ `关闭AI` - 关闭 AI，仅回复管理员（仅管理员可用）\n"
                "7️⃣ `开启AI` - 开启 AI，恢复正常状态（仅管理员可用）\n"
                "8️⃣ `帮助` - 显示此帮助菜单\n\n"
                "🔒 **注意**：只有管理员可以管理黑名单和 AI 状态。\n"
            )
            await ctx.reply([Plain(help_message)])
            ctx.prevent_default()
            return

        if message_text == "关闭AI":
            if not await self.is_admin(sender_id):
                await ctx.reply([Plain("❌ 权限不足，只有管理员可以使用此命令。")])
                ctx.prevent_default()
                return
            self.save_ai_status("off")
            await ctx.reply([Plain("✅ AI 已关闭，现在仅回复管理员消息。")])
            ctx.prevent_default()
            return

        if message_text == "开启AI":
            if not await self.is_admin(sender_id):
                await ctx.reply([Plain("❌ 权限不足，只有管理员可以使用此命令。")])
                ctx.prevent_default()
                return
            self.save_ai_status("on")
            await ctx.reply([Plain("✅ AI 已开启，现在回复所有用户消息。")])
            ctx.prevent_default()
            return

        if message_text.startswith("设置 群黑名单 "):
            if not await self.is_admin(sender_id):
                await ctx.reply([Plain("❌ 权限不足，只有管理员可以使用此命令。")])
                ctx.prevent_default()
                return
            try:
                target_group_id = int(message_text.split(" ")[2])
                group_blacklist = self.load_group_blacklist()
                if target_group_id in group_blacklist:
                    await ctx.reply([Plain(f"⚠️ 群 {target_group_id} 已在群黑名单中。")])
                else:
                    group_blacklist.append(target_group_id)
                    self.save_group_blacklist(group_blacklist)
                    self.ap.logger.info(f"管理员 {sender_id} 将群 {target_group_id} 添加到群黑名单")
                    await ctx.reply([Plain(f"✅ 成功将群 {target_group_id} 添加到群黑名单。")])
            except ValueError:
                await ctx.reply([Plain("❌ 请输入正确的群 ID！")])
            ctx.prevent_default()
            return

        if message_text.startswith("设置 移除群黑名单 "):
            if not await self.is_admin(sender_id):
                await ctx.reply([Plain("❌ 权限不足，只有管理员可以使用此命令。")])
                ctx.prevent_default()
                return
            try:
                target_group_id = int(message_text.split(" ")[2])
                group_blacklist = self.load_group_blacklist()
                if target_group_id in group_blacklist:
                    group_blacklist.remove(target_group_id)
                    self.save_group_blacklist(group_blacklist)
                    self.ap.logger.info(f"管理员 {sender_id} 将群 {target_group_id} 从群黑名单中移除")
                    await ctx.reply([Plain(f"✅ 成功将群 {target_group_id} 从群黑名单中移除。")])
                else:
                    await ctx.reply([Plain(f"⚠️ 群 {target_group_id} 不在群黑名单中。")])
            except ValueError:
                await ctx.reply([Plain("❌ 请输入正确的群 ID！")])
            ctx.prevent_default()
            return

    @handler(PersonNormalMessageReceived)
    async def handle_person_message(self, ctx: EventContext):
        """处理私聊普通消息"""
        event = ctx.event
        sender_id = int(event.sender_id)

        # 检查 AI 状态
        if await self.handle_ai_status(ctx, sender_id):
            return

        # 检查用户黑名单
        if await self.handle_blacklist(ctx, sender_id):
            return

        # 如果用户不在黑名单中，允许正常处理私聊消息
        message_text = event.text_message.strip()
        await ctx.reply([Plain(f"💬 收到你的消息：{message_text}")])
