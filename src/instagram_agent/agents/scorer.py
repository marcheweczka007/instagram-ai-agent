from instagram_agent.agents.base import BaseAgent


class ScorerAgent(BaseAgent):

    def score(self, profile: str):
        print(profile)