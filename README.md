# LLVM toolchain Conan recipe

LLVM project conan toolchain for being able to build with clang. 

Supported versions: **23.1.4** and **21.1.8**.
Supported platforms: **Linux x86_64** and **macOS ARM64** (`Macos`/`armv8` in Conan).

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

## Adding a version

1. Add the version to `config.yml` with `folder: all`.
2. Add its platform-specific archive URLs and SHA-256 checksums under `sources`
   in `all/conandata.yml`.
3. Run `conan create all --version=<version> --build-require`.

Conan guide for creating tool requires packages:
 https://docs.conan.io/2/tutorial/creating_packages/other_types_of_packages/tool_requires_packages.html
