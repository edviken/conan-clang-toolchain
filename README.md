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

The configured `clang++` reads its packaged driver configuration, which
selects the shipped headers and links the packaged `libc++`, `libc++abi`, and
`libunwind` after the object files. Use `clang++` as the linker driver for C++
targets. Conan's CMakeToolchain automatically includes the package's user
toolchain, which sets the build rpath to the packaged runtime directory.

### Deploying CMake targets

Install executables to `bin` and shared libraries to `lib`, and bundle the
matching runtime files in the same install tree:

```cmake
install(TARGETS my_app my_library RUNTIME DESTINATION bin LIBRARY DESTINATION lib)
llvm_toolchain_install_runtimes()
```

By default, the installed binaries resolve the runtime dylibs' `@rpath`
install names via `@loader_path` and `@loader_path/../lib` on macOS, or use
the corresponding `$ORIGIN` paths on Linux. No Conan cache rpath is needed
after installation. If you change the layout, set your own `CMAKE_INSTALL_RPATH`
before defining the targets.

Other Conan generators (e.g. MesonToolchain or AutotoolsToolchain) also select
the packaged compiler and flags. Configure their build rpath to the package's
runtime directory and their install rpath to the same relative layout described
above. When staging without CMake, copy the real library files under their
versioned install names (`libc++.1.dylib`, `libc++abi.1.dylib`, and
`libunwind.1.dylib` on macOS; `libc++.so.1`, `libc++abi.so.1`, and
`libunwind.so.1` on Linux). Do not deploy binaries with a cache rpath or set
`DYLD_LIBRARY_PATH`/`LD_LIBRARY_PATH` globally.

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

On macOS, packaging 23.1.4 requires the Xcode command-line tools. The shipped
`libunwind` has conflicting compact-unwind entries for `_Unwind_RaiseException`.
It reported end of stack before reaching the catch handler. Relinking the
archive's own `libunwind.a` with Apple `ld` fixes the table while keeping the
packaged LLVM runtime; switching the application's linker alone does not.

## Adding a version

1. Add the version to `config.yml` with `folder: all`.
2. Add its platform-specific archive URLs and SHA-256 checksums under `sources`
   in `all/conandata.yml`.
3. Run `conan create all --version=<version> --build-require`.

Conan guide for creating tool requires packages:
 https://docs.conan.io/2/tutorial/creating_packages/other_types_of_packages/tool_requires_packages.html
