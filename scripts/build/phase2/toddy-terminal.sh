# SPDX-License-Identifier: MIT
# Lightweight Bash defaults. Source this file from an interactive user's .bashrc.
case $- in *i*) ;; *) return 0 ;; esac
[ -n "${BASH_VERSION-}" ] || return 0
[ "${TODDY_TERMINAL_PROMPT-1}" != 0 ] || return 0
[[ ${PS1@a} != *r* ]] || return 0
# Preserve an existing custom prompt and every prompt hook/shell setting.
case ${PS1-} in
    ''|'\s-\v\$ ')
        case ${TERM-}:${COLORTERM-} in
            dumb:*|:*) PS1='\u@\h \w \$ ' ;;
            *:truecolor|*:24bit)
                PS1='\[\e[38;2;69;121;166m\]\u@\h\[\e[0m\] \w \$ ' ;;
            *) PS1='\u@\h \w \$ ' ;;
        esac
        ;;
esac
