#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/h06/common.sh
chroot_run <<'NATIVE'
set -euo pipefail
[[ $(pkg-config --modversion graphene-1.0) == 1.10.8 ]]
[[ $(dpkg-query -W -f='${Status}' graphene) == 'install ok installed' ]]
test -z "$(dpkg --audit)"
apt-get check
work=$(mktemp -d /tmp/toddy-graphene-consumer.XXXXXX)
trap 'rm -rf "$work"' EXIT
cat > "$work/probe.c" <<'C'
#include <graphene.h>
#include <graphene-gobject.h>
#include <math.h>
int main(void) {
    graphene_vec3_t vector,unit;graphene_matrix_t matrix;graphene_point3d_t origin,translation,result;
    graphene_vec3_init(&vector,3,4,0);
    if (fabsf(graphene_vec3_length(&vector)-5)>0.00001f) return 1;
    graphene_vec3_normalize(&vector,&unit);
    if (fabsf(graphene_vec3_length(&unit)-1)>0.00001f) return 2;
    graphene_point3d_init(&origin,0,0,0);graphene_point3d_init(&translation,1,2,3);
    graphene_matrix_init_identity(&matrix);graphene_matrix_translate(&matrix,&translation);
    graphene_matrix_transform_point3d(&matrix,&origin,&result);
    if (fabsf(result.x-1)>0.00001f || fabsf(result.y-2)>0.00001f || fabsf(result.z-3)>0.00001f) return 3;
    if (!graphene_point3d_get_type()) return 4;
    return 0;
}
C
cc "$work/probe.c" $(pkg-config --cflags --libs graphene-1.0 graphene-gobject-1.0) -lm -o "$work/probe"
"$work/probe"
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import gi
gi.require_version('Graphene','1.0')
from gi.repository import Graphene
point=Graphene.Point3D();point.init(1,2,3)
assert (point.x,point.y,point.z)==(1,2,3)
PY
NATIVE
