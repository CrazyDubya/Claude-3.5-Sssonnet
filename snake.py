from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv
import random
import os
import asyncio
import json
import logging
from collections import deque
from typing import Dict, List

from llm_providers import LLMManager, LLMResponse
from multi_snake_game import MultiSnakeGame, SnakeStatus

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create static and templates directories if they don't exist
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize LLM manager and game
llm_manager = LLMManager()
game = MultiSnakeGame(20, 20)

# Game configuration
GAME_MODE = os.getenv("GAME_MODE", "single")  # "single" or "multi"
AUTO_TICK = float(os.getenv("AUTO_TICK", "1.0"))  # Seconds between automatic moves

# Active WebSocket connections
active_connections: List[WebSocket] = []

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_to_all(self, data: dict):
        """Send data to all connected clients."""
        if self.active_connections:
            message = json.dumps(data)
            disconnected = []
            for connection in self.active_connections:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.error(f"Error sending to client: {e}")
                    disconnected.append(connection)
            
            # Remove disconnected clients
            for conn in disconnected:
                self.disconnect(conn)

manager = ConnectionManager()

# Game state for legacy single-snake mode
class LegacySnakeGame:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.snake = [(width // 2, height // 2)]
        self.direction = (1, 0)
        self.food = self.generate_food()
        self.message_history = deque(maxlen=60)

    def generate_food(self):
        while True:
            food = (random.randint(0, self.width - 1), random.randint(0, self.height - 1))
            if food not in self.snake:
                return food

    def move(self):
        head = self.snake[0]
        new_head = ((head[0] + self.direction[0]) % self.width, (head[1] + self.direction[1]) % self.height)
        
        if new_head in self.snake[1:]:
            return False  # Game over
        
        self.snake.insert(0, new_head)
        
        if new_head == self.food:
            self.food = self.generate_food()
        else:
            self.snake.pop()
        
        return True

    def change_direction(self, new_direction):
        if (new_direction[0] * -1, new_direction[1] * -1) != self.direction:
            self.direction = new_direction

    def get_state(self):
        return {
            "snake": self.snake,
            "food": self.food,
            "width": self.width,
            "height": self.height
        }

    def add_to_history(self, message):
        self.message_history.append(message)

# Initialize legacy game for backward compatibility
legacy_game = LegacySnakeGame(20, 20)

@app.get("/")
async def get():
    with open('templates/index.html', 'r') as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

@app.get("/api/providers")
async def get_providers():
    """Get list of available LLM providers."""
    providers = []
    for provider_id in llm_manager.list_providers():
        provider = llm_manager.get_provider(provider_id)
        if provider:
            providers.append({
                "id": provider_id,
                "name": provider.get_provider_name()
            })
    return {"providers": providers}

@app.get("/api/game-state")
async def get_game_state():
    """Get current game state."""
    if GAME_MODE == "multi":
        return game.get_state()
    else:
        return legacy_game.get_state()

@app.post("/api/add-snake")
async def add_snake(request: dict):
    """Add a new snake to the multi-snake game."""
    if GAME_MODE != "multi":
        raise HTTPException(status_code=400, detail="Multi-snake mode not enabled")
    
    snake_id = request.get("snake_id")
    llm_provider_id = request.get("llm_provider_id")
    
    if not snake_id or not llm_provider_id:
        raise HTTPException(status_code=400, detail="snake_id and llm_provider_id required")
    
    if llm_provider_id not in llm_manager.list_providers():
        raise HTTPException(status_code=400, detail="Invalid LLM provider")
    
    success = game.add_snake(snake_id, llm_provider_id)
    if success:
        # Notify all clients about the new snake
        await manager.send_to_all({
            "type": "snake_added",
            "snake_id": snake_id,
            "llm_provider_id": llm_provider_id,
            "game_state": game.get_state()
        })
        return {"success": True, "message": f"Snake {snake_id} added"}
    else:
        raise HTTPException(status_code=400, detail="Failed to add snake")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    logger.info("WebSocket connection accepted")
    
    try:
        if GAME_MODE == "multi":
            await handle_multi_snake_game(websocket)
        else:
            await handle_legacy_game(websocket)
    except WebSocketDisconnect:
        logger.info("Client disconnected")
        manager.disconnect(websocket)

async def handle_multi_snake_game(websocket: WebSocket):
    """Handle WebSocket for multi-snake game mode."""
    while True:
        if game.game_over:
            await manager.send_to_all({"type": "game_over", "final_state": game.get_state()})
            break
        
        # Process moves for all alive snakes
        move_tasks = []
        for snake_id, snake in game.snakes.items():
            if snake.status == SnakeStatus.ALIVE:
                task = asyncio.create_task(handle_snake_move(snake_id))
                move_tasks.append(task)
        
        if move_tasks:
            # Wait for all snakes to make their moves
            await asyncio.gather(*move_tasks, return_exceptions=True)
        
        # Update game state and send to all clients
        game_state = game.tick()
        await manager.send_to_all({"type": "game_state", "state": game_state})
        
        # Wait before next tick
        await asyncio.sleep(AUTO_TICK)

async def handle_snake_move(snake_id: str):
    """Handle move for a specific snake."""
    try:
        snake = game.snakes[snake_id]
        provider = llm_manager.get_provider(snake.llm_provider_id)
        
        if not provider:
            logger.error(f"No provider found for snake {snake_id}")
            return
        
        # Get game state from this snake's perspective
        game_state = game.get_snake_perspective(snake_id)
        message_history = list(snake.message_history)
        
        # Get move from LLM
        logger.info(f"Asking {provider.get_provider_name()} for next move for snake {snake_id}...")
        
        response = await provider.get_move("", game_state, message_history)
        
        if response.thinking:
            logger.info(f"Snake {snake_id} thinking: {response.thinking}")
            await manager.send_to_all({
                "type": "snake_thinking",
                "snake_id": snake_id,
                "thought": response.thinking,
                "provider": provider.get_provider_name()
            })
        
        if response.direction:
            logger.info(f"Snake {snake_id} decided to move: {response.direction}")
            
            # Send tool usage message
            await manager.send_to_all({
                "type": "tool_usage",
                "snake_id": snake_id,
                "direction": response.direction,
                "provider": provider.get_provider_name()
            })
            
            # Add the move to the snake's history
            game.add_message_to_snake_history(snake_id, f"Moved {response.direction}")
            
            # Execute the move
            success = game.move_snake(snake_id, response.direction)
            if not success:
                logger.info(f"Snake {snake_id} move failed or died")
        
        if response.error:
            logger.error(f"Error from {provider.get_provider_name()} for snake {snake_id}: {response.error}")
            await manager.send_to_all({
                "type": "snake_error",
                "snake_id": snake_id,
                "error": response.error,
                "provider": provider.get_provider_name()
            })

    except Exception as e:
        logger.error(f"Error handling move for snake {snake_id}: {e}")

async def handle_legacy_game(websocket: WebSocket):
    """Handle WebSocket for legacy single-snake game mode."""
    while True:
        await handle_next_move_legacy(websocket)

async def handle_next_move_legacy(websocket: WebSocket):
    """Handle next move for legacy single-snake mode."""
    try:
        logger.info("Asking Claude for next move...")
        
        provider = llm_manager.get_default_provider()
        game_state = legacy_game.get_state()
        message_history = list(legacy_game.message_history)
        
        response = await provider.get_move("", game_state, message_history)

        if response.thinking:
            logger.info(f"Claude's thought process: {response.thinking}")
            await websocket.send_json({"type": "claude_thinking", "thought": response.thinking})

        if response.direction:
            logger.info(f"Claude decided to move: {response.direction}")

            # Send tool usage message
            await websocket.send_json({"type": "tool_usage", "direction": response.direction})

            # Add the move to the game's message history
            legacy_game.add_to_history(f"Moved {response.direction}")

            if response.direction == "up":
                legacy_game.change_direction((0, -1))
            elif response.direction == "down":
                legacy_game.change_direction((0, 1))
            elif response.direction == "left":
                legacy_game.change_direction((-1, 0))
            elif response.direction == "right":
                legacy_game.change_direction((1, 0))

            if not legacy_game.move():
                logger.info("Game over")
                await websocket.send_json({"type": "game_over"})
            else:
                game_state = legacy_game.get_state()
                logger.info(f"Sending game state: {game_state}")
                await websocket.send_json({"type": "game_state", "state": game_state})
        
        if response.error:
            logger.error(f"Error from LLM: {response.error}")
            await websocket.send_json({"type": "error", "message": response.error})

        # Add a delay to slow down the game
        await asyncio.sleep(AUTO_TICK)

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        await websocket.send_json({"type": "error", "message": str(e)})

if __name__ == "__main__":
    import uvicorn
    
    # Initialize default snakes for multi-snake mode
    if GAME_MODE == "multi":
        available_providers = llm_manager.list_providers()
        if available_providers:
            # Add up to 3 snakes with different providers
            for i, provider_id in enumerate(available_providers[:3]):
                snake_id = f"snake_{i+1}"
                success = game.add_snake(snake_id, provider_id)
                if success:
                    logger.info(f"Added default snake {snake_id} with provider {provider_id}")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)