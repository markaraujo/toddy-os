#include <assert.h>
#include <libevdev/libevdev.h>
#include <stdio.h>
#include <string.h>

int main(void)
{
    struct libevdev *dev = libevdev_new();
    assert(dev && libevdev_get_fd(dev) == -1);
    libevdev_set_name(dev, "Toddy virtual input API");
    assert(strcmp(libevdev_get_name(dev), "Toddy virtual input API") == 0);
    assert(libevdev_enable_property(dev, INPUT_PROP_POINTER) == 0);
    assert(libevdev_has_property(dev, INPUT_PROP_POINTER));
    assert(libevdev_enable_event_type(dev, EV_KEY) == 0);
    assert(libevdev_enable_event_code(dev, EV_KEY, KEY_A, NULL) == 0);
    assert(libevdev_has_event_code(dev, EV_KEY, KEY_A));
    assert(libevdev_set_event_value(dev, EV_KEY, KEY_A, 1) == 0);
    assert(libevdev_get_event_value(dev, EV_KEY, KEY_A) == 1);
    assert(strcmp(libevdev_event_code_get_name(EV_KEY, KEY_A), "KEY_A") == 0);
    assert(libevdev_disable_event_code(dev, EV_KEY, KEY_A) == 0);
    assert(!libevdev_has_event_code(dev, EV_KEY, KEY_A));
    libevdev_free(dev);
    struct libevdev *invalid = NULL;
    assert(libevdev_new_from_fd(-1, &invalid) < 0 && invalid == NULL);
    puts("libevdev native name/capability/event-state/code mapping/cleanup/invalid-FD refusal");
    return 0;
}
