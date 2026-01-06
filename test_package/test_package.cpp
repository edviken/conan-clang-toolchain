#include <cstdlib>
#include <iostream>

int main()
{
    std::cout << "hello world!\n";
    std::cout << "Built with: " << __VERSION__ << "\n";
    std::cout << "C++ version: " << __cplusplus << std::endl;

    return EXIT_SUCCESS;
}
