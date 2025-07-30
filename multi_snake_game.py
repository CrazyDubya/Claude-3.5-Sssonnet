"""
Enhanced Snake Game supporting multiple snakes controlled by different LLMs.
"""
import random
import logging
from typing import Dict, List, Tuple, Optional
from collections import deque
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class SnakeStatus(Enum):
    ALIVE = "alive"
    DEAD = "dead"
    COLLISION = "collision"

@dataclass
class Snake:
    """Represents a single snake in the game."""
    id: str
    body: List[Tuple[int, int]]
    direction: Tuple[int, int]
    color: str
    llm_provider_id: str
    status: SnakeStatus = SnakeStatus.ALIVE
    score: int = 0
    message_history: deque = None
    
    def __post_init__(self):
        if self.message_history is None:
            self.message_history = deque(maxlen=60)

@dataclass
class Food:
    """Represents food in the game."""
    position: Tuple[int, int]
    value: int = 1

class MultiSnakeGame:
    """Enhanced snake game supporting multiple AI-controlled snakes."""
    
    def __init__(self, width: int = 20, height: int = 20, max_food: int = 3):
        self.width = width
        self.height = height
        self.max_food = max_food
        self.snakes: Dict[str, Snake] = {}
        self.food: List[Food] = []
        self.game_tick = 0
        self.game_over = False
        
        # Available colors for snakes
        self.snake_colors = [
            "#10b981",  # Primary green
            "#f43f5e",  # Rose
            "#3b82f6",  # Blue
            "#f59e0b",  # Amber
            "#8b5cf6",  # Violet
            "#06b6d4",  # Cyan
            "#f97316",  # Orange
            "#ef4444",  # Red
        ]
        self.color_index = 0
        
        self._generate_initial_food()
    
    def add_snake(self, snake_id: str, llm_provider_id: str, start_pos: Optional[Tuple[int, int]] = None) -> bool:
        """Add a new snake to the game."""
        if snake_id in self.snakes:
            logger.warning(f"Snake {snake_id} already exists")
            return False
        
        if len(self.snakes) >= len(self.snake_colors):
            logger.warning(f"Maximum number of snakes ({len(self.snake_colors)}) reached")
            return False
        
        # Generate a safe starting position if not provided
        if start_pos is None:
            start_pos = self._generate_safe_start_position()
        
        # Get color for this snake
        color = self.snake_colors[self.color_index % len(self.snake_colors)]
        self.color_index += 1
        
        snake = Snake(
            id=snake_id,
            body=[start_pos],
            direction=(1, 0),  # Start moving right
            color=color,
            llm_provider_id=llm_provider_id,
            message_history=deque(maxlen=60)
        )
        
        self.snakes[snake_id] = snake
        logger.info(f"Added snake {snake_id} controlled by {llm_provider_id}")
        return True
    
    def remove_snake(self, snake_id: str) -> bool:
        """Remove a snake from the game."""
        if snake_id in self.snakes:
            del self.snakes[snake_id]
            logger.info(f"Removed snake {snake_id}")
            return True
        return False
    
    def _generate_safe_start_position(self) -> Tuple[int, int]:
        """Generate a starting position that doesn't conflict with existing snakes or food."""
        occupied_positions = set()
        
        # Add all snake body positions
        for snake in self.snakes.values():
            occupied_positions.update(snake.body)
        
        # Add food positions
        for food in self.food:
            occupied_positions.add(food.position)
        
        # Try to find a safe position
        for _ in range(100):  # Max attempts
            pos = (random.randint(2, self.width - 3), random.randint(2, self.height - 3))
            if pos not in occupied_positions:
                return pos
        
        # Fallback to center if no safe position found
        return (self.width // 2, self.height // 2)
    
    def _generate_initial_food(self):
        """Generate initial food items."""
        for _ in range(self.max_food):
            self._add_food()
    
    def _add_food(self):
        """Add a new food item to the game."""
        occupied_positions = set()
        
        # Add all snake body positions
        for snake in self.snakes.values():
            occupied_positions.update(snake.body)
        
        # Add existing food positions
        for food in self.food:
            occupied_positions.add(food.position)
        
        # Try to find a position for new food
        for _ in range(100):  # Max attempts
            pos = (random.randint(0, self.width - 1), random.randint(0, self.height - 1))
            if pos not in occupied_positions:
                self.food.append(Food(position=pos))
                return
        
        logger.warning("Could not place new food - game area too crowded")
    
    def move_snake(self, snake_id: str, direction: str) -> bool:
        """Move a specific snake in the given direction."""
        if snake_id not in self.snakes:
            return False
        
        snake = self.snakes[snake_id]
        if snake.status != SnakeStatus.ALIVE:
            return False
        
        # Convert direction string to vector
        direction_map = {
            "up": (0, -1),
            "down": (0, 1),
            "left": (-1, 0),
            "right": (1, 0)
        }
        
        if direction not in direction_map:
            return False
        
        new_direction = direction_map[direction]
        
        # Prevent moving in opposite direction (suicide move)
        if (new_direction[0] * -1, new_direction[1] * -1) != snake.direction:
            snake.direction = new_direction
        
        return self._update_snake(snake)
    
    def _update_snake(self, snake: Snake) -> bool:
        """Update a snake's position and handle collisions."""
        head = snake.body[0]
        new_head = (
            (head[0] + snake.direction[0]) % self.width,
            (head[1] + snake.direction[1]) % self.height
        )
        
        # Check for self-collision
        if new_head in snake.body[1:]:
            snake.status = SnakeStatus.COLLISION
            logger.info(f"Snake {snake.id} collided with itself")
            return False
        
        # Check for collision with other snakes
        for other_id, other_snake in self.snakes.items():
            if other_id != snake.id and other_snake.status == SnakeStatus.ALIVE:
                if new_head in other_snake.body:
                    snake.status = SnakeStatus.COLLISION
                    logger.info(f"Snake {snake.id} collided with snake {other_id}")
                    return False
        
        # Move the snake
        snake.body.insert(0, new_head)
        
        # Check for food consumption
        food_eaten = None
        for food in self.food:
            if new_head == food.position:
                food_eaten = food
                break
        
        if food_eaten:
            # Snake grows (don't remove tail)
            snake.score += food_eaten.value
            self.food.remove(food_eaten)
            self._add_food()  # Add new food
            logger.info(f"Snake {snake.id} ate food, score: {snake.score}")
        else:
            # Snake doesn't grow (remove tail)
            snake.body.pop()
        
        return True
    
    def tick(self) -> Dict[str, any]:
        """Advance the game by one tick. Returns game state."""
        self.game_tick += 1
        
        # Check if game should end (all snakes dead or only one alive)
        alive_snakes = [s for s in self.snakes.values() if s.status == SnakeStatus.ALIVE]
        
        if len(alive_snakes) <= 1 and len(self.snakes) > 1:
            self.game_over = True
            if alive_snakes:
                logger.info(f"Game over! Winner: {alive_snakes[0].id}")
            else:
                logger.info("Game over! No survivors")
        elif len(alive_snakes) == 0:
            self.game_over = True
            logger.info("Game over! All snakes died")
        
        return self.get_state()
    
    def get_state(self) -> Dict[str, any]:
        """Get the current game state."""
        return {
            "width": self.width,
            "height": self.height,
            "snakes": {
                snake_id: {
                    "body": snake.body,
                    "direction": snake.direction,
                    "color": snake.color,
                    "status": snake.status.value,
                    "score": snake.score,
                    "llm_provider": snake.llm_provider_id
                }
                for snake_id, snake in self.snakes.items()
            },
            "food": [{"position": f.position, "value": f.value} for f in self.food],
            "game_tick": self.game_tick,
            "game_over": self.game_over
        }
    
    def get_snake_perspective(self, snake_id: str) -> Dict[str, any]:
        """Get game state from a specific snake's perspective."""
        if snake_id not in self.snakes:
            return {}
        
        snake = self.snakes[snake_id]
        state = self.get_state()
        
        # Add information relevant to this snake
        state["current_snake"] = {
            "id": snake_id,
            "body": snake.body,
            "direction": snake.direction,
            "score": snake.score,
            "status": snake.status.value
        }
        
        return state
    
    def add_message_to_snake_history(self, snake_id: str, message: str):
        """Add a message to a snake's history."""
        if snake_id in self.snakes:
            self.snakes[snake_id].message_history.append(message)