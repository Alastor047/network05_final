from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post

User = get_user_model()


class PaginatorViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testname')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Описание группы растянутое на много знаков',
        )
        cls.posts = []
        for i in range(0, 13):
            cls.posts.append(Post.objects.create(
                text=f'Рандомный текст{i}',
                author=cls.user,
                group=cls.group,
            ))

    def setUp(self):
        self.guest_client = Client()

    def test_first_page_contains_ten_records(self):
        """Проверка паджинатора 10 постов страница 1."""
        pages = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile',
                    kwargs={'username': self.user.username}
                    )
        ]
        for page in pages:
            with self.subTest(page=page):
                response = self.guest_client.get(page)
                self.assertEqual(len(response.context.get('page_obj')), 10)

    def test_last_page_contains_three_records(self):
        """Проверка паджинатора 3 поста страница 2."""
        pages = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile',
                    kwargs={'username': self.user.username}
                    )
        ]
        for page in pages:
            with self.subTest(page=page):
                response = self.guest_client.get(page + '?page=2')
                self.assertEqual(len(response.context.get('page_obj')), 3)
