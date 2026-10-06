_ogr()
{
    local current previous
    COMPREPLY=()
    current=${COMP_WORDS[COMP_CWORD]}
    previous=${COMP_WORDS[COMP_CWORD-1]}

    if [[ $previous == -r || $previous == --remote ]]; then
        while IFS= read -r remote; do
            [[ $remote == "$current"* ]] && COMPREPLY+=("$remote")
        done < <(git -C . remote 2>/dev/null)
        return
    fi

    if [[ $current == -* ]]; then
        while IFS= read -r option; do
            COMPREPLY+=("$option")
        done < <(compgen -W '-b --branch -r --remote -p --print -h --help -V --version' -- "$current")
        return
    fi

    while IFS= read -r directory; do
        COMPREPLY+=("$directory/")
    done < <(compgen -d -- "$current")
}
complete -o nospace -F _ogr ogr
