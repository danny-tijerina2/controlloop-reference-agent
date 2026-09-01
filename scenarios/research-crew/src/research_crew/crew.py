"""The crew wiring.

Deliberately mixed: two agents wire their tools in a shape ControlLoop
can read, and one does not. That third case is the point of this
scenario -- it is what a real project looks like, and it is what decides
whether a scanner is honest about what it could not see.
"""

from crewai import Agent, Crew, Task
from crewai_tools import FileWriterTool, ScrapeWebsiteTool, SerperDevTool

from research_crew.dynamic import tools_for_environment


class ResearchCrew:
    """A three-agent crew: research, write, publish."""

    def researcher(self) -> Agent:
        # Resolvable: a literal list of constructor calls.
        return Agent(
            config=self.agents_config["researcher"],
            tools=[SerperDevTool(), ScrapeWebsiteTool()],
        )

    def writer(self) -> Agent:
        # Resolvable.
        return Agent(
            config=self.agents_config["writer"],
            tools=[FileWriterTool()],
        )

    def publisher(self) -> Agent:
        # NOT resolvable, and deliberately so. The tool list is computed
        # at runtime from the environment. No static analyzer can know
        # what this agent can do -- and this agent is the one holding
        # publishing credentials.
        return Agent(
            config=self.agents_config["publisher"],
            tools=tools_for_environment(),
        )

    def crew(self) -> Crew:
        return Crew(
            agents=[self.researcher(), self.writer(), self.publisher()],
            tasks=[Task(description="Research, write, and publish a brief.")],
        )
