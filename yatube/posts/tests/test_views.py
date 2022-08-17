from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from posts.forms import PostForm
from posts.models import Group, Post
from posts.views import POST_QUANTITY

User = get_user_model()


class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # тестовый юзер profile/test-username/
        cls.author = User.objects.create(
            username='test-username',
            email='test-email@test-email.com',
            password='test-password',
        )
        # тестовая группа group/test-slug/
        cls.group = Group.objects.create(
            title='Тестовый заголовок группы',
            slug='test-group-slug',
            description='test-description',
        )
        cls.group2 = Group.objects.create(
            title='Тестовый заголовок группы2',
            slug='test-group-slug2',
            description='test-description2',
        )
        # словарь для тестового поста
        cls.post_data = {
            'text': 'Тестовый пост',
            'group': cls.group,
            'author': cls.author,
        }

        # тестовый пост
        for i in range(0, 10):
            cls.post = Post.objects.create(
                text=cls.post_data['text'],
                group=cls.post_data['group'],
                author=cls.post_data['author'],
            )

    def setUp(self):
        self.user = User.objects.create_user(username='views_user')
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    # Проверяем используемые шаблоны
    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        self.authorized_client = self.client
        self.authorized_client.force_login(self.author)
        # Собираем в словарь пары "имя_html_шаблона: reverse(name)"
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_posts', kwargs={'slug': self.group.slug}):
                'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': self.author.username}):
                        'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}):
                'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}):
                'posts/post_create.html',
            reverse('posts:post_create'): 'posts/post_create.html',
        }
        # Проверяем, что при обращении к name
        # вызывается соответствующий HTML-шаблон
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def service_asserts(self, test_object):
        """Служебные asserts."""
        self.assertEqual(test_object.pk, self.post.pk)
        self.assertEqual(
            test_object.author.username, self.post.author.username)
        self.assertEqual(test_object.group.title, self.group.title)
        self.assertEqual(test_object.text, self.post.text)

    def service_asserts_group(self, test_object):
        """Служебные asserts для тестирования групп."""
        self.assertEqual(test_object.pk, self.group.id)
        self.assertEqual(test_object.slug, self.group.slug)
        self.assertEqual(test_object.title, self.group.title)
        self.assertEqual(
            test_object.description, self.group.description)

    def helper_contexts(self, response, context):
        """Контексты для тестирования."""
        context_detail = {
            context.text: self.post_data['text'],
            context.author.username: self.post_data['author'].username,
            context.group.title: self.post_data['group'].title,
        }

        for context, expected in context_detail.items():
            with self.subTest(response=response, context=context):
                self.assertEqual(context, expected)

    def test_homepage_and_profile_show_correct_posts_contexts(self):
        """View: index получают соответствующий контекст."""
        response = self.authorized_client.get(reverse('posts:index'))
        context = response.context['page_obj'].object_list[0]
        self.assertEqual(context, self.post)
        self.helper_contexts(response, context)
        self.service_asserts(context)

    def test_profile_show_correct_contexts(self):
        """View: profile получает соответствующий контекст."""
        response = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': self.author.username}
            )
        )

        context = response.context['page_obj'].object_list[0]
        self.assertEqual(context, self.post)
        self.helper_contexts(response, context)
        self.service_asserts(context)

        context = response.context['author']
        self.assertEqual(context, self.author)

        context = response.context['posts_count']
        self.assertEqual(context, self.post_data['author'].posts.count())

    def test_group_posts_context(self):
        """View: group_posts имеет соответствующий контекст."""
        response = self.authorized_client.get(
            reverse(
                'posts:group_posts',
                kwargs={'slug': self.group.slug}
            )
        )
        context = response.context['group']
        self.assertEqual(context, self.group)
        self.service_asserts_group(context)

        context = response.context['page_obj'].object_list[0]
        self.assertEqual(context, self.post)
        self.helper_contexts(response, context)
        self.service_asserts(context)

    def test_post_detail_show_correct_context(self):
        """View: post_detail имеет соответствующий контекст."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        context = response.context['post']
        self.assertEqual(context, self.post)
        self.helper_contexts(response, context)

        context = response.context['author']
        self.assertEqual(context, self.author)

        context = response.context['posts_count']
        self.assertEqual(context, self.post_data['author'].posts.count())

    def test_create_post_correct_context(self):
        """
        View: post_create и post_edit имеют соответствующий
        контекст.
        """
        self.authorized_client = self.client
        self.authorized_client.force_login(self.author)

        response_types = [
            self.authorized_client.get(reverse('posts:post_create')),
            self.authorized_client.get(
                reverse('posts:post_edit', kwargs={'post_id': self.post.id})
            ),
        ]

        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }

        for response in response_types:
            if response.resolver_match.func.__name__ == 'post_create':
                print(response.context)
                self.assertNotIn('is_edit', response.context)

            if response.resolver_match.func.__name__ == 'post_edit':
                context = response.context['post']
                self.assertEqual(context, self.post)

                context = response.context['is_edit']
                self.assertTrue(context)

            self.assertIsInstance(
                response.context['form'], PostForm
            )
            for value, values in form_fields.items():
                with self.subTest(value=value):
                    f_field = response.context['form'].fields.get(value)
                    self.assertIsInstance(f_field, values)

    def test_new_post_appearance(self):
        """Проверка появления новой записи на всех страницах."""
        # На главной
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(
            response.context['page_obj'][0], self.post)

        # В группе
        response = self.authorized_client.get(
            reverse('posts:group_posts', kwargs={'slug': self.group.slug})
        )
        self.assertEqual(response.context['page_obj'][0], self.post)

        # В профиле пользователя
        response = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': self.author.username}
            )
        )
        post_in_profile = response.context['page_obj'][0]
        self.assertEqual(post_in_profile, self.post)

        context = {
            response.context['page_obj'][0]: self.post,
            post_in_profile.group: self.group,
        }

        for entity, entities in context.items():
            with self.subTest(element=entity):
                self.assertEqual(entity, entities)

    def test_post_not_found(self):
        """Проверка отсутствия записи не в той группе."""
        response = self.authorized_client.get(
            reverse('posts:group_posts', kwargs={'slug': self.group2.slug})
        )
        context = response.context['page_obj'].object_list
        self.assertNotIn(self.post, context)


class PaginatorViewsTest(TestCase):
    """Тестирование паджинатора."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.post_quantity_second_page = 3
        range_size = POST_QUANTITY + cls.post_quantity_second_page
        cls.posts = []
        cls.author = User.objects.create_user(
            username='paginator_author'
        )
        cls.group = Group.objects.create(
            title='Заголовок для паджинатора',
            slug='paginator_views',
            description='Описание для паджинатора',
        )

        for paginator_post in range(range_size):
            cls.posts.append(
                Post(
                    author=cls.author,
                    group=cls.group,
                    text=f'{paginator_post}',
                )
            )
        Post.objects.bulk_create(cls.posts)

    def setUp(self):
        self.user = User.objects.create_user(
            username='paginator_user'
        )
        self.authorized_client = self.client
        self.authorized_client.force_login(self.user)

    def test_paginator(self):
        self.authorized_client = self.client
        self.authorized_client.force_login(self.author)

        post_quantity_second_page = self.post_quantity_second_page

        response_types = {
            self.authorized_client.get(
                reverse('posts:index')
            ): POST_QUANTITY,
            self.authorized_client.get(
                reverse('posts:index') + '?page=2'
            ): post_quantity_second_page,

            self.authorized_client.get(
                reverse('posts:group_posts', kwargs={'slug': self.group.slug})
            ): POST_QUANTITY,
            self.authorized_client.get(
                reverse('posts:group_posts', kwargs={'slug': self.group.slug})
                + '?page=2'
            ): post_quantity_second_page,

            self.authorized_client.get(
                reverse(
                    'posts:profile',
                    kwargs={'username': self.author.username}
                )
            ): POST_QUANTITY,
            self.authorized_client.get(
                reverse(
                    'posts:profile',
                    kwargs={'username': self.author.username}
                )
                + '?page=2'
            ): post_quantity_second_page,
        }

        for response, quantity in response_types.items():
            self.assertEqual(len(response.context['page_obj']), quantity)
