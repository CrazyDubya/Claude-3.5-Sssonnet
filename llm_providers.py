"""
LLM provider abstraction layer for supporting multiple AI services.
"""
import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class LLMResponse:
    """Standardized response from any LLM provider."""
    thinking: Optional[str] = None
    direction: Optional[str] = None
    error: Optional[str] = None

class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def get_move(self, context: str, game_state: Dict[str, Any], message_history: List[str]) -> LLMResponse:
        """Get the next move from the LLM."""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the name of the LLM provider."""
        pass

class AnthropicProvider(LLMProvider):
    """Anthropic Claude LLM provider."""
    
    def __init__(self, api_key: str, model: str = "claude-3-5-haiku-20241022"):
        from anthropic import Anthropic
        self.client = Anthropic(api_key=api_key)
        self.model = model
    
    async def get_move(self, context: str, game_state: Dict[str, Any], message_history: List[str]) -> LLMResponse:
        """Get move from Claude."""
        try:
            # Prepare the context with game state and message history
            full_context = f"You are a sassy, witty snake in a 20x20 Snake game. You're living your best serpentine life! The current game state is: {game_state}. "
            full_context += "You can wrap around the board. "
            full_context += "That food is calling your name - better get there before it goes bad! No pressure, just your entire existence at stake. 🙄 "
            full_context += "Use the move_snake tool to work that body! Up, down, left, right - the dance floor is yours! "
            full_context += "Give us your sassy thought process behind your next move (max 5 words). "
            full_context += "Drop a spicy one-liner about your fabulous life as a snake (5 words max)."
            
            if message_history:
                full_context += "\nPrevious moves:\n"
                for msg in message_history:
                    full_context += f"- {msg}\n"

            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                temperature=0.5,
                tools=[{
                    "name": "move_snake",
                    "description": "This tool moves the snake in the Snake game in the specified direction. Use this tool when deciding the next move for the snake to avoid obstacles and eat the food. The direction parameter specifies which way the snake should move and can be 'up', 'down', 'left', or 'right'. Ensure that the snake does not move in the opposite direction of its current movement to avoid an immediate collision.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "direction": {
                                "type": "string",
                                "enum": ["up", "down", "left", "right"],
                                "description": "The direction to move the snake"
                            }
                        },
                        "required": ["direction"]
                    }
                }],
                tool_choice={"type": "auto"},
                messages=[{
                    "role": "user",
                    "content": full_context
                }]
            )

            # Extract thinking and tool use blocks
            thinking_block = next((block for block in response.content if block.type == "text"), None)
            tool_use_block = next((block for block in response.content if block.type == "tool_use"), None)

            thinking = thinking_block.text if thinking_block else None
            direction = tool_use_block.input["direction"] if tool_use_block else None

            return LLMResponse(thinking=thinking, direction=direction)

        except Exception as e:
            logger.error(f"Error getting move from Anthropic: {e}")
            return LLMResponse(error=str(e))
    
    def get_provider_name(self) -> str:
        return f"Claude-{self.model}"

class OllamaProvider(LLMProvider):
    """Ollama local LLM provider."""
    
    def __init__(self, model: str = "llama2", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        # We'll implement a simple HTTP client for Ollama
        import httpx
        self.client = httpx.AsyncClient()
    
    async def get_move(self, context: str, game_state: Dict[str, Any], message_history: List[str]) -> LLMResponse:
        """Get move from Ollama."""
        try:
            # Prepare the context
            full_context = f"You are playing Snake. Current game state: {game_state}. "
            full_context += "You can wrap around the board. "
            full_context += "Choose your next move: up, down, left, or right. "
            full_context += "Respond with EXACTLY this format: 'THINKING: [your thought] MOVE: [direction]' "
            full_context += "For example: 'THINKING: Food is above me MOVE: up'"
            
            if message_history:
                full_context += f"\nPrevious moves: {', '.join(message_history[-5:])}"

            payload = {
                "model": self.model,
                "prompt": full_context,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "max_tokens": 150
                }
            }

            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "").strip()
                
                # Parse the response
                thinking = None
                direction = None
                
                if "THINKING:" in response_text and "MOVE:" in response_text:
                    parts = response_text.split("MOVE:")
                    thinking_part = parts[0].replace("THINKING:", "").strip()
                    direction_part = parts[1].strip().lower()
                    
                    thinking = thinking_part
                    if direction_part in ["up", "down", "left", "right"]:
                        direction = direction_part
                
                if not direction:
                    # Fallback: try to extract direction from response
                    response_lower = response_text.lower()
                    for dir_option in ["up", "down", "left", "right"]:
                        if dir_option in response_lower:
                            direction = dir_option
                            break
                    
                    if not direction:
                        # Random fallback
                        import random
                        direction = random.choice(["up", "down", "left", "right"])
                        thinking = "Random move (parsing failed)"

                return LLMResponse(thinking=thinking, direction=direction)
            else:
                raise Exception(f"Ollama API returned status {response.status_code}")

        except Exception as e:
            logger.error(f"Error getting move from Ollama: {e}")
            # Fallback to random move
            import random
            direction = random.choice(["up", "down", "left", "right"])
            return LLMResponse(
                thinking=f"Error occurred: {str(e)[:50]}...", 
                direction=direction,
                error=str(e)
            )
    
    def get_provider_name(self) -> str:
        return f"Ollama-{self.model}"

class LLMManager:
    """Manages multiple LLM providers and their configurations."""
    
    def __init__(self):
        self.providers: Dict[str, LLMProvider] = {}
        self._setup_default_providers()
    
    def _setup_default_providers(self):
        """Setup default LLM providers based on available configurations."""
        # Setup Anthropic if API key is available
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            try:
                self.providers["claude-haiku"] = AnthropicProvider(anthropic_key, "claude-3-5-haiku-20241022")
                self.providers["claude-sonnet"] = AnthropicProvider(anthropic_key, "claude-3-5-sonnet-20240620")
                logger.info("Anthropic providers initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic providers: {e}")
        
        # Setup Ollama providers (we'll try common models)
        try:
            # Only add if we detect Ollama is running (for now, we'll add them anyway)
            self.providers["ollama-llama2"] = OllamaProvider("llama2")
            self.providers["ollama-llama3"] = OllamaProvider("llama3")
            self.providers["ollama-codellama"] = OllamaProvider("codellama")
            logger.info("Ollama providers initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Ollama providers: {e}")
    
    def get_provider(self, provider_id: str) -> Optional[LLMProvider]:
        """Get a specific LLM provider by ID."""
        return self.providers.get(provider_id)
    
    def list_providers(self) -> List[str]:
        """List all available provider IDs."""
        return list(self.providers.keys())
    
    def add_provider(self, provider_id: str, provider: LLMProvider):
        """Add a custom LLM provider."""
        self.providers[provider_id] = provider
    
    def get_default_provider(self) -> LLMProvider:
        """Get the default LLM provider."""
        # Prefer Claude if available, otherwise use first available
        if "claude-haiku" in self.providers:
            return self.providers["claude-haiku"]
        elif self.providers:
            return next(iter(self.providers.values()))
        else:
            raise Exception("No LLM providers available")