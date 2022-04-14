import datetime

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpRequest
from django.shortcuts import get_object_or_404, redirect, render

from posts.forms import CommentForm, PostForm
from posts.models import Follow, Group, Post, User

ORDER_SORT = 10


def index(request: HttpRequest) -> HttpRequest:
    """View функция главной страницы."""
    posts = Post.objects.select_related('group')
    paginator = Paginator(posts, ORDER_SORT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    title = 'Последние обновления на сайте'
    context = {
        'page_obj': page_obj,
        'posts': posts,
        'title': title,
    }
    template = 'posts/index.html'
    return render(request, template, context)


def group_posts(request: HttpRequest, slug: str) -> HttpRequest:
    """View функция для страницы с постами по группам."""
    group = get_object_or_404(Group, slug=slug)
    posts = Post.objects.filter(group=group)
    paginator = Paginator(posts, ORDER_SORT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    title = 'Лев Толстой – зеркало русской революции.'
    context = {
        'title': title,
        'group': group,
        'posts': posts,
        'page_obj': page_obj,
    }
    template = 'posts/group_list.html'
    return render(request, template, context)


def profile(request: HttpRequest, username: str) -> HttpRequest:
    """View функция для страницы профиля пользователя."""
    author = get_object_or_404(User, username=username)
    user = request.user
    following = False
    posts = author.posts.all()
    posts_count = author.posts.count()
    paginator = Paginator(posts, ORDER_SORT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    if user.is_authenticated:
        if Follow.objects.filter(user=user, author=author):
            following = True
    context = {
        'author': author,
        'posts_count': posts_count,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request: HttpRequest, post_id: int) -> HttpRequest:
    """View функция для страницы отдельного поста пользователя."""
    post = get_object_or_404(Post, id=post_id)
    group = post.group
    author = post.author
    posts_count = author.posts.count()
    comments = post.comments.select_related('author')
    form = CommentForm()
    context = {
        'post': post,
        'group': group,
        'posts_count': posts_count,
        'comments': comments,
        'form': form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """View функция создания нового поста."""
    template = 'posts/post_create.html'
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.pub_date = datetime
        post.save()
        return redirect('posts:profile', request.user)
    return render(request, template, {'form': form})


@login_required
def post_edit(request, post_id):
    """View функция редактирования поста."""
    template = 'posts/post_create.html'
    post = get_object_or_404(Post, id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    if not form.is_valid():
        return render(request, template, {'form': form})
    form.save()
    return redirect('posts:post_detail', post_id)


@login_required
def add_comment(request, post_id):
    """View функция добавления комментария."""
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    """View функция страницы подписок."""
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, ORDER_SORT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """View функция кнопки подписаться."""
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    """View функция кнопки отписаться."""
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(
        user=request.user,
        author=author
    )
    follow.delete()
    return redirect('posts:profile', username=author)
