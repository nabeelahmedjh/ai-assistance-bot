from __future__ import annotations

import asyncio
from uuid import uuid4

from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from documents.models import ConversationTurn
from documents.services.chat import classify_intent, handle_message


class ChatConsumer(AsyncJsonWebsocketConsumer):
    STREAM_CHUNK_WORDS = 1
    STREAM_DELAY_SECONDS = 0.08
    MIN_STREAM_DURATION_SECONDS = 1.4

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

        payload = await sync_to_async(handle_message)(message, self.lead_id, 3)
        request_id = str(uuid4())

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat.typing",
                "lead_id": self.lead_id,
                "is_typing": True,
            },
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat.stream_start",
                "lead_id": self.lead_id,
                "request_id": request_id,
            },
        )

        tokens = list(self._stream_chunks(payload["answer"]))
        per_token_delay = self.STREAM_DELAY_SECONDS
        if tokens:
            min_delay_for_visible_stream = self.MIN_STREAM_DURATION_SECONDS / len(tokens)
            per_token_delay = max(per_token_delay, min_delay_for_visible_stream)

        for token in tokens:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat.stream_token",
                    "lead_id": self.lead_id,
                    "request_id": request_id,
                    "token": token,
                },
            )
            await asyncio.sleep(per_token_delay)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat.stream_end",
                "lead_id": self.lead_id,
                "request_id": request_id,
            },
        )

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
                "request_id": request_id,
                "response": payload,
            },
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat.typing",
                "lead_id": self.lead_id,
                "is_typing": False,
            },
        )

    async def chat_message(self, event):
        await self.send_json(
            {
                "type": "message",
                "lead_id": event["lead_id"],
                "message_id": event["message_id"],
                "request_id": event.get("request_id"),
                "response": event["response"],
            }
        )

    async def chat_stream_start(self, event):
        await self.send_json(
            {
                "type": "stream_start",
                "lead_id": event["lead_id"],
                "request_id": event["request_id"],
            }
        )

    async def chat_stream_token(self, event):
        await self.send_json(
            {
                "type": "stream_token",
                "lead_id": event["lead_id"],
                "request_id": event["request_id"],
                "token": event["token"],
            }
        )

    async def chat_stream_end(self, event):
        await self.send_json(
            {
                "type": "stream_end",
                "lead_id": event["lead_id"],
                "request_id": event["request_id"],
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

    @staticmethod
    def _stream_chunks(answer: str):
        words = answer.split()
        if not words:
            return

        for i in range(0, len(words), ChatConsumer.STREAM_CHUNK_WORDS):
            chunk = " ".join(words[i : i + ChatConsumer.STREAM_CHUNK_WORDS])
            yield f"{chunk} "
