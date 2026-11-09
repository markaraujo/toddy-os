#include <assert.h>
#include <gusb.h>
#include <stdio.h>
#include <string.h>
int main(void) {
    assert(strcmp(g_usb_version_string(),"0.4.9")==0);
    GError *error=NULL;GUsbContext *context=g_usb_context_new(&error);assert(context && !error);
    GMainContext *main_context=g_main_context_new();g_usb_context_set_main_context(context,main_context);assert(g_usb_context_get_main_context(context)==main_context);g_main_context_unref(main_context);
    GUsbDevice *device=g_usb_context_find_by_vid_pid(context,0xffff,0xffff,&error);
    assert(!device && error && error->domain==G_USB_DEVICE_ERROR && error->code==G_USB_DEVICE_ERROR_NO_DEVICE);
    g_clear_error(&error);g_object_unref(context);
    puts("native GUsb context/version/configuration and unknown-device refusal; no USB device operation");return 0;
}
