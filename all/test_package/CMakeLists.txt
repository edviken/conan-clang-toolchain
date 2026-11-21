cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES CXX)

include(CheckCXXSourceCompiles)
if(NOT CMAKE_CXX_STANDARD)
    set(CMAKE_CXX_STANDARD 17)
endif()
check_cxx_source_compiles([=[
    #include <variant>
    int main() { throw std::bad_variant_access{}; }
]=] LLVM_TOOLCHAIN_CAN_LINK_BAD_VARIANT_ACCESS)
if(NOT LLVM_TOOLCHAIN_CAN_LINK_BAD_VARIANT_ACCESS)
    message(FATAL_ERROR "CMake compiler checks could not link std::bad_variant_access")
endif()

add_library(exception_source SHARED exception_source.cpp)
add_executable(${PROJECT_NAME} test_package.cpp)
target_link_libraries(${PROJECT_NAME} PRIVATE exception_source)

find_package(GTest CONFIG REQUIRED)
add_executable(unit_test unit_test.cpp)
target_link_libraries(unit_test PRIVATE exception_source GTest::gtest_main)

if(APPLE)
    set_property(TARGET test_package PROPERTY INSTALL_RPATH "@loader_path/../lib")
endif()

install(TARGETS ${PROJECT_NAME} exception_source RUNTIME DESTINATION bin LIBRARY DESTINATION lib)
llvm_toolchain_install_runtimes()
