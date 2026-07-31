from instagram_agent.agents.scorer import ScorerAgent
from instagram_agent.services.profile_loader import load_example_profile


def main():
    profile = load_example_profile()

    scorer = ScorerAgent()

    result = scorer.score(profile)

    print(result)


if __name__ == "__main__":
    main()

    