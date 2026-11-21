#include <cstdlib>
#include <iostream>
#include <variant>

#ifndef _LIBCPP_VERSION
#error "This test must use libc++ headers"
#endif

void throw_from_library();

static void throw_locally()
{
    throw std::bad_variant_access{};
}

static bool catches_bad_variant_access(void (*raise)(), const char* test)
{
    try {
        raise();
    } catch (const std::bad_variant_access& error) {
        std::cout << test << ": caught " << error.what() << '\n';
        return true;
    } catch (...) {
        std::cerr << test << ": caught the wrong exception type\n";
        return false;
    }
    std::cerr << test << ": no exception thrown\n";
    return false;
}

int main()
{
    std::cout << "Build with: " << __VERSION__ << "\n";
    std::cout << "C++ version: " << __cplusplus << std::endl;

    const bool local = catches_bad_variant_access(throw_locally, "local throw");
    const bool shared = catches_bad_variant_access(throw_from_library, "shared library throw");
    return local && shared ? EXIT_SUCCESS : EXIT_FAILURE;
}