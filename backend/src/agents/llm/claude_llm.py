# import asyncio
# from contextlib import asynccontextmanager
# from typing import AsyncGenerator, Generator, List, Optional
# from llama_index.llms.anthropic import Anthropic
# from llama_index.core.llms import ChatMessage
# from .base import BaseLLM
# from src.config import Config
# import logging
# from llama_index.core import Settings

# logger = logging.getLogger(__name__)

# class ClaudeLLM(BaseLLM):
#     def __init__(self):
#         config = Config.CLAUDE_CONFIG
#         super().__init__(
#             api_key=config.api_key,
#             model_name=config.model_name,
#             model_id=config.model_id,
#             temperature=config.temperature,
#             max_tokens=config.max_tokens,
#             system_prompt=config.system_prompt
#         )
#         self._initialize_model()

#     def _initialize_model(self) -> None:
#         try:
#             tokenizer = Anthropic().tokenizer
#             Settings.tokenizer = tokenizer
#             self.model = Anthropic(
#                 api_key=self.api_key,
#                 model=self.model_id,
#                 temperature=self.temperature,
#                 max_tokens=self.max_tokens
#             )
#         except Exception as e:
#             logger.error(f"Failed to initialize Claude model: {str(e)}")
#             raise

#     def _prepare_messages(
#         self,
#         query: str,
#         chat_history: Optional[List[ChatMessage]] = None
#     ) -> List[ChatMessage]:
#         messages = []
#         if self.system_prompt:
#             messages.append(ChatMessage(role="system", content=self.system_prompt))
#             messages.append(ChatMessage(role="assistant", content="I understand and will follow these instructions."))
        
#         if chat_history:
#             messages.extend(chat_history)
        
#         messages.append(ChatMessage(role="user", content=query))
#         return messages

#     def _extract_response(self, response) -> str:
#         """Trích xuất text từ response của Claude."""
#         try:
#             if hasattr(response, 'text'):
#                 return response.text
#             elif hasattr(response, 'content'):
#                 return response.content.parts[0].text
#             else:
#                 return response.message.content
#         except Exception as e:
#             logger.error(f"Error extracting response from Claude: {str(e)}")
#             return response.message.content

#     def chat(
#         self,
#         query: str,
#         chat_history: Optional[List[ChatMessage]] = None
#     ) -> str:
#         try:
#             messages = self._prepare_messages(query, chat_history)
#             response = self.model.chat(messages)
#             return self._extract_response(response)
#         except Exception as e:
#             logger.error(f"Error in Claude chat: {str(e)}")
#             raise

#     async def achat(
#         self,
#         query: str,
#         chat_history: Optional[List[ChatMessage]] = None
#     ) -> str:
#         try:
#             messages = self._prepare_messages(query, chat_history)
#             response = await self.model.achat(messages)
#             return self._extract_response(response)
#         except Exception as e:
#             logger.error(f"Error in Claude async chat: {str(e)}")
#             raise

#     def stream_chat(
#         self,
#         query: str,
#         chat_history: Optional[List[ChatMessage]] = None
#     ) -> Generator[str, None, None]:
#         try:
#             messages = self._prepare_messages(query, chat_history)
#             response_stream = self.model.stream_chat(messages)
#             for response in response_stream:
#                 yield self._extract_response(response)
#         except Exception as e:
#             logger.error(f"Error in Claude stream chat: {str(e)}")
#             raise

#     async def astream_chat(
#         self,
#         query: str,
#         chat_history: Optional[List[ChatMessage]] = None
#     ) -> AsyncGenerator[str, None]:
#         try:
#             messages = self._prepare_messages(query, chat_history)
#             response = await self.model.astream_chat(messages)
            
#             if asyncio.iscoroutine(response):
#                 response = await response
            
#             if hasattr(response, '__aiter__'):
#                 async for chunk in response:
#                     yield self._extract_response(chunk)
#             else:
#                 yield self._extract_response(response)
                
#         except Exception as e:
#             logger.error(f"Error in Claude async stream chat: {str(e)}")
#             raise
#     @asynccontextmanager
#     async def session(self):
#         """Context manager để quản lý phiên làm việc với model"""
#         try:
#             yield self
#         finally:
#             # Cleanup code if needed
#             pass