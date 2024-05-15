# echo "[\e[1;32m NTFY \e[0m] *** Sending message: [$1]"
echo "[ NTFY ] *** Sending message: [$1]"
curl -d "$1 😀" localhost/horse
