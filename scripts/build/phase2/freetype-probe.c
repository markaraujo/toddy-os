/* Toddy native API/bitmap parser fixture, not a desktop-font qualification. */
#include <ft2build.h>
#include FT_FREETYPE_H
#include <string.h>
static const unsigned char font[]=
"STARTFONT 2.1\nFONT -toddy-proof-medium-r-normal--8-80-75-75-c-80-iso10646-1\n"
"SIZE 8 75 75\nFONTBOUNDINGBOX 8 8 0 0\nSTARTPROPERTIES 2\n"
"FONT_ASCENT 8\nFONT_DESCENT 0\nENDPROPERTIES\nCHARS 1\nSTARTCHAR A\n"
"ENCODING 65\nSWIDTH 1000 0\nDWIDTH 8 0\nBBX 8 8 0 0\nBITMAP\n"
"18\n24\n42\n7E\n42\n42\n42\n00\nENDCHAR\nENDFONT\n";
int main(void) {
    FT_Library library;FT_Face face;FT_Int major,minor,patch;
    const unsigned char pixels[]={0x18,0x24,0x42,0x7e,0x42,0x42,0x42,0};
    if (FT_Init_FreeType(&library)) return 1;
    FT_Library_Version(library,&major,&minor,&patch);
    if (major!=2 || minor!=14 || patch!=3) return 2;
    if (FT_New_Memory_Face(library,font,sizeof(font)-1,0,&face)) return 3;
    if (face->num_fixed_sizes!=1 || FT_Select_Size(face,0)) return 4;
    if (!FT_Get_Char_Index(face,'A') || FT_Load_Char(face,'A',FT_LOAD_RENDER)) return 5;
    if (face->glyph->bitmap.width!=8 || face->glyph->bitmap.rows!=8 || face->glyph->bitmap.pitch!=1) return 6;
    if (memcmp(face->glyph->bitmap.buffer,pixels,sizeof(pixels))) return 7;
    if (FT_Done_Face(face) || FT_Done_FreeType(library)) return 8;
    return 0;
}
