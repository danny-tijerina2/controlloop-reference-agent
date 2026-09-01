"""The tool list ControlLoop deliberately cannot resolve.

Choosing tools from the environment is ordinary code. That is exactly
why it matters: the publish step is the one that can reach the outside
world, and a scanner that quietly reported it as having no tools would
be reporting a confident pass over the riskiest node in the graph.
"""

import os


def build_publish_tools() -> list[object]:
    from langchain_community.tools import FileManagementToolkit

    if os.environ.get("PUBLISH_TARGET") == "production":
        return FileManagementToolkit(root_dir="/srv/site").get_tools()
    return []
