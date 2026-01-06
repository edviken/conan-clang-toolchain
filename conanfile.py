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

    def validate(self):
        if self.settings.arch != "x86_64" or self.settings.os != "Linux":
            raise ConanInvalidConfiguration(f"This toolchain is not compatible with {self.settings.os}-{self.settings.arch}. "
                                            "It can only run on Linux-x86_64.")

    def source(self):
        download(self, "https://raw.githubusercontent.com/llvm/llvm-project/main/llvm/LICENSE.TXT", "LICENSE", verify=False)

    def build(self):
        get(self, "https://github.com/llvm/llvm-project/releases/download/llvmorg-21.1.8/LLVM-21.1.8-Linux-X64.tar.xz",
             sha256="b3b7f2801d15d50736acea3c73982994d025b01c2f035b91ae3b49d1b575732b", strip_root=True)
        
    def package(self):
        dirs_to_copy = [self.toolchain, "bin", "include", "lib", "libexec"]
        for dir_name in dirs_to_copy:
            copy(self, pattern=f"{dir_name}/*", src=self.build_folder, dst=self.package_folder, keep_path=True)
        copy(self, "LICENSE", src=self.build_folder, dst=os.path.join(self.package_folder, "licenses"), keep_path=False)

    def package_id(self):
        self.info.settings_target = self.settings_target
        # We only want the ``arch`` and ``os`` setting
        self.info.settings_target.rm_safe("compiler")
        self.info.settings_target.rm_safe("build_type")

    def package_info(self):
        self.cpp_info.bindirs.append(os.path.join(self.package_folder, self.toolchain, "bin"))

        self.conf_info.define("tools.build:compiler_executables", {
            "c":   f"clang",
            "cpp": f"clang++",
            "asm": f"llvm-as"
        })
