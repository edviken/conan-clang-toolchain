#include <variant>

void throw_from_library()
{
    const std::variant<int, float> value{42};
    (void)std::get<float>(value);
}
