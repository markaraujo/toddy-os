#include <popt.h>
#include <stdio.h>
#include <string.h>

int main(void)
{
    int count = 0;
    struct poptOption options[] = {
        { "count", 'c', POPT_ARG_INT, &count, 'c', "number of items", "N" },
        POPT_TABLEEND
    };
    const char *bad[] = { "toddy-popt", "--unknown" };
    const char *good[] = { "toddy-popt", "--count", "42", "--", "entrada" };

    for (int i = 0; i < 2; ++i) {
        count = 0;
        poptContext ctx = poptGetContext(bad[0], 2, bad, options, 0);
        if (!ctx || poptGetNextOpt(ctx) != POPT_ERROR_BADOPT ||
            strcmp(poptBadOption(ctx, POPT_BADOPTION_NOALIAS), bad[1]) != 0 || count != 0)
            return 1;
        poptFreeContext(ctx);

        ctx = poptGetContext(good[0], 5, good, options, 0);
        if (!ctx || poptGetNextOpt(ctx) != 'c' || count != 42 || poptGetNextOpt(ctx) != -1)
            return 1;
        const char *arg = poptGetArg(ctx);
        if (!arg || strcmp(arg, "entrada") != 0 || poptGetArg(ctx))
            return 1;
        poptFreeContext(ctx);
    }
    puts("Popt unknown option refusal and two typed argument recoveries passed");
    return 0;
}
