#include <assert.h>
#include <errno.h>
#include <fcntl.h>
#include <libei.h>
#include <libeis.h>
#include <liboeffis.h>
#include <stdio.h>

int main(void)
{
    int token = 42;
    struct ei *sender = ei_new_sender(&token);
    struct ei *receiver = ei_new_receiver(&token);
    struct eis *server = eis_new(&token);
    struct oeffis *portal = oeffis_new(&token);
    assert(sender && receiver && server && portal);
    assert(ei_is_sender(sender) && !ei_is_sender(receiver));
    assert(ei_get_user_data(sender) == &token && ei_get_user_data(receiver) == &token);
    assert(eis_get_user_data(server) == &token && oeffis_get_user_data(portal) == &token);
    ei_configure_name(sender, "Toddy native sender");
    ei_configure_name(receiver, "Toddy native receiver");
    int fd = oeffis_get_fd(portal);
    assert(fd >= 0 && fcntl(fd, F_GETFD) >= 0);
    errno = 0;
    assert(oeffis_get_eis_fd(portal) == -1 && errno == ENODEV);
    assert(oeffis_unref(portal) == NULL);
    errno = 0;
    assert(fcntl(fd, F_GETFD) == -1 && errno == EBADF);
    assert(eis_unref(server) == NULL);
    assert(ei_unref(receiver) == NULL && ei_unref(sender) == NULL);
    puts("native EI/EIS/Oeffis context/state/user-data/fd cleanup and disconnected-portal refusal");
    return 0;
}
