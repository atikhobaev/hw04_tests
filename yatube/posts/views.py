from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect


from .models import Post, Group
from .forms import PostForm

POST_QUANTITY = 10


def index(request):
    """Главная страница с постами."""
    # использовал django-querycount из статьи
    # https://www.tutorialspoint.com/django-query-count-in-terminal-for-debugging
    # 1) Изначально было 31 запрос
    # Post.objects.all()
    # 2) Потом стало 21
    # Post.objects.select_related('author').all()
    # 3) Сейчас осталось 14
    # Total queries: 14 in 0.0095s
    # Ради интереса отключил вывод постов через шаблон показало 3 запроса
    # Total queries: 3 in 0.0038s
    # Если я открываю страницу с одним постом post_detail
    # Total queries: 7 in 0.0047s
    #
    # Итого:
    # Как я понял 3 запроса делает джанга обсолютно в любом случае
    # Если мы показываем одну страницу
    # через get_object_or_404(Post, pk=post_id) запросов  становится 7
    # Если я включаю отображение постов методе index
    # к трём запросам добавляется 11 запросов
    # Не знаю какие выводы из этого делать xD мыслать зашла в тупик
    posts = Post.objects.select_related('author').select_related('group').all()
    paginator = Paginator(posts, POST_QUANTITY)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
    }

    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    """Страница группы с постами."""
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, POST_QUANTITY)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """Страница с постами автора."""
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    paginator = Paginator(posts, POST_QUANTITY)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'author': author,
        'page_obj': page_obj,
        'posts_count': author.posts.count(),
    }

    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """Страница одного поста."""
    post = get_object_or_404(Post, pk=post_id)

    context = {
        'post': post,
        'author': post.author,
        'posts_count': post.author.posts.count(),
    }

    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """Создать новый пост."""
    form = PostForm(
        request.POST or None,
    )

    if form.is_valid():
        post = form.save(False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', request.user.username)

    context = {
        'form': form,
    }

    return render(request, 'posts/post_create.html', context)


@login_required
def post_edit(request, post_id):
    """Отредактировать пост."""
    post = get_object_or_404(Post, pk=post_id)
    form = PostForm(
        request.POST or None,
        instance=post,
    )

    if not request.user == post.author:
        return redirect('posts:post_detail', post_id=post_id)

    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)

    context = {
        'post': post,
        'form': form,
        'is_edit': True,
    }
    return render(request, 'posts/post_create.html', context)
