#include <sass/context.h>
#include <sass/version.h>
#include <assert.h>
#include <stdlib.h>
#include <string.h>

int main(void) {
    struct Sass_Data_Context *data = sass_make_data_context(strdup("$navy: #002040; .toddy { color: $navy; &:hover { opacity: 0.9; } }"));
    assert(data && sass_compile_data_context(data) == 0);
    const char *css = sass_context_get_output_string(sass_data_context_get_context(data));
    assert(css && strstr(css, "#002040") && strstr(css, ".toddy:hover"));
    sass_delete_data_context(data);
    data = sass_make_data_context(strdup(".toddy { color:;"));
    assert(data && sass_compile_data_context(data) != 0);
    assert(sass_context_get_error_message(sass_data_context_get_context(data)));
    sass_delete_data_context(data);
    return 0;
}
