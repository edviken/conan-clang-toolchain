# Readme

To install the package locally, run
```
conan create . --build-require
```
inside this directory

## Test package
To test the package, run
```
conan test test_package llvm-toolchain/21.1.8
```
*Note: test of package is implicitly run when doing the create command*

Conan guide for creating tool requires packages:
 https://docs.conan.io/2/tutorial/creating_packages/other_types_of_packages/tool_requires_packages.html
