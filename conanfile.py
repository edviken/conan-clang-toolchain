import os
from conan import ConanFile
from conan.tools.files import get, copy, download
from conan.errors import ConanInvalidConfiguration
from conan.tools.scm import Version

class LlvmToolchainPackage(ConanFile):
    name = "llvm-toolchain"
    version = "21.1.8"

    license = ""
    homepage = "https://github.com/llvm/llvm-project/releases"
    description = "LLVM clang toolchain for C/C++"
    settings = "os", "arch"
    package_type = "application"

    # The toolchain name
    toolchain = "LLVM-21.1.8-Linux-X64"

    def _get_toolchain(self):
        if self.settings.arch == "x86_64" or self.settings.os == "Linux":
            return "Linux-X64", "b3b7f2801d15d50736acea3c73982994d025b01c2f035b91ae3b49d1b575732b"
        if self.settings.arch == "armv8" and self.settings.os == "Macos":
            return "Macos-ARM64", "b95bdd32a33a81ee4d40363aaeb26728a26783fcef26a4d80f65457433ea4669"

    def validate(self):
        if self.settings.arch == "x86_64" or self.settings.os == "Linux":
            return
        if self.settings.arch == "armv8" and self.settings.os == "Macos":
            return
        raise ConanInvalidConfiguration(f"This toolchain is not compatible with {self.settings.os}-{self.settings.arch}. "
                                        "It can only run on Macos-armv8 or Linux-x84_64")

    def source(self):
        download(self, "https://raw.githubusercontent.com/llvm/llvm-project/main/llvm/LICENSE.TXT", "LICENSE", verify=False)

    def build(self):
        toolchain_name, hash = self._get_toolchain()
        get(self, f"https://github.com/llvm/llvm-project/releases/download/llvmorg-21.1.8/LLVM-21.1.8-{toolchain_name}.tar.xz",
             sha256=f"{hash}", strip_root=True)
        
    def package(self):
        toolchain_name, _ = self._get_toolchain()
        toolchain_folder = f"LLVM-21.1.8-{toolchain_name}"
        dirs_to_copy = [toolchain_folder, "bin", "include", "lib", "libexec"]
        for dir_name in dirs_to_copy:
            copy(self, pattern=f"{dir_name}/*", src=self.build_folder, dst=self.package_folder, keep_path=True)
        copy(self, "LICENSE", src=self.build_folder, dst=os.path.join(self.package_folder, "licenses"), keep_path=False)

    def package_id(self):
        self.info.settings_target = self.settings_target
        # We only want the ``arch`` and ``os`` setting
        self.info.settings_target.rm_safe("compiler")
        self.info.settings_target.rm_safe("build_type")

    def package_info(self):
        toolchain_name, _ = self._get_toolchain()
        toolchain_folder = f"LLVM-21.1.8-{toolchain_name}"
        self.cpp_info.bindirs.append(os.path.join(self.package_folder, toolchain_folder, "bin"))

        self.conf_info.define("tools.build:compiler_executables", {
            "c":   f"clang",
            "cpp": f"clang++",
            "asm": f"llvm-as"
        })
        if self.settings.os == "Macos":
            self.buildenv_info.define_path("DYLD_LIBRARY_PATH", "")
            self.buildenv_info.define_path("LD_LIBRARY_PATH", "")
            # Note: needed to not fallback to macos native linker, which will fail to find some symbols
            self.conf_info.append("tools.build:exelinkflags", "-fuse-ld=lld")

        
