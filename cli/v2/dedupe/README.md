Context 
there are old files in source folder on windows, some files are duplicated by mistake.

Goal
copy all files to target folder and keep only 1 copy for duplicate files, do not touch original files.

Task 
generate python script to find such files and group such file paths in json, default to dryrun=true, when dryrun=false copy to target folder.
use good hash function at least as good as sha256 to avoid false positive, compare file byte by byte when hash collision happens to make sure they are truly identical.
use typer to create cli script, use rich to provide visual progress, add logging also.
make script performant where possible.
save intermediate files if necessary to make future rerun faster.
feel free to add other suggestions.
in json output, add summary of how many duplicate files are found, the total size of the duplicates, how many files will be copied to target folder, total size of files to be copied to target folder.

python script.py "C:\Backup\Allphotos" "C:\Backup\deduped" --output-json duplicates.json --log-level INFO

python script.py "C:\Backup\Allphotos" "C:\Backup\deduped" --output-json duplicates.json --no-dryrun --log-level INFO
