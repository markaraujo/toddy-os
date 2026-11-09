#include <assert.h>
#include <libxcvt/libxcvt.h>
#include <stdio.h>
#include <stdlib.h>

static void validate(const struct libxcvt_mode_info *m)
{
    assert(m && m->hdisplay == 1920 && m->vdisplay == 1080);
    assert(m->hsync_start > m->hdisplay && m->hsync_end > m->hsync_start);
    assert(m->htotal > m->hsync_end);
    assert(m->vsync_start > m->vdisplay && m->vsync_end > m->vsync_start);
    assert(m->vtotal > m->vsync_end);
    assert(m->dot_clock > 0 && m->vrefresh > 59 && m->vrefresh <= 61);
    assert(!(m->mode_flags & LIBXCVT_MODE_FLAG_INTERLACE));
}

int main(void)
{
    struct libxcvt_mode_info *normal = libxcvt_gen_mode_info(1920, 1080, 60, false, false);
    struct libxcvt_mode_info *reduced = libxcvt_gen_mode_info(1920, 1080, 60, true, false);
    validate(normal);
    validate(reduced);
    assert(reduced->dot_clock < normal->dot_clock);
    printf("native CVT1920x1080 normal=%llu reduced=%llu refresh=%.3f/%.3f\n",
           (unsigned long long)normal->dot_clock, (unsigned long long)reduced->dot_clock,
           normal->vrefresh, reduced->vrefresh);
    free(normal);
    free(reduced);
    return 0;
}
