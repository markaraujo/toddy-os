#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
mkdir /build/compile
cd /build/compile
/src/configure --prefix=/usr --libdir=/usr/lib --disable-static > /build/configure.log 2>&1
make -j4 > /build/compile.log 2>&1
timeout 60 ./test/mtdev-matching > /build/upstream-matching.log 2>&1
make DESTDIR=/stage install > /build/stage.log 2>&1
cc -std=c11 -Wall -Wextra -Werror /src/toddy-probe.c -I/stage/usr/include \
    -L/stage/usr/lib -Wl,-rpath,/stage/usr/lib $(PKG_CONFIG_PATH=/stage/usr/lib/pkgconfig pkg-config --cflags --libs mtdev) \
    -o /build/consumer
/build/consumer > /build/consumer.log 2>&1
python3 - <<'PY'
from pathlib import Path
import itertools,json,re
source=Path('/src/test/mtdev-matching.c').read_text();output=Path('/build/upstream-matching.log').read_text()
assert output.rstrip().endswith('done')
cases=[]
for name,end in [('test1','test2'),('test2','speed1')]:
    body=re.search(r'static void '+name+r'\(\)\s*\{(.*?)\n\}',source,re.S).group(1)
    array=re.search(r'int A\[[^\]]+\]\s*=\s*\{([^}]+)\}',body,re.S).group(1)
    values=[int(x.strip()) for x in array.split(',') if x.strip()]
    rows,cols=map(int,re.search(r'mtdev_match\(index, A, (\d+), (\d+)\)',body).groups())
    assert rows==cols and 1<=rows<=5 and len(values)==rows*cols
    block=output.split(name+'\n',1)[1].split(end+'\n',1)[0]
    matches={int(i):int(c) for i,c in re.findall(r'^match\[(\d+)\] = (-?\d+)$',block,re.M)}
    assert set(matches)==set(range(rows)) and set(matches.values())==set(range(cols))
    cost=sum(values[i+rows*matches[i]] for i in range(rows))
    optimum=min(sum(values[i+rows*p[i]] for i in range(rows)) for p in itertools.permutations(range(cols)))
    assert cost==optimum,(name,cost,optimum)
    cases.append({'name':name,'rows':rows,'matching_cost':cost,'independent_exhaustive_optimum':optimum})
Path('/build/test-results.json').write_text(json.dumps({'scope':'Native matching examples with independent exhaustive oracle and actual C capability/frame/invalid-FD APIs; not physical multitouch acceptance',
    'upstream_diagnostic_exit':0,'matching_oracle':cases,'matching_cases':2,'staged_consumer_exit':0,
    'upstream_benchmark':'Original diagnostic also prints timing, not a performance gate or an assertion suite',
    'physical_device_programs':'mtdev-test/mtdev-kernel not executed; no physical device exposed'},indent=2)+'\n')
PY
