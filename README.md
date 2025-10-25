# AI Werewolf Game - 9 Players Standard Edition

An AI-powered Werewolf (Mafia) game supporting human vs AI gameplay, using various AI models from AWS Bedrock as AI players.

## ✨ Features

- **9-Player Standard Setup**: 3 Werewolves + 3 Villagers + 3 Special Roles (Seer, Witch, Hunter)
- **Multiple Game Modes**:
  - Pure AI vs AI (spectator mode)
  - 1 Human + 8 AI players
  - Custom configuration (1-9 human players)
- **Diverse AI Models**: Uses 9 different AWS Bedrock AI models, each with unique thinking patterns
- **Complete Game Flow**: Night actions, day discussions, voting, and more

## 🎭 Roles Configuration

### Werewolf Team
- **3 Werewolves**
  - Discuss tactics and kill 1 player each night
  - Know each other's identities
  - Win condition: Eliminate all special roles OR all villagers

### Special Roles (Good Team)
- **Seer** (Prophet)
  - Can check 1 player's identity each night (Good/Werewolf)
  - Guide the good team during discussions

- **Witch**
  - Has 1 Antidote (save the killed player)
  - Has 1 Poison (kill 1 player)
  - Can only use 1 potion per night
  - Cannot save themselves

- **Hunter**
  - When killed by werewolves or voted out, can shoot 1 player
  - Cannot shoot if poisoned by witch

### Villagers
- **3 Villagers**
  - No special abilities
  - Find werewolves through logical reasoning

## 🤖 AI Model Assignment

Default AI model distribution when all players are AI:

| Role | AI Model |
|------|----------|
| Werewolf 1 | claude-opus-4-20250514 |
| Werewolf 2 | claude-sonnet-4-5-20250929 |
| Werewolf 3 | claude-3-7-sonnet-20250219 |
| Seer | claude-opus-4-1-20250805 |
| Witch | claude-sonnet-4-20250514 |
| Hunter | claude-sonnet-4-5-20250929 |
| Villager 1 | claude-haiku-4-5-20251001 |
| Villager 2 | claude-3-7-sonnet-20250219 |
| Villager 3 | claude-haiku-4-5-20251001 |

**Note**: DeepSeek and Claude 3.5 Sonnet models have been removed as they are not available in the current AWS region.

## 📦 Installation

### Prerequisites

- Python 3.8+
- AWS Account with configured credentials
- Access to AWS Bedrock service

### Setup Steps

1. Clone or download the project:
```bash
cd open_werewolf
```

2. Create virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure AWS credentials:

Ensure your AWS credentials are properly configured using one of these methods:

- **Method 1: AWS CLI Configuration**
  ```bash
  aws configure
  ```

- **Method 2: Environment Variables**
  ```bash
  export AWS_ACCESS_KEY_ID=your_access_key
  export AWS_SECRET_ACCESS_KEY=your_secret_key
  export AWS_DEFAULT_REGION=us-west-2
  ```

- **Method 3: .env File**
  ```bash
  cp .env.example .env
  # Edit .env file and fill in your AWS credentials
  ```

## 🎮 Usage

### Starting the Game

```bash
python main.py
```

### Game Mode Selection

After starting, select the number of human players:

- **0** - Pure AI battle (spectator mode): Watch 9 AIs play against each other
- **1** - 1 human player + 8 AI players: You participate in the game
- **2-9** - Custom number of human players

### Game Flow

1. **Role Assignment**: Roles are randomly assigned at game start
2. **Night Phase**:
   - Werewolves discuss and choose kill target
   - Seer checks a player's identity
   - Witch decides whether to use antidote or poison
3. **Day Phase**:
   - Announce deaths
   - Last words from dead players
   - Players speak in turn
   - Vote to exile a player
4. **Repeat steps 2-3 until game ends**

### Human Player Actions

If you're a human player, when it's your turn:

- **Night Actions**: Enter player number based on prompts (e.g., 1)
- **Day Speech**: Enter your speech content
- **Voting**: Enter the player number you want to vote for

## 📁 Project Structure

```
open_werewolf/
├── main.py                 # Main entry point
├── requirements.txt        # Dependencies
├── README.md              # Documentation
├── CHANGELOG.md           # Update history
├── QUICK_START.md         # Quick start guide
├── .env.example           # Environment variables example
├── .gitignore            # Git ignore file
├── docs/                 # Technical documentation
│   ├── GAMEPLAY.md       # Gameplay rules
│   ├── FAQ.md           # Frequently asked questions
│   └── ...
└── src/
    ├── __init__.py
    ├── game/             # Game logic
    │   ├── __init__.py
    │   └── werewolf_game.py
    ├── models/           # Role models
    │   ├── __init__.py
    │   └── roles.py
    ├── players/          # Player system
    │   ├── __init__.py
    │   └── player.py
    └── utils/            # Utility modules
        ├── __init__.py
        └── llm_client.py
```

## 🚀 Key Features

- **Werewolf Night Tactics Discussion**: Werewolves discuss strategy before killing
- **Day Strategy Planning**: Coordinate deception tactics during the day
- **Secret Voting System**: All players vote simultaneously without seeing others' choices
- **Proper Last Words Rules**: Only first night and voted-out players get last words
- **Logical Consistency Checks**: AI maintains consistent behavior with their claims
- **Tactical Flexibility**: AI can break patterns when victory is assured (werewolf rush)
- **Object-Oriented Design**: Clean class hierarchy
- **AI Memory System**: AI players remember key game information
- **Intelligent Decision-Making**: Reasoning and decisions based on large language models
- **Complete Rules Implementation**: Strictly follows 9-player standard rules

## ⚠️ Important Notes

1. **AWS Costs**: Using AWS Bedrock incurs charges, monitor your usage
2. **Model Availability**: Ensure your AWS account has access to all used models
3. **Game Duration**: Pure AI battles may be lengthy, patience recommended
4. **Network Connection**: Requires stable connection to AWS services

## 🛠️ Development

### Adding New Models

Modify the `DEFAULT_MODEL_ASSIGNMENT` dictionary in `src/utils/llm_client.py` to customize model assignments.

### Adjusting Game Rules

Modify game flow and rules in `src/game/werewolf_game.py`.

### Custom Roles

Add new role types in `src/models/roles.py`.

## 🔧 Troubleshooting

### Issue: AWS Authentication Failed

**Solution**:
- Check if AWS credentials are correctly configured
- Ensure AWS account has Bedrock service permissions
- Verify region is set to `us-west-2`

### Issue: Model Call Failed

**Solution**:
- Confirm model is available in your region
- Check if you have sufficient quota
- Review Bedrock service status in AWS console

### Issue: Game Stuck

**Solution**:
- Check network connection
- Review console error messages
- Use Ctrl+C to interrupt the program

## 📝 Recent Updates

- ✅ Fixed player name information leak (now using generic names)
- ✅ Implemented proper last words rules
- ✅ Added werewolf team coordination and strategy discussion
- ✅ Enhanced voting logic consistency checks
- ✅ Improved tactical flexibility (werewolf rush when advantageous)
- ✅ Organized documentation structure

See [CHANGELOG.md](CHANGELOG.md) for detailed update history.

## 📄 License

This project is for educational and entertainment purposes only.

## 🤝 Contributing

Issues and improvement suggestions are welcome!

## 📧 Contact

For questions, please create an Issue.
