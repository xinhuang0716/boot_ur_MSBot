"""Bot logic layer."""

from typing import cast

from botbuilder.core import ActivityHandler, ConversationState, MessageFactory, TurnContext
from botbuilder.schema import ActionTypes, CardAction, SuggestedActions

from bot.cards import build_adaptive_card, build_hero_card
from bot.feedback import save_feedback
from config import DefaultConfig
from services.ollama import call_ollama

CONFIG = DefaultConfig()


class OllamaBot(ActivityHandler):
    """A Bot that replies to user messages using the Ollama LLM.

    Handles Activity dispatching:
    - Regular messages        → calls Ollama LLM for a reply + 👍/👎 buttons
    - "hero card"             → displays a Hero Card example
    - "adaptive card"         → displays an Adaptive Card example
    - feedback:up/down:{id}   → stores rating in state, asks for comment
    - pending feedback state  → saves comment + rating to feedback.json
    """

    def __init__(self, conversation_state: ConversationState) -> None:
        super().__init__()
        self._conversation_state = conversation_state
        self._feedback_accessor = conversation_state.create_property("pending_feedback")
        self._history_accessor = conversation_state.create_property("chat_history")

    async def on_message_activity(self, turn_context: TurnContext) -> None:
        user_message = (turn_context.activity.text or "").strip()

        # ---------- Pending feedback comment ----------
        pending = cast(dict | None, await self._feedback_accessor.get(turn_context, None))
        if pending:
            comment = "" if user_message == "略過" else user_message
            save_feedback(
                response_id=pending["response_id"],
                user_id=getattr(turn_context.activity.from_property, "id", ""),
                rating=pending["rating"],
                comment=comment,
            )
            await self._feedback_accessor.set(turn_context, None)
            await turn_context.send_activity(MessageFactory.text("感謝您的回饋！"))
            await self._conversation_state.save_changes(turn_context)
            return None

        # ---------- Feedback button clicked ----------
        if user_message.startswith("feedback:"):
            _, rating, response_id = (*user_message.split(":", 2), "", "")[:3]
            await self._feedback_accessor.set(turn_context, {"rating": rating, "response_id": response_id})
            prompt = MessageFactory.text("謝謝！請問您有其他意見想補充嗎？")
            prompt.suggested_actions = SuggestedActions(actions=[CardAction(title="略過", type=ActionTypes.im_back, value="略過")])
            await turn_context.send_activity(prompt)
            await self._conversation_state.save_changes(turn_context)
            return None

        # ---------- Normal message ----------
        if user_message.lower() == "hero card":
            await turn_context.send_activity(MessageFactory.attachment(build_hero_card()))

        elif user_message.lower() == "adaptive card":
            await turn_context.send_activity(MessageFactory.attachment(build_adaptive_card()))

        else:
            history = cast(list | None, await self._history_accessor.get(turn_context, None)) or []
            reply_text = await call_ollama(user_message, history)
            history.append({"role": "user", "content": user_message})
            history.append({"role": "assistant", "content": reply_text})
            if len(history) > CONFIG.HISTORY_LIMIT: history = history[-CONFIG.HISTORY_LIMIT:]
            await self._history_accessor.set(turn_context, history)
            response_id = turn_context.activity.id or ""
            reply = MessageFactory.text(reply_text)
            reply.suggested_actions = SuggestedActions(
                actions=[
                    CardAction(title="👍 有幫助", type=ActionTypes.message_back, text=f"feedback:up:{response_id}", display_text="👍 有幫助"),
                    CardAction(title="👎 沒幫助", type=ActionTypes.message_back, text=f"feedback:down:{response_id}", display_text="👎 沒幫助"),
                ]
            )
            await turn_context.send_activity(reply)

        await self._conversation_state.save_changes(turn_context)

    async def on_members_added_activity(self, members_added, turn_context: TurnContext) -> None:
        recipient_id = getattr(turn_context.activity.recipient, "id", "")
        for member in members_added:
            if member.id != recipient_id:
                welcome = MessageFactory.text("歡迎！輸入任何訊息，Bot 將透過 Ollama LLM 回覆您。")
                welcome.suggested_actions = SuggestedActions(
                    actions=[
                        CardAction(title="Hello", type=ActionTypes.im_back, value="Hello"),
                        CardAction(title="Display Hero Card Example", type=ActionTypes.im_back, value="Hero Card"),
                        CardAction(title="Display Adaptive Card Example", type=ActionTypes.im_back, value="Adaptive Card"),
                    ]
                )
                await turn_context.send_activity(welcome)
