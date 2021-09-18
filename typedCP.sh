#!/bin/bash

src=$1
dst=$2

exit

xclip -sel c < ${src}
sleep 0.1 && xdotool type "i" && xdotool type "$(xclip -o -selection clipboard)" && xdotool key Escape && xdotool type ":wq" && xdotool key Return &
vi ${dst}
