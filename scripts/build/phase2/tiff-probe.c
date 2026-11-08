#include <tiffio.h>
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

int main(void) {
    char path[]="/tmp/toddy-tiff-XXXXXX";
    int fd=mkstemp(path);assert(fd>=0);assert(close(fd)==0);
    const uint16_t codecs[]={COMPRESSION_LZW,COMPRESSION_ADOBE_DEFLATE};
    unsigned char row[]={0,32,64,255,128,0},decoded[sizeof row];
    TIFFOpenOptions *options=TIFFOpenOptionsAlloc();assert(options);
    TIFFOpenOptionsSetMaxSingleMemAlloc(options,16*1024*1024);
    for(size_t i=0;i<sizeof codecs/sizeof codecs[0];i++) {
        TIFF *p=TIFFOpenExt(path,"w",options);assert(p);
        assert(TIFFSetField(p,TIFFTAG_IMAGEWIDTH,2));
        assert(TIFFSetField(p,TIFFTAG_IMAGELENGTH,1));
        assert(TIFFSetField(p,TIFFTAG_SAMPLESPERPIXEL,3));
        assert(TIFFSetField(p,TIFFTAG_BITSPERSAMPLE,8));
        assert(TIFFSetField(p,TIFFTAG_ORIENTATION,ORIENTATION_TOPLEFT));
        assert(TIFFSetField(p,TIFFTAG_PLANARCONFIG,PLANARCONFIG_CONTIG));
        assert(TIFFSetField(p,TIFFTAG_PHOTOMETRIC,PHOTOMETRIC_RGB));
        assert(TIFFSetField(p,TIFFTAG_COMPRESSION,codecs[i]));
        assert(TIFFWriteScanline(p,row,0,0)==1);TIFFClose(p);
        p=TIFFOpenExt(path,"r",options);assert(p);
        uint32_t width=0,height=0;
        assert(TIFFGetField(p,TIFFTAG_IMAGEWIDTH,&width));
        assert(TIFFGetField(p,TIFFTAG_IMAGELENGTH,&height));
        assert(width==2&&height==1&&TIFFScanlineSize(p)==(tmsize_t)sizeof row);
        assert(TIFFReadScanline(p,decoded,0,0)==1&&memcmp(row,decoded,sizeof row)==0);
        TIFFClose(p);
    }
    FILE *bad=fopen(path,"wb");assert(bad);assert(fwrite("bad",1,3,bad)==3);assert(fclose(bad)==0);
    assert(TIFFOpenExt(path,"r",options)==NULL);TIFFOpenOptionsFree(options);assert(unlink(path)==0);
    puts("Native TIFF LZW/Deflate exact RGB roundtrip and invalid header refusal with16MiB allocation bound passed");
    return 0;
}
