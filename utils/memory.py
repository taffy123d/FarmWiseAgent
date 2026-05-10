from utils.logger_handler import logger

MAX_TOKENS = 128 * 1024


class ConversationMemory:
    """内存级对话记忆管理器，按 user_id 区分会话，不持久化"""

    def __init__(self):
        self._sessions: dict[str, list[dict]] = {}

    def add_message(self, user_id: str, role: str, content: str, reasoning_content: str = None):
        if user_id not in self._sessions:
            self._sessions[user_id] = []
        msg = {"role": role, "content": content}
        if reasoning_content:
            msg["reasoning_content"] = reasoning_content
        self._sessions[user_id].append(msg)
        self._trim_history(user_id)

    def get_history(self, user_id: str) -> list[dict]:
        return self._sessions.get(user_id, [])

    def clear(self, user_id: str):
        if user_id in self._sessions:
            del self._sessions[user_id]
            logger.info(f"[memory]已清空用户 {user_id} 的对话记忆")

    @staticmethod
    def _estimate_tokens(messages: list[dict]) -> int:
        total = 0
        for msg in messages:
            total += len(msg.get("content", "")) / 1.5
        return int(total)

    def _trim_history(self, user_id: str):
        messages = self._sessions.get(user_id, [])
        while self._estimate_tokens(messages) > MAX_TOKENS and len(messages) > 1:
            removed = messages.pop(0)
            logger.info(f"[memory]裁剪旧消息 token={self._estimate_tokens([removed])}，当前总量={self._estimate_tokens(messages)}")

    def __contains__(self, user_id: str) -> bool:
        return user_id in self._sessions


memory = ConversationMemory()
