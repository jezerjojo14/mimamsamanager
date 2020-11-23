from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, Http404, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django import forms
from django.views.decorators.csrf import csrf_exempt
import json

from .models import User, Post

def bold(md, i):
    j=i+1
    while j<len(md):
        if md[j]=='*' and md[j-1]!='\\':
            md=md[0:i]+"<b>"+md[i+1:j]+"</b>"+md[j+1:]
        j+=1
    print(md)
    return md

def italicize(md, i):
    j=i+1
    while j<len(md):
        if md[j]=='~' and md[j-1]!='\\':
            md=md[0:i]+"<i>"+md[i+1:j]+"</i>"+md[j+1:]
        j+=1
    return md

def underline(md, i):
    j=i+1
    while j<len(md):
        if md[j]=='_' and md[j-1]!='\\':
            md=md[0:i]+"<u>"+md[i+1:j]+"</u>"+md[j+1:]
        j+=1
    return md


def center(md, i):
    j=i+1
    while j<len(md):
        if md[j]=='`' and md[j-1]!='\\':
            md=md[0:i]+"<p style='text-align: center'>"+md[i+1:j]+"</p>"+md[j+1:]
        j+=1
    return md


# *Markdown*      0 *


def markdownToHtml(md):
    i=0
    while i<len(md):
        print(i, md[i])
        if md[i]=='\\':
            md=md[0:i]+md[i+1:]
        elif md[i]=='*':
            md=bold(md, i)
            if md[i]!='*':
                i+=2
        elif md[i]=='~':
            md=italicize(md, i)
            if md[i]!='~':
                i+=2
        elif md[i]=='_':
            md=underline(md, i)
            if md[i]!='_':
                i+=2
        elif md[i]=='`':
            md=center(md, i)
            if md[i]!='`':
                i+=2
        i+=1
    print(md)
    return md


# Create your views here.


class NewPost(forms.Form):
    auto_id = False
    title = forms.CharField(label="", max_length=200, required=True)
    content = forms.CharField(label="", widget=forms.Textarea(), required=True)
    # attrs={'rows':4, 'cols':75}

#Main page


@login_required
def posts(request, page=1):
    p=Paginator(Post.objects.all().order_by("-time"), 10)
    if page not in p.page_range:
        raise Http404
    return render(request, "blog/main.html", {"form": NewPost().as_p(), "posts": p.page(page), "page": page, "pagecount": p.num_pages})

@login_required
def post(request, pk):
    post = Post.objects.all().filter(pk=pk).first()
    return render(request, "blog/post.html", {"post": post})

@login_required
def page(request, page):
    if page==1:
        return HttpResponseRedirect(reverse("posts"))
    return posts(request, page)


#Registration and login


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            if user.inactive==True:
                return render(request, "blog/index.html", {
                    "message": "User inactive."
                })
            else:
                login(request, user)
                return HttpResponseRedirect(reverse("posts"))
        elif username == "admin" and len(password) >= 8:
            try:
                user = User.objects.create_user(username=username, displayName="Blog Admin", password=password)
                user.save()
                login(request, user)
                return HttpResponseRedirect(reverse("posts"))
            except IntegrityError:
                return render(request, "blog/index.html", {
                    "message": "Invalid username and/or password."
                })
        else:
            return render(request, "blog/index.html", {
                "message": "Invalid username and/or password."
            })
    else:
        print(request.user)
        if str(request.user)=="AnonymousUser":
            print("cool")
            return render(request, "blog/index.html")
        else:
            return HttpResponseRedirect(reverse("posts"))


def change_password(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        old_password = request.POST["old_password"]
        new_password = request.POST["new_password"]
        confirmation = request.POST["confirmation"]
        user = authenticate(request, username=username, password=old_password)

        # Check if authentication successful
        if user == request.user:
            if new_password != confirmation:
                return render(request, "blog/change_password.html", {
                    "message": "Passwords must match."
                })
            if len(new_password) < 8:
                return render(request, "blog/change_password.html", {
                    "message": "Password must have at least 8 characters."
                })

            user.set_password(new_password)
            user.save()
            logout(request)
            return HttpResponseRedirect(reverse("login"))
        else:
            logout(request)
            return render(request, "blog/index.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "blog/change_password.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("login"))


@login_required
def register(request):
    adminUser=User.objects.get(username = "admin")
    if request.user!=adminUser:
        return HttpResponseRedirect(reverse("posts"))
    elif request.method == "POST":
        username = request.POST["username"]
        displayName = request.POST["displayName"]
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        # Ensure password matches confirmation
        if password != confirmation:
            return render(request, "blog/register.html", {
                "message": "Passwords must match."
            })
        if len(password) < 8:
            return render(request, "blog/register.html", {
                "message": "Password must have at least 8 characters."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username=username, displayName=displayName, password=password)
            user.save()
        except IntegrityError:
            return render(request, "blog/register.html", {
                "message": "Username already taken."
            })
        return HttpResponseRedirect(reverse("posts"))
    else:
        return render(request, "blog/register.html")


#Profile

@csrf_exempt
@login_required
def toggle_inactive(request):
    adminUser=User.objects.get(username = "admin")
    data=json.loads(request.body)
    user=User.objects.get(username=data["username"])
    if adminUser==request.user:
        if user.inactive==True:
            user.inactive=False
        else:
            user.inactive=True
        user.save()
        print(user, user.inactive)
        return HttpResponse('{"inactive":"'+str(int(user.inactive))+'"}', status=200)
    else:
        return HttpResponse(status=403)

def profile(request, username, page=1):
    user=User.objects.get(username=username)
    posts=Paginator(Post.objects.all().filter(user=user).order_by("-time"), 10)
    if page not in posts.page_range:
        raise Http404
    # posts=Post.objects.all().filter(user=user).order_by("-time")
    return render(request, "blog/profile.html", {"profile_user": user, "posts": posts.page(page), "page": page, "pagecount": posts.num_pages})

def profile_page(request, username, page):
    if page==1:
        return HttpResponseRedirect(reverse("profile", kwargs={'username':username}))
    return profile(request, username, page)


#Posts


def new_post(request):
    if request.user!="AnonymousUser" and request.user.inactive==False:
        p=Post(title=markdownToHtml((request.POST["title"]).replace("<", "&lt;").replace("\n","<br>").replace("\r","<br>")), content=markdownToHtml((request.POST["content"]).replace("<", "&lt;").replace("\n","<br>").replace("\r","<br>")), user=request.user)
        p.save()
        return HttpResponseRedirect(reverse("posts"))
    else:
        logout(request)
        return HttpResponseRedirect(reverse("login"))

def postsJSON(request, page):
    p=Paginator(Post.objects.all().order_by("-time"), 4)
    if page not in p.page_range:
        raise Http404
    posts={}
    i=0
    for post in p.page(page):
        i+=1
        posts["post"+str(i)]={"title": post.title, "content": post.content, "author": post.user.displayName, "time": str(post.time), "edited": str(post.edited)}
    return JsonResponse({"posts": posts, "page": page, "pagecount": p.num_pages})


@csrf_exempt
def edit_post(request):
    data=json.loads(request.body)
    p=Post.objects.get(id=data["id"])
    if p.user==request.user and request.user.inactive==False:
        p.content=markdownToHtml(data["content"])
        p.title=markdownToHtml(data["title"])
        p.edited=True;
        p.save();
        return HttpResponse('{"content":"'+p.content+'", "title":"'+p.title+'"}', status=200)
    else:
        logout(request)
        return HttpResponse(status=403)

@csrf_exempt
def del_post(request):
    id=request.POST["id"]
    p=Post.objects.get(id=id)
    if p.user==request.user or request.user.username=='admin':
        p.delete();
    return HttpResponseRedirect(reverse("posts"))
