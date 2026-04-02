from __future__ import annotations

from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from documents.models import ConversationTurn
from documents.services.chat import classify_intent, generate_structured_reply
from documents.services.prompting import build_prompt
from documents.services.retrieval import retrieve_context


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.lead_id = self.scope["url_route"]["kwargs"]["lead_id"]
        self.room_group_name = f"chat_{self.lead_id}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        event_type = content.get("type")

        if event_type == "typing":
            await self._handle_typing(content)
            return

        if event_type == "message":
            await self._handle_message(content)
            return

        await self.send_json({
            "type": "error",
            "error": "Unsupported event type. Use 'message' or 'typing'.",
        })

    async def _handle_typing(self, content: dict):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat.typing",
                "lead_id": self.lead_id,
                "is_typing": bool(content.get("is_typing", False)),
            },
        )

    async def _handle_message(self, content: dict):
        message = (content.get("message") or "").strip()
        if not message:
            await self.send_json({"type": "error", "error": "Message must not be empty."})
            return

        user_intent = await sync_to_async(classify_intent)(message)
        await self._create_user_turn(message=message, intent=user_intent)

        context = await sync_to_async(retrieve_context)(message, 3)
        prompt = await sync_to_async(build_prompt)(message, context)
        payload = await sync_to_async(generate_structured_reply)(message, context, user_intent)
        payload["prompt_preview"] = prompt[:500]

        assistant_turn_id = await self._create_assistant_turn(
            answer=payload["answer"],
            intent=user_intent,
            payload=payload,
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat.message",
                "lead_id": self.lead_id,
                "message_id": assistant_turn_id,
                "response": payload,
            },
        )

    async def chat_message(self, event):
        await self.send_json(
            {
                "type": "message",
                "lead_id": event["lead_id"],
                "message_id": event["message_id"],
                "response": event["response"],
            }
        )

    async def chat_typing(self, event):
        await self.send_json(
            {
                "type": "typing",
                "lead_id": event["lead_id"],
                "is_typing": event["is_typing"],
            }
        )

    @database_sync_to_async
    def _create_user_turn(self, message: str, intent: str):
        ConversationTurn.objects.create(
            lead_id=self.lead_id,
            role="user",
            message=message,
            intent=intent,
        )

    @database_sync_to_async
    def _create_assistant_turn(self, answer: str, intent: str, payload: dict) -> int:
        turn = ConversationTurn.objects.create(
            lead_id=self.lead_id,
            role="assistant",
            message=answer,
            intent=intent,
            response_payload=payload,
        )
        return turn.id
