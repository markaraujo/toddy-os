/* Toddy's native test-process adapter for the published BDB 5.3 Tcl contract.
 * The upstream db_repsite.cpp source is absent from the published archive.
 * Every database operation below invokes the actual frozen Berkeley DB API.
 * This test-only program is never installed in the production package.
 */
#define _POSIX_C_SOURCE 200809L
#define _DEFAULT_SOURCE 1
#include <sys/types.h>
#include <db.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

static DB_ENV *environment;
static DB *database;
static FILE *diagnostics;
static char *home;
static int opened;

static int failure(const char *operation, int result)
{
    fprintf(stderr, "db_repsite: %s: %s (%d)\n", operation,
            db_strerror(result), result);
    return 1;
}

static int port_number(const char *text, unsigned int *port, int allow_zero)
{
    char *end;
    unsigned long value;
    if (!text || !*text || *text == '-') return EINVAL;
    errno = 0;
    value = strtoul(text, &end, 10);
    if (errno || *end || value > 65535 || (!allow_zero && value == 0))
        return EINVAL;
    *port = (unsigned int)value;
    return 0;
}

static int site(const char *host, unsigned int port, int local, int peer)
{
    DB_SITE *handle = NULL;
    int result = environment->repmgr_site(environment, host, port, &handle, 0);
    if (!result)
        result = handle->set_config(handle, local ? DB_LOCAL_SITE : DB_BOOTSTRAP_HELPER, 1);
    if (!result && peer) result = handle->set_config(handle, DB_REPMGR_PEER, 1);
    if (handle) {
        int close_result = handle->close(handle);
        if (!result) result = close_result;
    }
    return result;
}

static int command(int count, char **words)
{
    const char *name = words[0];
    unsigned int port;
    int result;
    if (!strcmp(name, "home") && count == 2 && !opened) {
        char *replacement = strdup(words[1]);
        if (!replacement) return ENOMEM;
        free(home);
        home = replacement;
        return 0;
    }
    if (!strcmp(name, "output") && count == 2) {
        /* Keep errors/verbose output out of the line-oriented reply channel. */
        FILE *replacement = fopen(words[1], "w");
        if (!replacement) return errno;
        setvbuf(replacement, NULL, _IOLBF, 0);
        environment->set_errfile(environment, replacement);
        environment->set_msgfile(environment, replacement);
        if (diagnostics) fclose(diagnostics);
        diagnostics = replacement;
        return 0;
    }
    if (!strcmp(name, "local") && count == 2) {
        if ((result = port_number(words[1], &port, 0))) return result;
        return site("127.0.0.1", port, 1, 0);
    }
    if (!strcmp(name, "remote") && (count == 3 || count == 4)) {
        int peer = count == 4;
        if (peer && strcmp(words[1], "-p")) return EINVAL;
        if ((result = port_number(words[count - 1], &port, 0))) return result;
        return site(words[count - 2], port, 0, peer);
    }
    if (!strcmp(name, "open_env") && count == 1 && !opened && home) {
        result = environment->open(environment, home,
            DB_CREATE | DB_INIT_MPOOL | DB_INIT_LOCK | DB_INIT_LOG |
            DB_INIT_TXN | DB_INIT_REP | DB_THREAD, 0600);
        if (!result) opened = 1;
        return result;
    }
    if (!strcmp(name, "start") && count == 2 && opened) {
        u_int32_t policy;
        if (!strcmp(words[1], "master")) policy = DB_REP_MASTER;
        else if (!strcmp(words[1], "client")) policy = DB_REP_CLIENT;
        else if (!strcmp(words[1], "election")) policy = DB_REP_ELECTION;
        else return EINVAL;
        result = environment->repmgr_start(environment, 3, policy);
        /* DB_REP_IGNORE is an actual API result for a subordinate listener,
         * explicitly asserted by repmgr102. Do not turn other errors into it. */
        if (!result) puts("Successful");
        else puts(db_strerror(result));
        return result == DB_REP_IGNORE ? 0 : result;
    }
    if (!strcmp(name, "open_db") && count == 2 && opened && !database) {
        result = db_create(&database, environment, 0);
        if (result) return result;
        result = database->open(database, NULL, words[1], NULL, DB_BTREE,
                                DB_CREATE | DB_AUTO_COMMIT | DB_THREAD, 0600);
        if (result) {
            database->close(database, 0);
            database = NULL;
        }
        return result;
    }
    if (!strcmp(name, "put") && count == 3 && database) {
        DBT key = {0}, value = {0};
        key.data = words[1]; key.size = (u_int32_t)strlen(words[1]);
        value.data = words[2]; value.size = (u_int32_t)strlen(words[2]);
        return database->put(database, NULL, &key, &value, DB_AUTO_COMMIT);
    }
    if (!strcmp(name, "is_connected") && count == 2 && opened) {
        DB_REPMGR_SITE *sites = NULL;
        u_int count_sites = 0;
        int connected = 0;
        if ((result = port_number(words[1], &port, 1))) return result;
        result = environment->repmgr_site_list(environment, &count_sites, &sites);
        if (result) return result;
        for (u_int i = 0; i < count_sites; ++i)
            if ((!port || sites[i].port == port) && sites[i].status == DB_REPMGR_CONNECTED)
                connected = 1;
        free(sites);
        printf("%d\n", connected);
        return 0;
    }
    if (!strcmp(name, "echo") && count >= 2) {
        for (int i = 1; i < count; ++i) printf("%s%s", i == 1 ? "" : " ", words[i]);
        putchar('\n');
        return 0;
    }
    return EINVAL;
}

int main(void)
{
    char *line = NULL;
    size_t capacity = 0;
    ssize_t length;
    int failed = 0, result;
    if (geteuid() == 0) {
        fputs("db_repsite: run only as the disposable test user\n", stderr);
        return 2;
    }
    setvbuf(stdout, NULL, _IOLBF, 0);
    if ((result = db_env_create(&environment, 0))) return failure("db_env_create", result);
    environment->set_errpfx(environment, "toddy-test-repsite");
    while ((length = getline(&line, &capacity, stdin)) >= 0) {
        char *words[16], *state, *word;
        int count = 0;
        if (length > 8192 || memchr(line, '\0', (size_t)length)) {
            failed = failure("invalid command length/encoding", EINVAL);
            break;
        }
        word = strtok_r(line, " \t\r\n", &state);
        while (word && count < 16) {
            words[count++] = word;
            word = strtok_r(NULL, " \t\r\n", &state);
        }
        if (!count) continue;
        if (word) { failed = failure("too many command words", EINVAL); break; }
        if (!strcmp(words[0], "exit") && count == 1) break;
        if ((result = command(count, words))) { failed = failure(words[0], result); break; }
    }
    if (ferror(stdin)) failed = failure("read command", EIO);
    /* EOF is a graceful shutdown. Default signals deliberately remain abrupt
     * for repmgr102's actual process-death/failchk recovery assertions. */
    if (database && (result = database->close(database, 0))) failed = failure("close database", result);
    if ((result = environment->close(environment, 0))) failed = failure("close environment", result);
    if (diagnostics && fclose(diagnostics)) failed = 1;
    free(home);
    free(line);
    return failed;
}
