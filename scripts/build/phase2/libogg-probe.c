#include <assert.h>
#include <ogg/ogg.h>
#include <stdio.h>
#include <string.h>

int main(void)
{
    oggpack_buffer writer,reader;
    oggpack_writeinit(&writer);
    oggpack_write(&writer,0x00204080,32);
    oggpack_write(&writer,0x546f6464,32);
    assert(oggpack_bytes(&writer)==8);
    oggpack_readinit(&reader,oggpack_get_buffer(&writer),8);
    assert(oggpack_read(&reader,32)==0x00204080);
    assert(oggpack_read(&reader,32)==0x546f6464);
    assert(oggpack_read(&reader,1)==-1);
    oggpack_writeclear(&writer);
    const unsigned char text[]="Toddy offline";
    ogg_packet input={0},decoded;
    input.packet=(unsigned char *)text;input.bytes=sizeof(text)-1;
    input.b_o_s=1;input.e_o_s=1;
    ogg_stream_state encoder,decoder;
    ogg_sync_state sync,bad;
    assert(ogg_stream_init(&encoder,42)==0 && ogg_stream_init(&decoder,42)==0);
    assert(ogg_sync_init(&sync)==0 && ogg_sync_init(&bad)==0);
    assert(ogg_stream_packetin(&encoder,&input)==0);
    ogg_page page,loaded;
    assert(ogg_stream_flush(&encoder,&page)==1);
    assert(ogg_page_serialno(&page)==42 && ogg_page_bos(&page) && ogg_page_eos(&page));
    long size=page.header_len+page.body_len;
    char *buffer=ogg_sync_buffer(&sync,size);assert(buffer);
    memcpy(buffer,page.header,page.header_len);memcpy(buffer+page.header_len,page.body,page.body_len);
    assert(ogg_sync_wrote(&sync,size)==0 && ogg_sync_pageout(&sync,&loaded)==1);
    assert(ogg_stream_pagein(&decoder,&loaded)==0 && ogg_stream_packetout(&decoder,&decoded)==1);
    assert(decoded.bytes==(long)sizeof(text)-1 && memcmp(decoded.packet,text,sizeof(text)-1)==0);
    buffer=ogg_sync_buffer(&bad,size);assert(buffer);
    memcpy(buffer,page.header,page.header_len);memcpy(buffer+page.header_len,page.body,page.body_len);
    buffer[size-1]^=1;
    assert(ogg_sync_wrote(&bad,size)==0 && ogg_sync_pageout(&bad,&loaded)==-1);
    ogg_sync_clear(&bad);ogg_sync_clear(&sync);
    ogg_stream_clear(&decoder);ogg_stream_clear(&encoder);
    puts("native Ogg bitpack/end refusal/packet-page roundtrip and corrupted-CRC refusal; no audio output");
    return 0;
}
