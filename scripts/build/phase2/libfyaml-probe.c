#include <libfyaml.h>
#include <assert.h>
#include <string.h>

int main(void) {
    const char *value = "ação 日本語";
    struct fy_document *doc = fy_document_build_from_string(NULL, "name: ação 日本語\nextras: [git, terminal]\n", FY_NT);
    assert(doc);
    struct fy_node *node = fy_node_mapping_lookup_by_string(fy_document_root(doc), "name", FY_NT);
    assert(node);
    size_t length = 0;
    const char *scalar = fy_node_get_scalar(node, &length);
    assert(scalar && length == strlen(value) && !memcmp(scalar, value, length));
    fy_document_destroy(doc);
    doc = fy_document_build_from_string(NULL, "name: [broken\n", FY_NT);
    assert(!doc);
    return 0;
}
