import asyncio
import sys

from instagram_agent.domain.models import AnalysisResult
from instagram_agent.pipelines import analyse_profile


def print_analysis_result(result: AnalysisResult) -> None:
    print(f"Profile name: {result.profile.name}")
    print(f"Followers: {result.profile.followers}")
    print(f"Score: {result.analysis.score}")
    print(f"Follow recommendation: {result.analysis.follow}")
    print(f"Reason: {result.analysis.reason}")
    print(f"Suggested comment: {result.analysis.comment}")


async def main() -> None:
    url = (
        sys.argv[1]
        if len(sys.argv) > 1
        else ("https://www.instagram.com/upcycle.lab.jollyzu/")
    )
    result = await analyse_profile(url)
    print_analysis_result(result)


if __name__ == "__main__":
    asyncio.run(main())
