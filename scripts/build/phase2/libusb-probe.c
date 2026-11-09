#include <assert.h>
#include <libusb.h>
#include <stdio.h>
int main(void) {
    const struct libusb_version *version=libusb_get_version();assert(version && version->major==1 && version->minor==0 && version->micro==30);
    libusb_context *context=NULL;
    struct libusb_init_option option={.option=LIBUSB_OPTION_NO_DEVICE_DISCOVERY};
    assert(libusb_init_context(&context,&option,1)==0 && context);
    assert(libusb_set_option(context,(enum libusb_option)999)==LIBUSB_ERROR_INVALID_PARAM);
    libusb_device **list=NULL;assert(libusb_get_device_list(context,&list)==0 && list);
    libusb_free_device_list(list,1);libusb_exit(context);
    puts("native libusb no-discovery lifecycle/version/empty-list and invalid-option refusal; no physical USB access");return 0;
}
