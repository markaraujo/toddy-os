/* Pure native subject decoding, not an authorization decision or daemon fixture. */
#include <polkit/polkit.h>
#include <polkit/polkitprivate.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
static GVariant *process_subject(unsigned kind,guint64 start) {
    GVariantBuilder b;g_variant_builder_init(&b,G_VARIANT_TYPE_VARDICT);
    if(kind==5)g_variant_builder_add(&b,"{sv}","pid",g_variant_new_string("bad"));
    else g_variant_builder_add(&b,"{sv}","pid",g_variant_new_uint32((guint32)getpid()));
    if(kind==6)g_variant_builder_add(&b,"{sv}","start-time",g_variant_new_string("bad"));
    else g_variant_builder_add(&b,"{sv}","start-time",g_variant_new_uint64(start));
    if(kind==1)g_variant_builder_add(&b,"{sv}","uid",g_variant_new_uint32((guint32)getuid()));
    else if(kind==2)g_variant_builder_add(&b,"{sv}","uid",g_variant_new_string("bad"));
    else if(kind!=8)g_variant_builder_add(&b,"{sv}","uid",g_variant_new_int32((gint32)getuid()));
    if(kind==3)g_variant_builder_add(&b,"{sv}","uid",g_variant_new_int32((gint32)getuid()));
    if(kind==7)g_variant_builder_add(&b,"{sv}","pidfd",g_variant_new_string("bad"));
    if(kind==4)g_variant_builder_add(&b,"{sv}","future-attribute",g_variant_new_string("data"));
    return g_variant_ref_sink(g_variant_new("(s@a{sv})","unix-process",g_variant_builder_end(&b)));
}
static int check(GVariant *v,gboolean accept) {
    GError *error=NULL;PolkitSubject *s=polkit_subject_new_for_gvariant(v,&error);
    int result=0;
    if(accept) {if(!s||error)result=1;}
    else if(s||!error||error->domain!=POLKIT_ERROR||error->code!=POLKIT_ERROR_FAILED)result=2;
    g_clear_object(&s);g_clear_error(&error);
    if(!accept) {s=polkit_subject_new_for_gvariant(v,NULL);if(s)result=3;g_clear_object(&s);}
    g_variant_unref(v);return result;
}
static GVariant *other(const char *kind,const char *key,GVariant *value) {
    GVariantBuilder b;g_variant_builder_init(&b,G_VARIANT_TYPE_VARDICT);g_variant_builder_add(&b,"{sv}",key,value);
    return g_variant_ref_sink(g_variant_new("(s@a{sv})",kind,g_variant_builder_end(&b)));
}
int main(int argc,char **argv) {
    gboolean corrected=argc==2&&!strcmp(argv[1],"--corrected");
    PolkitSubject *self=polkit_unix_process_new_for_owner(getpid(),0,getuid());if(!self)return 10;
    guint64 start=polkit_unix_process_get_start_time(POLKIT_UNIX_PROCESS(self));g_object_unref(self);if(!start)return 11;
    if(check(process_subject(0,start),TRUE))return 12;
    if(!corrected) {
        if(check(process_subject(1,start),TRUE)||check(process_subject(3,start),TRUE))return 13;
        puts("{\"scope\":\"UNQUALIFIED original source diagnosis\",\"valid_signed_uid_accepted\":true,\"malformed_unsigned_uid_accepted\":true,\"duplicate_uid_accepted\":true}");return 0;
    }
    unsigned rejected[]={1,2,3,5,6,7};
    for(unsigned i=0;i<sizeof rejected/sizeof rejected[0];i++)if(check(process_subject(rejected[i],start),FALSE))return 20+(int)i;
    if(check(process_subject(4,start),TRUE)||check(process_subject(8,start),TRUE))return 30;
    if(check(other("system-bus-name","name",g_variant_new_uint32(7)),FALSE))return 31;
    if(check(other("unix-session","session-id",g_variant_new_int32(7)),FALSE))return 32;
    if(check(other("system-bus-name","name",g_variant_new_string(":1.7")),TRUE))return 33;
    if(check(other("system-bus-name","name",g_variant_new_string("invalid-name")),FALSE))return 34;
    puts("{\"scope\":\"Corrected pure subject decoding, not authorization\",\"cases\":13,\"invalid_subject_cases_refused\":9,\"error_pointer_null_controls\":9,\"legacy_missing_uid_preserved\":true,\"unknown_attribute_preserved_as_data\":true}");return 0;
}
