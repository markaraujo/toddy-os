/* Native PAM module dispatch, deny-by-default and recovery. No password fixture. */
#include <security/pam_appl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
static int converse(int n, const struct pam_message **msg, struct pam_response **out, void *data) {
    (void)n; (void)msg; (void)out; (void)data; return PAM_CONV_ERR;
}
static int check(const char *dir, int allow) {
    struct pam_conv conversation={converse,NULL}; pam_handle_t *p=NULL;
    int r=pam_start_confdir("toddy-probe","tester",&conversation,dir,&p);
    if(r!=PAM_SUCCESS) return 10;
    int auth=pam_authenticate(p,PAM_DISALLOW_NULL_AUTHTOK);
    int account=pam_acct_mgmt(p,0);
    int session=pam_open_session(p,0);
    if(session==PAM_SUCCESS && pam_close_session(p,0)!=PAM_SUCCESS) return 11;
    int end=pam_end(p,auth);
    if(end!=PAM_SUCCESS) return 12;
    if(allow) return auth==PAM_SUCCESS && account==PAM_SUCCESS && session==PAM_SUCCESS ? 0:13;
    return auth!=PAM_SUCCESS && account!=PAM_SUCCESS && session!=PAM_SUCCESS ? 0:14;
}
int main(int argc,char **argv) {
    if(argc!=3 || mkdir(argv[1],0700)!=0) return 1;
    char file[4096]; if(snprintf(file,sizeof file,"%s/toddy-probe",argv[1])>=(int)sizeof file) return 2;
    const char *modules[]={"pam_permit.so","pam_deny.so","absent-toddy.so",NULL,"pam_permit.so"};
    for(size_t i=0;i<sizeof modules/sizeof modules[0];i++) {
        FILE *f=fopen(file,"w");if(!f)return 3;
        if(modules[i]) {
            const char *kinds[]={"auth","account","password","session"};
            for(size_t j=0;j<4;j++)fprintf(f,"%s required %s/%s\n",kinds[j],argv[2],modules[i]);
        } else fputs("malformed-policy\n",f);
        if(fclose(f)!=0)return 4;
        int r=check(argv[1],i==0 || i==4);if(r)return r;
    }
    puts("PAM real allow/deny/missing-module/malformed-policy/recovery passed; no password claim");return 0;
}
