# LLVM toolchain Conan recipe

LLVM project conan toolchain for being able to build with clang. 

Supported versions: **23.1.4** and **21.1.8**.
Supported platforms: **Linux x86_64** and **macOS ARM64** (`Macos`/`armv8` in Conan).

## Using the toolchain

Declare `llvm-toolchain/<version>` as a **direct** `tool_requires` of every
recipe that compiles or links with it (or add it to those recipes via a
profile). Conan does not propagate the package's `conf_info` through
transitive tool requirements. Use a Conan compiler profile compatible with the
packaged Clang and set `compiler.libcxx=libc++`; rebuild C++ dependencies that
share the C++ ABI rather than mixing libc++ and libstdc++ objects.

Use `clang++` as the linker driver for C++ targets. On macOS, the configured
driver selects the active Apple SDK's C++ headers and links the system libc++,
libc++abi, and unwinder. It does not use or deploy the archive's LLVM C++
runtimes. Conan's build environment sets `SDKROOT` from the existing
environment or `xcrun --sdk macosx --show-sdk-path`; a profile may override it.
For direct compiler invocations outside that environment, set `SDKROOT` or pass
`-isysroot <sdk-path>`. CMake's `CMAKE_OSX_SYSROOT` can select an SDK too.

Clang's language features and the SDK's standard-library features are separate.
Set the appropriate C++ standard, choose a deployment target supported by the
SDK and runtime features you use, and test on the oldest supported macOS.

On Linux, the driver selects the shipped LLVM headers and links the packaged
`libc++`, `libc++abi`, and `libunwind` after the object files. Conan's
CMakeToolchain includes the package's user toolchain, which sets the build
rpath to the packaged runtime directory.

### Conan compiler settings

The host profile should identify the actual upstream compiler, for example:

```ini
include(default)

[settings]
compiler=clang
compiler.version=23
compiler.libcxx=libc++
compiler.cppstd=gnu23

[tool_requires]
*: llvm-toolchain/23.1.4
```

Apply the tool requirement to the application and every C++ dependency that
needs it. Ensure build-tool requirements are compatible with the profile;
use more specific patterns when necessary. Rebuild dependencies with this
profile: changing a tool requirement does not by itself guarantee that Conan
will reject a previously cached binary.

If `compiler.version=23` is rejected, update Conan and check
`<CONAN_HOME>/settings.yml`. Conan's installed settings may not be replaced on
upgrade if customized. If needed, add `"23"` to `compiler.clang.version` in
that file (not `apple-clang.version`); remove the generated-file warning
comment when customizing it so Conan does not overwrite your change. Share
the updated settings with the team using `conan config install`. Use a
separate Conan home for experimentation, and do not claim a different
compiler version merely to reuse incompatible cached binaries.

### Deploying CMake targets

On macOS, deploy your application's own libraries as usual; Apple supplies the
C++ runtime. `llvm_toolchain_install_runtimes()` is a no-op on macOS.

On Linux, install executables to `bin` and shared libraries to `lib`, and bundle
the matching LLVM runtime files in the same install tree:

```cmake
install(TARGETS my_app my_library RUNTIME DESTINATION bin LIBRARY DESTINATION lib)
llvm_toolchain_install_runtimes()
```

By default, installed binaries use `$ORIGIN` and `$ORIGIN/../lib`. No Conan
cache rpath is needed after installation. If you change the layout, set your
own `CMAKE_INSTALL_RPATH` before defining the targets.

Other Conan generators (e.g. MesonToolchain or AutotoolsToolchain) also select
the packaged compiler and flags. On Linux, configure their build rpath to the
package's runtime directory and their install rpath to the same relative
layout. When staging without CMake, copy the real library files under their
versioned install names (`libc++.so.1`, `libc++abi.so.1`, and `libunwind.so.1`).
Do not deploy binaries with a Conan cache rpath.

## Creating the package

To install the package locally, run
```
conan create all --version=23.1.4 --build-require
```
inside this directory. Use `--version=21.1.8` to create the older version.
Conan requires the version explicitly; it does not select one from `config.yml`.

## Test package
To test the package, run
```
conan test all/test_package llvm-toolchain/23.1.4
```
*Note: test of package is implicitly run when doing the create command*

The test links `std::bad_variant_access` during CMake configuration, then
throws and catches it both locally and across a shared-library boundary. It
runs the same checks from the build tree and from a relocated installation.
It also builds and runs a Google Test executable with local and cross-library
exception tests.

To test a **shared** Google Test built with the same LLVM toolchain, add a
direct tool requirement for Google Test in a host profile such as:

```ini
include(default)

[tool_requires]
gtest/*: llvm-toolchain/23.1.4
```

Then run (replace `llvm-gtest.profile` with the profile path):

```sh
conan test all/test_package llvm-toolchain/23.1.4 \
  -pr:h llvm-gtest.profile -o 'gtest/*:shared=True' --build='gtest/*'
```

The forced rebuild is important: an existing Conan binary with the same
package ID may have been built with another compiler. On macOS the test also
checks the compiler's header trace and the runtime links of the executable,
the shared exception library and, when shared, Google Test.

## Adding a version

1. Add the version to `config.yml` with `folder: all`.
2. Add its platform-specific archive URLs and SHA-256 checksums under `sources`
   in `all/conandata.yml`.
3. Run `conan create all --version=<version> --build-require`.

Conan guide for creating tool requires packages:
 https://docs.conan.io/2/tutorial/creating_packages/other_types_of_packages/tool_requires_packages.html
