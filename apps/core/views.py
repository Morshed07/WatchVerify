from django.shortcuts import render

# Create your views here.


def PrivacyPolicyView(request):
    return render(request, 'privacy_and_policy/privacy_and_policy.html')
