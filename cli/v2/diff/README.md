Context 
there are 2 folders, each containing a lot of files, some of the files are duplicates

Goal
compare these 2 folders and find out different unique files within each folder, you can use hash function but need to compare files byte by byte to confirm exact match

Task 
generate list of files that only exists in these 2 folders
do not delete/modify any file
be performant

python script.py C:\Backup\deduped C:\Backup\final -o results.json -v

