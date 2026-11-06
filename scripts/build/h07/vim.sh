#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ -f /var/log/toddy/build/h07-vim-glvs-inputs.success.json ]] || exit 1
cd "$LFS/sources"
python3 "$SOURCE_TOOL" vim-9.2.1201.tar.gz
chroot_run < /opt/toddy-build/scripts/build/h07/vim-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py vim 9.2.1201-1 \
 "$LFS/sources/stage/vim" --depends 'glibc (>= 2.44-1), ncurses' --source vim-9.2.1201.tar.gz \
 --conffile /etc/vimrc --recipe /opt/toddy-build/scripts/build/h07/vim.sh --install
