from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect

def index(request):
    return render_to_response('trend/index.html')

def create_new_user(request):
    form = UserCreationForm()
    # if form was submitted, bind form instance.
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # user must be active for login to work
            user.is_active = True
            user.put()
            return HttpResponseRedirect('/trend/login/')
    return render_to_response('trend/user_create_form.html', {'form': form})