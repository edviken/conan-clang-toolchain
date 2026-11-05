import os
from conan import ConanFile
from conan.tools.files import get, copy, download
from conan.errors import ConanInvalidConfiguration

class LlvmToolchainPackage(ConanFile):
    name = "llvm-toolchain"

    license = ""
    homepage = "https://github.com/llvm/llvm-project/releases"
    description = "LLVM clang toolchain for C/C++"
    settings = "os", "arch"
    package_type = "application"

    def validate(self):
        platforms = self.conan_data["sources"][str(self.version)]
        if str(self.settings.arch) not in platforms.get(str(self.settings.os), {}):
            raise ConanInvalidConfiguration(
                f"This toolchain is not compatible with {self.settings.os}-{self.settings.arch}. "
                "It can only run on Macos-armv8 or Linux-x86_64"
            )

    def source(self):
        download(self, f"https://raw.githubusercontent.com/llvm/llvm-project/llvmorg-{self.version}/llvm/LICENSE.TXT",
                 "LICENSE")

    def build(self):
        get(self, **self.conan_data["sources"][str(self.version)][str(self.settings.os)][str(self.settings.arch)],
            strip_root=True)

    def package(self):
        dirs_to_copy = ["bin", "include", "lib", "libexec"]
        for dir_name in dirs_to_copy:
            copy(self, pattern=f"{dir_name}/*", src=self.build_folder, dst=self.package_folder, keep_path=True)
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"), keep_path=False)

    def package_id(self):
        self.info.settings_target = self.settings_target
        # We only want the ``arch`` and ``os`` setting
        self.info.settings_target.rm_safe("compiler")
        self.info.settings_target.rm_safe("build_type")

    def package_info(self):
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
