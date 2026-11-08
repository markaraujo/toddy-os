/* Unknown-ID lookup is a native API fixture, not PCI hardware qualification. */
#include <assert.h>
#include <stddef.h>
#include <pciaccess.h>
#include <stdio.h>
int main(void) {
    struct pci_id_match fixture={.vendor_id=0xffff,.device_id=0xffff,
        .subvendor_id=0xffff,.subdevice_id=0xffff};
    const char *device=(void *)1,*vendor=(void *)1,*subdevice=(void *)1,*subvendor=(void *)1;
    pci_get_strings(&fixture,&device,&vendor,&subdevice,&subvendor);
    assert(device==NULL && vendor==NULL && subdevice==NULL && subvendor==NULL);
    pci_system_cleanup();
    puts("native-pciaccess-unknown-id-cleanup");
    return 0;
}
