#include <atk/atk.h>
#include <atspi/atspi.h>

int main(void) {
    AtkStateSet *atk = atk_state_set_new();
    g_assert_true(atk_state_set_add_state(atk, ATK_STATE_FOCUSED));
    g_assert_true(atk_state_set_contains_state(atk, ATK_STATE_FOCUSED));
    g_assert_true(atk_state_set_remove_state(atk, ATK_STATE_FOCUSED));
    g_assert_false(atk_state_set_contains_state(atk, ATK_STATE_FOCUSED));
    g_object_unref(atk);
    AtspiStateSet *atspi = atspi_state_set_new(NULL);
    atspi_state_set_add(atspi, ATSPI_STATE_FOCUSED);
    g_assert_true(atspi_state_set_contains(atspi, ATSPI_STATE_FOCUSED));
    atspi_state_set_remove(atspi, ATSPI_STATE_FOCUSED);
    g_assert_false(atspi_state_set_contains(atspi, ATSPI_STATE_FOCUSED));
    g_object_unref(atspi);
    return 0;
}
