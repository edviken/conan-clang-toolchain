import os
import shlex
from tempfile import TemporaryDirectory

from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.cmake import CMake, cmake_layout


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "CMakeToolchain", "VirtualBuildEnv"

    def build_requirements(self):
        self.tool_requires(self.tested_reference_str)

    def layout(self):
        cmake_layout(self)

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def test(self):
        if not can_run(self):
            return

        def run_without_loader_overrides(executable):
            self.run("env -u DYLD_LIBRARY_PATH -u DYLD_FALLBACK_LIBRARY_PATH "
                     f"-u LD_LIBRARY_PATH {shlex.quote(executable)}", env=None)

        executable = os.path.join(self.build_folder, self.cpp.build.bindirs[0], "test_package")
        run_without_loader_overrides(executable)

        with TemporaryDirectory() as staging:
            original = os.path.join(staging, "install")
            relocated = os.path.join(staging, "relocated")
            self.run(f"cmake --install {shlex.quote(self.build_folder)} "
                     f"--config {self.settings.build_type} --prefix {shlex.quote(original)}")
            os.rename(original, relocated)
            run_without_loader_overrides(os.path.join(relocated, "bin", "test_package"))
