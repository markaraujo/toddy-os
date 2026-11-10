/* Root-only native qualification; synthetic new token is stdin-only, never logged. */
#define _GNU_SOURCE
#include <security/pam_appl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
static int converse(int n,const struct pam_message **messages,struct pam_response **out,void *data) {
 struct pam_response *r=calloc((size_t)n,sizeof *r);if(!r)return PAM_BUF_ERR;
 for(int i=0;i<n;i++) {
  if(messages[i]->msg_style==PAM_PROMPT_ECHO_OFF)r[i].resp=strdup((char *)data);
  else if(messages[i]->msg_style!=PAM_TEXT_INFO && messages[i]->msg_style!=PAM_ERROR_MSG) {
   for(int j=0;j<i;j++)if(r[j].resp){explicit_bzero(r[j].resp,strlen(r[j].resp));free(r[j].resp);}
   free(r);return PAM_CONV_ERR;
  }
 }
 *out=r;return PAM_SUCCESS;
}
int main(int argc,char **argv) {
 if(argc!=2 || geteuid()!=0)return 64;
 char *token=NULL;size_t capacity=0;ssize_t n=getline(&token,&capacity,stdin);if(n<0)return 65;
 if(n && token[n-1]=='\n')token[n-1]='\0';
 struct pam_conv conv={converse,token};pam_handle_t *p=NULL;
 int start=pam_start("toddy-password",argv[1],&conv,&p),change=-1;
 if(start==PAM_SUCCESS)change=pam_chauthtok(p,0);
 explicit_bzero(token,capacity);free(token);
 int end=p ? pam_end(p,change):PAM_SYSTEM_ERR;
 printf("{\"start\":%d,\"change\":%d,\"end\":%d}\n",start,change,end);
 return start==PAM_SUCCESS && end==PAM_SUCCESS ? 0:66;
}
