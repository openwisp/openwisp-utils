from django.shortcuts import render


def non_admin_view(request):
    # To test menu on non admin page
    return render(request, 'test_project/non_admin_test.html')
