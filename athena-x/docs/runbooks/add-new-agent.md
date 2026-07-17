# Add a New AI Agent

```bash
# Scaffold a new raw-intelligence agent
python tools/agent-scaffolder/scaffold.py raw-intelligence my_agent

# Or a decision-intelligence agent
python tools/agent-scaffolder/scaffold.py decision-intelligence my_agent
```

Then:
1. Edit `manifest.py` to declare subscriptions + publications
2. Edit `agent.py` to implement the agent class
3. Edit `config.py` to add instance config fields
4. Add tests under `tests/`
5. Register the agent in `apps/python-backend/src/athena_x_backend/agent_registry.py` (STEP 4)

The Supervisor will automatically detect and supervise the new agent.
