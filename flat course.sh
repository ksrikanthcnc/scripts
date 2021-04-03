#!/bin/bash
echo "doing nothing exiting";exit
target=$(basename $1)
mkdir "${target}-new"
for sub in "$target/"*;do
	for subsub in "$sub/"*;do
		for file in "$subsub/"*;do
				if [ ${file: -4} == ".srt" -o ${file: -4} == ".mp4" ]
				then
					echo $(echo ${sub##*/}|cut -d'_' -f 1)_$(echo ${subsub##*/}|cut -d'_' -f 1)_${file##*/}
 					cp -u "$file" "${target}-new"/$(echo ${sub##*/}|cut -d'_' -f 1)_$(echo ${subsub##*/}|cut -d'_' -f 1)_${file##*/}
				fi
		done
	done
done