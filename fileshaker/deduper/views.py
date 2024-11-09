from django.shortcuts import render
from .utils import find_duplicates

# Create your views here.
def scan_directory_view(request):
    duplicates = None
    if request.method == 'POST':
        directory = request.POST.get('directory_path')
        if directory:
            duplicates = find_duplicates(directory)
    
    return render(request, 'deduper/scan_results.html', {'duplicates': duplicates})


