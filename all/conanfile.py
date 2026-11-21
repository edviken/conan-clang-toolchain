import os
from pathlib import Path
import shlex

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import copy, download, get, load, save


class LlvmToolchainPackage(ConanFile):
    name = "llvm-toolchain"

    license = ""
    homepage = "https://github.com/llvm/llvm-project/releases"
    description = "LLVM clang toolchain for C/C++"
    settings = "os", "arch"
    package_type = "application"
    exports_sources = "llvm-runtime.cmake.in"

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
        if self.settings.os == "Macos" and str(self.version) == "23.1.4":
            self._relink_macos_unwind()
        self._package_runtime_configuration()

    def _relink_macos_unwind(self):
        lib = Path(self.package_folder) / "lib"
        # The 23.1.4 dylib has conflicting compact-unwind entries for
        # _Unwind_RaiseException. Relink the shipped objects with Apple ld.
        output = lib / "libunwind.1.0.dylib"
        rebuilt = lib / "libunwind.relinked.dylib"
        command = [
            "xcrun", "--sdk", "macosx", "clang", "-fuse-ld=ld",
            "-arch", "arm64", "-mmacosx-version-min=14.0", "-dynamiclib",
            "-Xlinker", "-force_load", "-Xlinker", str(lib / "libunwind.a"),
            "-Wl,-install_name,@rpath/libunwind.1.dylib",
            "-Wl,-compatibility_version,1.0.0", "-Wl,-current_version,1.0.0",
            "-o", str(rebuilt),
        ]
        self.run(" ".join(shlex.quote(arg) for arg in command))
        rebuilt.replace(output)

    def _package_runtime_configuration(self):
        root = Path(self.package_folder)
        is_macos = self.settings.os == "Macos"
        names = [f"lib{name}.1.dylib" if is_macos else f"lib{name}.so.1"
                 for name in ("c++", "c++abi", "unwind")]
        candidates = [root / "lib", *sorted((root / "lib").glob("*-linux-*"))]
        lib = next((path for path in candidates if all((path / name).is_file() for name in names)), None)
        if lib is None:
            raise ConanInvalidConfiguration(f"No directory with all LLVM shared runtimes: {', '.join(names)}")
        libdir = lib.relative_to(root).as_posix()

        headers = root / "include" / "c++" / "v1"
        config_headers = [headers, *sorted((root / "include").glob("*-linux-*/c++/v1"))]
        config_headers = next((path for path in config_headers if (path / "__config_site").is_file()), None)
        if not (headers / "variant").is_file() or config_headers is None:
            raise ConanInvalidConfiguration("The archive is missing the packaged libc++ headers")

        flags = ["-stdlib=libc++", "-nostdinc++", "-nostdlib++"]
        if config_headers != headers:
            flags.append(f'-isystem"<CFGDIR>/../{config_headers.relative_to(root).as_posix()}"')
        flags.append('-isystem"<CFGDIR>/../include/c++/v1"')
        # Clang appends $-prefixed config options after the link inputs.
        if not is_macos:
            flags.append("$-Wl,--push-state,--no-as-needed")
        flags.extend(f'$"<CFGDIR>/../{libdir}/{name}"' for name in names)
        if not is_macos:
            flags.append("$-Wl,--pop-state")
        save(self, str(root / "bin" / "clang++.cfg"), "\n".join(flags) + "\n")

        template = load(self, os.path.join(self.source_folder, "llvm-runtime.cmake.in"))
        save(self, str(root / "llvm-runtime.cmake"),
             template.replace("@LLVM_RUNTIME_LIBDIR@", libdir)
             .replace("@LLVM_RUNTIME_NAMES@", ";".join(names))
             .replace("@LLVM_RUNTIME_ORIGIN@", "@loader_path" if is_macos else "$ORIGIN"))

    def package_id(self):
        self.info.settings_target = self.settings_target
        # We only want the ``arch`` and ``os`` setting
        self.info.settings_target.rm_safe("compiler")
        self.info.settings_target.rm_safe("build_type")

    def package_info(self):
        bindir = Path(self.package_folder) / "bin"
        # Don't inject libc++ into the environment of CMake or other build tools.
        self.cpp_info.libdirs = []
        self.conf_info.define("tools.build:compiler_executables", {
            "c": str(bindir / "clang"),
            "cpp": str(bindir / "clang++"),
            "asm": str(bindir / "llvm-as"),
        })
        self.conf_info.append("tools.cmake.cmaketoolchain:user_toolchain",
                              os.path.join(self.package_folder, "llvm-runtime.cmake"))
        self.conf_info.append("tools.build:cxxflags", "-stdlib=libc++")
        if self.settings.os == "Macos":
            self.conf_info.append("tools.build:exelinkflags", "-fuse-ld=lld")
            self.conf_info.append("tools.build:sharedlinkflags", "-fuse-ld=lld")
