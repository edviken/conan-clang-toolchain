#include <gtest/gtest.h>
#include <variant>

#ifndef _LIBCPP_VERSION
#error "This test must use libc++ headers"
#endif

void throw_from_library();

TEST(LlvmRuntime, CatchesBadVariantAccessAcrossSharedLibrary)
{
    EXPECT_THROW(throw_from_library(), std::bad_variant_access);
}

TEST(LlvmRuntime, CatchesLocalBadVariantAccess)
{
    EXPECT_THROW(throw std::bad_variant_access{}, std::bad_variant_access);
}

#if defined(__cpp_explicit_this_parameter) && __cpp_explicit_this_parameter >= 202110L
struct ExplicitObjectParameter {
    int value;
    int get(this const ExplicitObjectParameter& self) { return self.value; }
};

TEST(ClangLanguage, SupportsExplicitObjectParameters)
{
    EXPECT_EQ(ExplicitObjectParameter{23}.get(), 23);
}
#endif
