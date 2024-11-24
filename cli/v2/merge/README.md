Context 
there are 2 folders, each folder contain duplicates within themselves, these 2 folders might have same files too.

Goal
collect unique files in these 2 folders, copy to specified target folder, within the target folder, follow these rules 
1. for all image files known to man kind (including proprietary format HEIC .etc) extract their creation time from metadata and put them in folder named in format year-month-day if available, otherwise use file use their file creation time to determine the folder they go to
2. for all audio files known to man kind do the same as 1. 
3. for all video files known to man kind do the same as 1. 
4. for all other files, use their file creation time to determine the folder they go to  
5. remove all apple specific files .DS_Store

make sure all unique files are copied 

Task 
generate python script for this task 
you can use hash for performance but for potential duplicate, use byte by byte comparison for sure 
use rick to generate visual progress indication
generate json file to include which file was copied where 
generate number of files copied and their total size

Feel free to ask me anything

python script.py C:\Backup\Allphotos C:\Backup\final C:\Backup\merged

python script.py C:\Backup\Allphotos C:\Backup\final D:\merged
