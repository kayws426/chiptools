import logging
import traceback

# TODO: Replace with dynamic plugin discovery and loading
from chiptools.wrappers.synthesisers.quartus import Quartus
from chiptools.wrappers.synthesisers.ise import Ise
from chiptools.wrappers.simulators.modelsim import Modelsim

log = logging.getLogger(__name__)

# A registry of synthesis tool names and functions to return an appropriate
# synthesis tool wrapper.
synthesis_tool_class_registry = {
    'ise': lambda project, user_paths: Ise(
        project,
        user_paths,
        mode='manual'
    ),
    'quartus': lambda project, user_paths: Quartus(
        project,
        user_paths
    ),
    'xflow': lambda project, user_paths: Ise(
        project,
        user_paths,
        mode='xflow'
    ),
}

simulation_tool_class_registry = {
    'modelsim': lambda project, user_paths: Modelsim(project, user_paths),
}


def get_all_tools(project, user_paths, tool_type='synthesis'):
    """Return all tools of the given type, this could be used for reporting
    available tools."""
    if tool_type == 'synthesis':
        registry = synthesis_tool_class_registry
    elif tool_type == 'simulation':
        registry = simulation_tool_class_registry
    else:
        log.error(
            'Invalid tool type specified: {0}'.format(tool_type) +
            ' Use one of [simulation, synthesis]'
        )
        return None

    tools = {}
    for toolname, inst_fn in registry.items():
        try:
            inst = inst_fn(project, user_paths)
            if not inst.installed:
                log.warning(
                    toolname.capitalize() +
                    ' could not be found.' +
                    ' Update .chiptoolsconfig or your PATH variable'
                )
            tools[toolname] = inst
        except:
            # Error instancing this tool.
            log.error(
                'Encountered an error when loading tool wrapper: ' +
                toolname
            )
            log.error(traceback.format_exc())
    return tools


class ToolWrapper:
    """
    ToolWrapper holds instances of all available toolchains and provides a
    method of retrieving the tool currently specified in the loaded project
    file.
    """
    def __init__(self, project, user_paths={}):
        self.project = project
        self.synthesisers = get_all_tools(
            self.project,
            user_paths,
            tool_type='synthesis'
        )
        self.simulators = get_all_tools(
            self.project,
            user_paths,
            tool_type='simulation'
        )

    def get_tool(self, tool_type='synthesis', tool_name=None):
        if tool_type == 'synthesis':
            if tool_name is None:
                tool_name = self.project.get_synthesis_tool_name()
            tool = self.synthesisers.get(tool_name, None)
        elif tool_type == 'simulation':
            if tool_name is None:
                tool_name = self.project.get_simulation_tool_name()
            tool = self.simulators.get(tool_name, None)
        else:
            log.error(
                'Invalid tool type specified: {0}'.format(tool_type) +
                ' Use one of [simulation, synthesis]'
            )
            tool = None
        if tool is None:
            log.error(
                'No wrapper exists for the tool: ' + str(tool_name)
            )
        return tool