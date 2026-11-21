import os
import shlex
from io import StringIO
from tempfile import TemporaryDirectory

from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.cmake import CMake, cmake_layout


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "CMakeDeps", "CMakeToolchain", "VirtualBuildEnv"

    def requirements(self):
        self.requires("gtest/1.17.0")

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

        if self.settings.os == "Macos":
            compiler = os.path.join(self.dependencies.build[self.tested_reference_str].package_folder,
                                    "bin", "clang++")
            headers = StringIO()
            source = os.path.join(self.source_folder, "exception_source.cpp")
            self.run(f"{shlex.quote(compiler)} -std=c++17 -H -fsyntax-only "
                     f"{shlex.quote(source)}", stderr=headers)
            trace = headers.getvalue()
            assert "/usr/include/c++/v1/variant" in trace, trace
            assert "/bin/../include/c++/v1/" not in trace, trace

            def assert_apple_runtime(path):
                output = StringIO()
                self.run(f"otool -L {shlex.quote(path)}", stdout=output, env=None)
                dependencies = output.getvalue()
                assert "/usr/lib/libc++.1.dylib" in dependencies, dependencies
                assert "@rpath/libc++.1.dylib" not in dependencies, dependencies
                assert "@rpath/libc++abi.1.dylib" not in dependencies, dependencies
                assert "@rpath/libunwind.1.dylib" not in dependencies, dependencies

            assert_apple_runtime(os.path.join(self.build_folder, "test_package"))
            assert_apple_runtime(os.path.join(self.build_folder, "unit_test"))
            assert_apple_runtime(os.path.join(self.build_folder, "libexception_source.dylib"))
            gtest = self.dependencies["gtest"]
            if gtest.options.shared:
                assert_apple_runtime(os.path.join(gtest.package_folder, "lib", "libgtest.dylib"))
                assert_apple_runtime(os.path.join(gtest.package_folder, "lib", "libgtest_main.dylib"))

        def run_without_loader_overrides(executable):
            self.run("env -u DYLD_LIBRARY_PATH -u DYLD_FALLBACK_LIBRARY_PATH "
                     f"-u LD_LIBRARY_PATH {shlex.quote(executable)}", env=None)

        unit_test = os.path.join(self.build_folder, self.cpp.build.bindirs[0], "unit_test")
        run_without_loader_overrides(unit_test)
        executable = os.path.join(self.build_folder, self.cpp.build.bindirs[0], "test_package")
        run_without_loader_overrides(executable)

        with TemporaryDirectory() as staging:
            original = os.path.join(staging, "install")
            relocated = os.path.join(staging, "relocated")
            self.run(f"cmake --install {shlex.quote(self.build_folder)} "
                     f"--config {self.settings.build_type} --prefix {shlex.quote(original)}")
            os.rename(original, relocated)
            run_without_loader_overrides(os.path.join(relocated, "bin", "test_package"))
