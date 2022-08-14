from django.test import TestCase, Client
from http import HTTPStatus

from posts.models import Group, Post, User


class PostURLTests(TestCase):
    # Создадим записи в тестовой БД
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
            title='Тестовый заголовок',
            slug='test-slug',
            description='test-description',
        )

        # тестовый пост post/test-slug/
        cls.post = Post.objects.create(
            id=333,
            group=cls.group,
            author=cls.author,
            text='Тестовый текст',
        )

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованый клиент
        self.user = User.objects.create_user(username='SemenUrlTester')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    # Проверяем общедоступные страницы
    def test_url_homepage(self):
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_group(self):
        """Проверка /group/test-slug/."""
        response = self.guest_client.get('/group/test-slug/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_profile_guest(self):
        """Проверка /profile/test-username/."""
        response = self.guest_client.get('/profile/test-username/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_post(self):
        """Проверка /posts/333/."""
        response = self.guest_client.get('/posts/333/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_post_edit_guest_redirect(self):
        """Проверка /posts/333/edit для гостя."""
        response = self.guest_client.get('/posts/333/edit')
        self.assertEqual(response.status_code, HTTPStatus.MOVED_PERMANENTLY)

    def test_url_create_guest_redirect(self):
        """Редирект /create/ для гостя."""
        response = self.guest_client.post('/create/')
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_url_404(self):
        """Проверка на 404 ошибку /some-trash-link/."""
        response = self.guest_client.get('/some-trash-link/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    # Проверяем доступность страниц для авторизованного пользователя
    def test_url_post_edit_author(self):
        """Проверка /posts/333/edit для автора."""
        response = self.authorized_client.get('/posts/333/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_url_create_user(self):
        """Редирект /create/ для юзера."""
        response = self.authorized_client.post('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    # Проверка вызываемых шаблонов для каждого адреса
    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/group/test-slug/': 'posts/group_list.html',
            '/create/': 'posts/post_create.html',
            '/posts/333/': 'posts/post_detail.html',
            '/profile/test-username/': 'posts/profile.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
