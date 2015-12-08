import logging
import os
import shlex

from chiptools.wrappers.simulator import Simulator
from chiptools.common.filetypes import FileType
from chiptools.common import utils

log = logging.getLogger(__name__)


class Isim(Simulator):

    name = 'isim'
    executables = ['fuse', 'vlogcomp', 'vhpcomp']

    # Name of the output file generated by fuse
    sim_exe_name = 'fuse_sim'
    sim_project_name = 'isim_project.prj'
    sim_ini_name = 'xilinxsim.ini'
    sim_tcl_name = 'isim.tcl'

    def __init__(self, project, user_paths):
        super(Isim, self).__init__(project, self.executables, user_paths)
        self.fuse = os.path.join(self.path, 'fuse')
        self.vhpcomp = os.path.join(self.path, 'vhpcomp')
        self.vlogcomp = os.path.join(self.path, 'vlogcomp')

        # ISE requires the XILINX path to be set or the generated simulation
        # executables will crash when launched. The path should be the
        # ISE_DS/ISE directory where the settings32/64 bat files reside. This
        # should be two levels up from the located path, unless the user has
        # modified their ISE installation structure.
        os.environ['XILINX'] = os.path.join(self.path, '../../')

    def write_includes(self):
        """Write the includes dictionary to the xilinxsim.ini file in the
        simulation directory, which is required by vlogcomp, vhpcomp and fuse
        to locate existing compiled libraries."""
        cwd = self.project.get_simulation_directory()
        with open(os.path.join(cwd, self.sim_ini_name), 'w') as f:
            f.write('--Do not modify this file, any changes will be lost.\n')
            f.write(
                '--Generated by ChipTools on {0}\n'.format(
                    utils.getDateString()
                )
            )
            for libname, path in self.libraries.items():
                f.write('{0}={1}\n'.format(libname, path))

    def simulate(
        self,
        library,
        entity,
        gui=False,
        generics={},
        includes={},
        args=[],
        duration=None
    ):
        cwd = self.project.get_simulation_directory()
        # Execute FUSE on the design files:
        fuse_args = [
            library + '.' + entity,
            '-o', self.sim_exe_name,
        ]
        # Set simulator generics
        for name, binding in generics.items():
            fuse_args += ['--generic_top', name + '=' + str(binding)]
        Isim._call(self.fuse, fuse_args, cwd=cwd, quiet=False)
        # Fuse generates a simulation executable, this can be called now with
        # the specified simulator arguments:
        sim_args = []
        if gui:
            sim_args += ['-gui']
        # Create a TCL file:
        with open(os.path.join(cwd, self.sim_tcl_name), 'w') as f:
            # Set run duration
            if duration is not None:
                if duration <= 0:
                    duration = 'all'
                else:
                    duration = utils.seconds_to_timestring(self.duration)
                f.write('run {0}\n'.format(duration))
                f.write('exit\n')
        sim_args += ['-tclbatch', self.sim_tcl_name]
        # Run the simulation
        ret, stdout, stderr = Isim._call(
            os.path.join(cwd, self.sim_exe_name),
            sim_args,
            cwd=self.project.get_simulation_directory(),
            quiet=False
        )

        return ret, stdout, stderr

    def compile(self, file_object, cwd=None):
        cwd = self.project.get_simulation_directory()
        if file_object.library not in self.libraries:
            self.libraries[file_object.library] = file_object.library
            self.write_includes()
        args = self.project.get_tool_arguments(self.name, 'compile')
        if len(args) == 0:
            args = file_object.get_tool_arguments(self.name, 'compile')
        args = shlex.split(['', args][args is not None])
        args += [
            '-incremental',
            '-work',
            file_object.library + '=' + file_object.library,
            file_object.path
        ]
        if file_object.fileType == FileType.VHDL:
            Isim._call(self.vhpcomp, args, cwd=cwd)
        elif file_object.fileType == FileType.Verilog:
            Isim._call(self.vlogcomp, args, cwd=cwd)
        elif file_object.fileType == FileType.SystemVerilog:
            Isim._call(self.vlogcomp, args, cwd=cwd)
        else:
            log.warning(
                'ISIM wrapper skipping file with unknown type: ' +
                file_object.path
            )

    def library_exists(self, libname, workdir):
        if os.path.exists(os.path.join(workdir, libname)):
            return True
        return False

    def set_working_library(self, library, cwd=None):
        pass

    def set_library_path(self, library, path, cwd=None):
        pass

    def add_library(self, library):
        pass