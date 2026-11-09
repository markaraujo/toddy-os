#include <nspr/nspr.h>
#include <nspr/prerror.h>
#include <assert.h>
#include <stdio.h>
#include <string.h>
static PRLock *lock;
static int count;
static void worker(void *unused) {
 (void)unused;
 for(int n=0;n<500;n++){PR_Lock(lock);count++;assert(PR_Unlock(lock)==PR_SUCCESS);}
}
int main(int argc,char **argv) {
 assert(argc==2 && PR_VersionCheck("4.40") && !PR_VersionCheck("99.0"));
 PR_Init(PR_USER_THREAD,PR_PRIORITY_NORMAL,0);
 for(int cycle=0;cycle<2;cycle++) {
  lock=PR_NewLock();assert(lock);count=0;
  PRThread *a=PR_CreateThread(PR_USER_THREAD,worker,NULL,PR_PRIORITY_NORMAL,PR_GLOBAL_THREAD,PR_JOINABLE_THREAD,0);
  PRThread *b=PR_CreateThread(PR_USER_THREAD,worker,NULL,PR_PRIORITY_NORMAL,PR_GLOBAL_THREAD,PR_JOINABLE_THREAD,0);
  assert(a && b && PR_JoinThread(a)==PR_SUCCESS && PR_JoinThread(b)==PR_SUCCESS && count==1000);PR_DestroyLock(lock);
  const char *message="Toddy private file roundtrip";char output[64]={0};
  PRFileDesc *file=PR_Open(argv[1],PR_RDWR|PR_CREATE_FILE|PR_EXCL,0600);assert(file);
  assert(PR_Write(file,message,strlen(message))==(PRInt32)strlen(message));assert(PR_Seek(file,0,PR_SEEK_SET)==0);
  assert(PR_Read(file,output,sizeof(output))==(PRInt32)strlen(message) && !strcmp(output,message));assert(PR_Close(file)==PR_SUCCESS && PR_Delete(argv[1])==PR_SUCCESS);
  assert(!PR_Open(argv[1],PR_RDONLY,0) && PR_GetError()==PR_FILE_NOT_FOUND_ERROR);
 }
 assert(PR_Cleanup()==PR_SUCCESS);
 puts("{\"version_compatibility_and_refusal\":true,\"real_joinable_threads_locked_updates\":1000,\"private_file_roundtrip_and_missing_file_refusal\":true,\"recovery_cycles\":2}");return 0;
}
