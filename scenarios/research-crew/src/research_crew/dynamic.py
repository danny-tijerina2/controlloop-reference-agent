"""The tool list ControlLoop deliberately cannot resolve.

Nothing here is exotic -- picking tools from configuration is ordinary,
and that is exactly why it matters. A scanner that quietly reported this
agent as having no tools would be reporting a confident pass over the
one agent in the crew that can publish.
"""

import os


def tools_for_environment() -> list[object]:
    """Chosen at runtime. Unknowable statically, by construction."""

    from crewai_tools import DirectoryReadTool, FileWriterTool

    if os.environ.get("PUBLISH_TARGET") == "production":
        return [FileWriterTool(), DirectoryReadTool()]
    return [DirectoryReadTool()]
