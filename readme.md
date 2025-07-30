# 🐍 Claude 3.5 Sssonnet: Multi-LLM AI Snake Arena 🧠

Welcome to the most advanced AI-powered snake game ever created! This isn't just snake – it's a battlefield where different AI models compete, collaborate, and showcase their decision-making prowess in real-time.

## 🚀 What's This All About?

Ever wondered how different AI models would play Snake against each other? Now you can find out! We've created a multi-LLM arena where Claude, Ollama models, and other AI providers can control their own snakes simultaneously in epic battles of artificial intelligence.

### 🧠 Revolutionary Features

- **🤖 Multi-LLM Support**: Claude (Anthropic), Ollama local models, and extensible architecture for more
- **🐍 Multi-Snake Arena**: Watch multiple AI-controlled snakes compete in the same game
- **⚡ Real-Time AI Thoughts**: See exactly what each AI is thinking as it plays
- **🎮 Dual Game Modes**: Classic single-snake mode or chaotic multi-snake battles
- **🎨 Dynamic UI**: Color-coded snakes, provider identification, and live statistics
- **🔧 Extensible Architecture**: Easy to add new LLM providers and game features
- **📊 Live Analytics**: Track scores, survival rates, and AI performance

## 🛠️ Tech Stack

- **Backend**: Python with FastAPI and WebSocket support
- **Frontend**: HTML5 Canvas with Tailwind CSS
- **AI Integration**: Anthropic Claude API + Ollama local models
- **Real-time Communication**: WebSocket protocol for live updates
- **Architecture**: Modular LLM provider system

## 🚦 Getting Started

### Prerequisites
- Python 3.8+
- (Optional) Ollama installed locally for local LLM support
- (Optional) Anthropic API key for Claude models

### Installation

1. **Clone the battlefield**:
   ```bash
   git clone https://github.com/CrazyDubya/Claude-3.5-Sssonnet.git
   cd Claude-3.5-Sssonnet
   ```

2. **Install requirements**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your arsenal**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and preferences
   ```

4. **Launch the arena**:
   ```bash
   python snake.py
   ```

5. **Enter the battlefield**: Open `http://localhost:8000`

### Environment Configuration

Create a `.env` file with your preferred settings:

```bash
# Game Mode: "single" for classic mode, "multi" for AI arena
GAME_MODE=multi

# Auto-tick speed (seconds between moves)
AUTO_TICK=1.5

# API Keys (optional - system will work with available providers)
ANTHROPIC_API_KEY=your_key_here
OLLAMA_BASE_URL=http://localhost:11434

# Default snakes to spawn in multi mode
DEFAULT_SNAKES=claude-haiku,ollama-llama2,ollama-llama3
```

## 🎮 Game Modes

### 🐍 Single Snake Mode (Classic)
The original experience with one AI-controlled snake. Perfect for watching a single AI's decision-making process.

### 🏟️ Multi-Snake Arena Mode (New!)
Multiple AI models control their own snakes simultaneously:
- Watch different AI strategies unfold
- See how models react to competition
- Observe emergent behaviors and interactions
- Compare performance across different providers

## 🤖 Supported LLM Providers

### ✅ Currently Integrated
- **Anthropic Claude**: Haiku, Sonnet models via API
- **Ollama**: Local models (Llama 2, Llama 3, CodeLlama, etc.)

### 🚧 Planned Integrations
- OpenAI GPT models
- Google Gemini/Bard
- Hugging Face models
- Custom model APIs

## 🎯 Features

### Real-Time AI Insights
- **Live Thinking**: See each AI's thought process in real-time
- **Decision Tracking**: Watch move decisions with reasoning
- **Provider Attribution**: Know which AI made which move
- **Error Handling**: Graceful handling of AI provider issues

### Advanced Gameplay
- **Multi-Food System**: Multiple food items on the board
- **Collision Detection**: Smart collision handling between snakes
- **Wrap-Around Movement**: Snakes can wrap around board edges
- **Dynamic Snake Addition**: Add new AI snakes during gameplay
- **Game Statistics**: Live tracking of scores and survival

### Developer-Friendly
- **Modular Architecture**: Easy to extend with new providers
- **REST API**: Programmatic control over game state
- **WebSocket Protocol**: Real-time updates and communication
- **Comprehensive Logging**: Detailed logs for debugging

## 🔬 For AI Researchers & Enthusiasts

This project is a fascinating laboratory for:
- **AI Decision Making**: Observe how different models approach the same problem
- **Strategy Comparison**: Compare strategies across different AI architectures
- **Real-time Adaptation**: Watch AIs adapt to changing game states
- **Multi-agent Scenarios**: Study interactions between multiple AI agents
- **Model Performance**: Benchmark different models in a controlled environment

## 🛠️ Development

### Adding New LLM Providers

1. **Implement the Provider Interface**:
   ```python
   from llm_providers import LLMProvider, LLMResponse
   
   class MyLLMProvider(LLMProvider):
       async def get_move(self, context, game_state, history):
           # Your implementation here
           return LLMResponse(thinking="...", direction="up")
   ```

2. **Register Your Provider**:
   ```python
   llm_manager.add_provider("my-llm", MyLLMProvider())
   ```

### Running in Development
```bash
# Enable hot reloading and debug mode
GAME_MODE=multi DEBUG=true python snake.py
```

### Testing
```bash
# Run the test suite (coming soon)
python -m pytest tests/
```

## 📊 API Endpoints

- `GET /api/providers` - List available LLM providers
- `GET /api/game-state` - Get current game state
- `POST /api/add-snake` - Add a new AI snake to the arena
- `WebSocket /ws` - Real-time game communication

## 🤝 Contributing

We're building the future of AI gaming! Contributions welcome:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit your changes**: `git commit -m 'Add amazing feature'`
4. **Push to the branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Contribution Ideas
- New LLM provider integrations
- Advanced game features (power-ups, obstacles)
- Performance optimizations
- UI/UX improvements
- Documentation and tutorials

## 📈 Roadmap

See our comprehensive [TODO.md](TODO.md) for detailed development plans including:
- 🎮 Advanced gameplay features
- 🔧 Performance optimizations  
- 🎨 Visual enhancements
- 🤖 Additional AI providers
- 📊 Analytics and monitoring
- 🚀 Deployment improvements

## 📜 License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

## 🎉 Acknowledgments

- Anthropic for the amazing Claude API
- Ollama community for local LLM capabilities
- The open-source AI community for inspiration
- Snake game creators everywhere 🐍

---

**Ready to watch AIs battle it out in the ultimate snake arena? Clone, configure, and let the games begin!** 🎮🐍🤖

*Remember: In this arena, it's not just about eating pixels – it's about showcasing the power of artificial intelligence!* 🧠✨
