#!/bin/bash
set -euo pipefail
db_stat -V | grep -F '5.3.28'
fixture=$(mktemp -d /tmp/toddy-db.XXXXXX)
trap 'rm -rf "$fixture"' EXIT
mkdir "$fixture/environment"
cat > "$fixture/probe.c" <<'C'
#include <db.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(call) do {int rc=(call);if(rc){fprintf(stderr,"%s: %s\n",#call,db_strerror(rc));return 1;}} while(0)
int main(int argc,char **argv) {
 DB_ENV *env;DB *db;DB_TXN *txn;DBT key={0},value={0};
 const char expected[]="committed native data";
 int a,b,c;
 if(argc!=3 || !db_version(&a,&b,&c) || a!=5 || b!=3 || c!=28)return 2;
 CHECK(db_env_create(&env,0));
 CHECK(env->open(env,argv[2],DB_CREATE|DB_INIT_MPOOL|DB_INIT_LOCK|DB_INIT_LOG|DB_INIT_TXN,0600));
 CHECK(db_create(&db,env,0));
 CHECK(db->open(db,NULL,"data.db",NULL,DB_BTREE,DB_CREATE|DB_AUTO_COMMIT,0600));
 key.data=(void *)"toddy";key.size=5;
 if(!strcmp(argv[1],"write")) {
  CHECK(env->txn_begin(env,NULL,&txn,0));value.data=(void *)expected;value.size=sizeof(expected);
  CHECK(db->put(db,txn,&key,&value,0));CHECK(txn->commit(txn,0));
  CHECK(env->txn_begin(env,NULL,&txn,0));value.data=(void *)"must roll back";value.size=15;
  CHECK(db->put(db,txn,&key,&value,0));CHECK(txn->abort(txn));
 } else {
  value.flags=DB_DBT_MALLOC;CHECK(db->get(db,NULL,&key,&value,0));
  if(value.size!=sizeof(expected)||memcmp(value.data,expected,sizeof(expected)))return 3;
  free(value.data);
 }
 CHECK(db->close(db,0));CHECK(env->close(env,0));return 0;
}
C
cc "$fixture/probe.c" -ldb -o "$fixture/probe"
"$fixture/probe" write "$fixture/environment"
"$fixture/probe" read "$fixture/environment"
printf 'Native production DB commit/persistence/reopen/rollback passed\n'
