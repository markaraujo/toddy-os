#include <assert.h>
#include <mtdev.h>
#include <mtdev-plumbing.h>
#include <stdio.h>

int main(void)
{
    struct mtdev *dev = mtdev_new();
    assert(dev && mtdev_init(dev) == 0 && mtdev_empty(dev));
    mtdev_set_mt_event(dev, ABS_MT_SLOT, 1);
    mtdev_set_mt_event(dev, ABS_MT_POSITION_X, 1);
    mtdev_set_abs_minimum(dev, ABS_MT_POSITION_X, -100);
    mtdev_set_abs_maximum(dev, ABS_MT_POSITION_X, 1000);
    mtdev_set_abs_fuzz(dev, ABS_MT_POSITION_X, 2);
    mtdev_set_abs_resolution(dev, ABS_MT_POSITION_X, 40);
    assert(mtdev_has_mt_event(dev, ABS_MT_SLOT));
    assert(mtdev_has_mt_event(dev, ABS_MT_POSITION_X));
    assert(mtdev_get_abs_minimum(dev, ABS_MT_POSITION_X) == -100);
    assert(mtdev_get_abs_maximum(dev, ABS_MT_POSITION_X) == 1000);
    assert(mtdev_get_abs_fuzz(dev, ABS_MT_POSITION_X) == 2);
    assert(mtdev_get_abs_resolution(dev, ABS_MT_POSITION_X) == 40);
    struct input_event key = {.type = EV_KEY, .code = BTN_LEFT, .value = 1};
    struct input_event sync = {.type = EV_SYN, .code = SYN_REPORT};
    mtdev_put_event(dev, &key);
    mtdev_put_event(dev, &sync);
    struct input_event out;
    assert(!mtdev_empty(dev));
    mtdev_get_event(dev, &out);
    assert(out.type == EV_KEY && out.code == BTN_LEFT && out.value == 1);
    assert(!mtdev_empty(dev));
    mtdev_get_event(dev, &out);
    assert(out.type == EV_SYN && out.code == SYN_REPORT);
    assert(mtdev_empty(dev));
    mtdev_close_delete(dev);
    assert(mtdev_new_open(-1) == NULL);
    puts("mtdev native capabilities, event frame, cleanup and invalid-FD refusal");
    return 0;
}
