# from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post
from posts.forms import PostForm

User = get_user_model()


class PostsFormsTests(TestCase):
    """Тестирование формы поста."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.form = PostForm()
        cls.user = User.objects.create_user(username='test-username')

        cls.group = Group.objects.create(
            title='Тестовый заголовок группы',
            slug='test-group-slug',
            description='test-description',
        )
        cls.group2 = Group.objects.create(
            title='Тестовый заголовок группы',
            slug='test-group2-slug',
            description='test-description',
        )

        cls.post = Post.objects.create(
            group=cls.group,
            author=cls.user,
            text='Текст формы')

        cls.form_data = {
            'group': cls.group.id,
            'text': cls.post.text,
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = self.client
        self.authorized_client.force_login(self.user)

    def test_create_new_post(self):
        """Тестирование создания новой записи."""
        count_posts = Post.objects.count()

        context = {
            'group': self.group.id,
            'text': 'Какой-то текст 1',
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'), data=context, follow=False)

        self.assertEqual(
            Post.objects.latest('id').text, context['text'])

        self.assertEqual(
            Post.objects.latest('id').group_id, context['group'])

        self.assertRedirects(
            response,
            reverse('posts:profile', args=[self.user]))

        self.assertEqual(Post.objects.count(), count_posts + 1)

    def test_editing_post(self):
        """Тестирование редактирования записи."""
        count_posts = Post.objects.count()
        latest_post_id = Post.objects.latest('id').id
        context = {
            'group': self.group2.id,
            'text': 'Какой-то текст 2',
        }
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': latest_post_id}),
            data=context, follow=True)

        self.assertRedirects(
            response, reverse(
                'posts:post_detail',
                kwargs={'post_id': latest_post_id}
            ))

        self.assertEqual(Post.objects.count(), count_posts)

        self.assertTrue(Post.objects.filter(
            id=latest_post_id, text=context['text'],
            group=context['group']).exists())

    def test_guest_client_cannot_create_post(self):
        """Тестирование невозможности создания записи без
        регистрации.
        """
        post_count = Post.objects.count()

        response = self.guest_client.post(
            reverse('posts:post_create'),
            data={'group': 1, 'text': "Guest post"},
            follow=False)

        self.assertRedirects(
            response, '%s?next=/create/' % reverse('login')
        )

        self.assertEqual(Post.objects.count(), post_count)

    def test_fail_to_edit_other_person_post(self):
        """Тестирование невозможности редактировать чужие записи."""
        edited_post_before = 'Исправленный текст'
        response = self.guest_client.post(
            reverse('posts:post_edit', args=[self.post.pk]),
            data={'text': edited_post_before},
        )
        edited_post_after = get_object_or_404(Post, pk=self.post.pk).text
        self.assertNotEqual(edited_post_after, edited_post_before)
        self.assertRedirects(
            response, (
                f'/auth/login/?next=/posts/{self.post.pk}/edit/')
        )

    def test_post_help_text(self):
        """
        Тестирование text_field и group_field.
        """
        response = PostsFormsTests.post
        fields_help_texts = {
            'group': 'Группа, к которой будет относиться пост',
            'text': 'Текст нового поста',
        }

        for field, fields in fields_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    response._meta.get_field(field).help_text, fields
                )
