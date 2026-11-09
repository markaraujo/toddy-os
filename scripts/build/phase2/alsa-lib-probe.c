#define _POSIX_C_SOURCE 200809L
#include <alsa/asoundlib.h>
#include <assert.h>
#include <stdio.h>
#include <string.h>

int main(void)
{
    assert(strcmp(snd_asoundlib_version(), "1.2.16.1") == 0);
    const char text[] = "pcm.toddy_null { type null }\n";
    snd_config_t *config = NULL;
    snd_input_t *input = NULL;
    assert(snd_config_top(&config) == 0);
    assert(snd_input_buffer_open(&input, text, sizeof(text)-1) == 0);
    assert(snd_config_load(config, input) == 0);
    assert(snd_input_close(input) == 0);
    snd_pcm_t *pcm = NULL;
    assert(snd_pcm_open_lconf(&pcm, "toddy_null", SND_PCM_STREAM_PLAYBACK, 0, config) == 0);
    assert(snd_pcm_set_params(pcm, SND_PCM_FORMAT_S16_LE, SND_PCM_ACCESS_RW_INTERLEAVED,
                              2, 48000, 0, 100000) == 0);
    short samples[960] = {0};
    assert(snd_pcm_writei(pcm, samples, 480) == 480);
    assert(snd_pcm_drain(pcm) == 0);
    assert(snd_pcm_close(pcm) == 0);
    pcm = NULL;
    assert(snd_pcm_open_lconf(&pcm, "toddy_missing", SND_PCM_STREAM_PLAYBACK, 0, config) < 0);
    assert(pcm == NULL);
    assert(snd_config_delete(config) == 0);
    snd_config_update_free_global();
    puts("native ALSA configuration parse/null PCM stereo48000Hz480frames/drain/close and unknown-PCM refusal");
    return 0;
}
