#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <vorbis/vorbisenc.h>
#define OV_EXCLUDE_STATIC_CALLBACKS
#include <vorbis/vorbisfile.h>
int main(void) {
    vorbis_info info; vorbis_comment tags; vorbis_dsp_state dsp; vorbis_block block;
    vorbis_info_init(&info);
    assert(vorbis_encode_init_vbr(&info,2,48000,0.4f)==0);
    assert(info.channels==2 && info.rate==48000);
    vorbis_comment_init(&tags);vorbis_comment_add_tag(&tags,"TITLE","Toddy offline");
    assert(strcmp(vorbis_comment_query(&tags,"TITLE",0),"Toddy offline")==0);
    assert(vorbis_analysis_init(&dsp,&info)==0);
    assert(vorbis_block_init(&dsp,&block)==0);
    ogg_packet header,comment,code;assert(vorbis_analysis_headerout(&dsp,&tags,&header,&comment,&code)==0);
    assert(header.bytes>7 && memcmp(header.packet+1,"vorbis",6)==0);
    vorbis_info decoded;vorbis_comment decoded_tags;vorbis_info_init(&decoded);vorbis_comment_init(&decoded_tags);
    assert(vorbis_synthesis_headerin(&decoded,&decoded_tags,&header)==0);
    assert(vorbis_synthesis_headerin(&decoded,&decoded_tags,&comment)==0);
    assert(vorbis_synthesis_headerin(&decoded,&decoded_tags,&code)==0);
    assert(decoded.channels==2 && decoded.rate==48000);
    ogg_packet invalid={0};unsigned char bad[]="invalid";invalid.packet=bad;invalid.bytes=7;
    assert(vorbis_synthesis_headerin(&decoded,&decoded_tags,&invalid)<0);
    vorbis_comment_clear(&decoded_tags);vorbis_info_clear(&decoded);
    vorbis_block_clear(&block);vorbis_dsp_clear(&dsp);vorbis_comment_clear(&tags);vorbis_info_clear(&info);
    puts("native Vorbis encoder/header decoding/metadata and malformed-header refusal; no audible output");
    return 0;
}
