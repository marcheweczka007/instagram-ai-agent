from pathlib import Path

from instagram_agent.agents.base import BaseAgent


class ScorerAgent(BaseAgent):
    def __init__(self):
        super().__init__()

        prompt_path = (
            Path(__file__).parent.parent
            / "prompts"
            / "scorer.md"
        )

        self.system_prompt = prompt_path.read_text()


    def score(self, profile: str):
        pass