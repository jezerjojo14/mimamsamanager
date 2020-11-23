
from django.urls import path

from . import views

urlpatterns = [
    path("postsJSON/<int:page>", views.postsJSON, name="postsJSON"),
    path("changepassword", views.change_password, name="change_password"),
    path("posts", views.posts, name="posts"),
    path("post/<int:pk>", views.post, name="post"),
    path("posts/<int:page>", views.page, name="page"),
    path("user/<str:username>/<int:page>", views.profile_page, name="profile_page"),
    path("user/<str:username>", views.profile, name="profile"),
    path("", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("newpost", views.new_post, name="new_post"),
    path("edit", views.edit_post, name="edit_post"),
    path("delete", views.del_post, name="delete"),
    path("toggle_inactive", views.toggle_inactive, name="toggle_inactive")
]
