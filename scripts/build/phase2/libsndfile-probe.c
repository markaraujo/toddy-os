#include <assert.h>
#include <sndfile.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
int main(void) {
    char path[]="/tmp/toddy-sndfile-XXXXXX";int fd=mkstemp(path);assert(fd>=0);
    SF_INFO info={0};info.samplerate=48000;info.channels=2;info.format=SF_FORMAT_WAV|SF_FORMAT_PCM_16;
    SNDFILE *file=sf_open_fd(fd,SFM_WRITE,&info,1);assert(file);
    short pcm[8]={0,0,8192,-8192,16384,-16384,0,0};assert(sf_writef_short(file,pcm,4)==4);assert(sf_close(file)==0);
    memset(&info,0,sizeof(info));file=sf_open(path,SFM_READ,&info);assert(file);
    assert(info.frames==4 && info.channels==2 && info.samplerate==48000);
    short out[8];assert(sf_readf_short(file,out,4)==4 && memcmp(out,pcm,sizeof(pcm))==0);
    assert(sf_close(file)==0);assert(unlink(path)==0);
    assert(sf_open("/this-path-does-not-exist/toddy.wav",SFM_READ,&info)==NULL);
    puts("native PCM WAV write/reopen/exact samples and absent-file refusal; no device output");return 0;
}
