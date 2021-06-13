from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User

RECORD_COUNT = 10


def get_page_numbers(request, filter):
    paginator = Paginator(filter, RECORD_COUNT)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def get_subscriptions_count(request, author):
    subscriptions_count = author.follower.count()
    signed_count = author.following.count()
    if request.user.is_authenticated:
        following = Follow.objects.filter(user=request.user,
                                          author=author).exists()
    else:
        following = False
    return subscriptions_count, signed_count, following


@cache_page(20, key_prefix="index_page")
def index(request):
    post_list = Post.objects.all().order_by('-pub_date')
    page = get_page_numbers(request, post_list)
    return render(request, "index.html", {"page": page})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    page = get_page_numbers(request, post_list)
    return render(request,
                  "group.html",
                  {"group": group, "page": page})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    author_posts = author.posts.all()
    post_count = author_posts.count()
    (subscriptions_count, signed_count,
        following) = get_subscriptions_count(request, author)
    page = get_page_numbers(request, author_posts)
    return render(request, 'profile.html',
                           {"author": author,
                            "author_posts": author_posts,
                            "post_count": post_count,
                            "subscriptions_count": subscriptions_count,
                            "signed_count": signed_count,
                            "following": following,
                            "page": page
                            })


def post_view(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    post_count = post.author.posts.count()
    comments = post.comments.all()
    (subscriptions_count, signed_count,
        following) = get_subscriptions_count(request, post.author)
    form = CommentForm()
    return render(request, 'post.html',
                  {"author": post.author,
                   "post": post,
                   "post_count": post_count,
                   'form': form,
                   "comments": comments,
                   "subscriptions_count": subscriptions_count,
                   "signed_count": signed_count,
                   "following": following,
                   })


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('index')
        return render(request, 'new_post.html', {'form': form})
    return render(request, 'new_post.html', {'form': form})


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    if request.user != post.author:
        return redirect('post',
                        username=post.author.username,
                        post_id=post.id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if request.method == 'POST':
        if form.is_valid():
            form.save()
        return redirect('post',
                        username=post.author.username,
                        post_id=post.id)
    return render(request,
                  'new_post.html', {'form': form, 'post': post, 'edit': True})


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    form = CommentForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
        return redirect('post', username, post_id)
    return render(request, 'comments.html', {'form': form, 'post': post})


@login_required
def follow_index(request):
    following_posts = Post.objects.filter(
        author__following__user=request.user
    ).select_related('author')
    page = get_page_numbers(request, following_posts)
    return render(request, 'follow.html', {'page': page})


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    follower = Follow.objects.filter(user=request.user, author=author).exists()
    if not follower and request.user != author:
        Follow.objects.create(user=request.user, author=author)
        return redirect('follow_index')
    return redirect('index')


@login_required
def profile_unfollow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    unfollow = Follow.objects.get(user_id=user.pk, author_id=author.pk)
    unfollow.delete()
    return redirect('follow_index')


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)
