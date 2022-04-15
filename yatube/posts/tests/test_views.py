import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post, Follow

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPageTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testname')
        cls.user2 = User.objects.create_user(username='testname2')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Описание группы растянутое на много знаков',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.image = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=cls.image,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(PostPageTests.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}
                    ): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': self.user.username}
                    ): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id}
                    ): 'posts/post_detail.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.id}
                    ): 'posts/post_create.html',
            reverse('posts:post_create'): 'posts/post_create.html',
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.author_client.get(reverse_name)
                self.assertTemplateUsed(response, template, 'Не верный тест!')

    def test_post_context_index(self):
        """Проверка контекста домашней страницы index"""
        response = self.author_client.get(reverse('posts:index'))
        first_object = response.context.get('page_obj')[0]
        self.assertEqual(
            first_object.group.title, self.post.group.title, 'Ошибка Title'
        )
        self.assertEqual(first_object.text, self.post.text, 'Ошибка Text')
        self.assertEqual(
            first_object.pub_date, self.post.pub_date, 'Ошибка Date'
        )
        self.assertEqual(
            first_object.author, self.post.author, 'Ошибка Author'
        )
        self.assertEqual(first_object.image, self.post.image, 'Ошибка image')

    def test_context_post_create(self):
        """Проверка контекста для post_create."""
        response = self.author_client.get(reverse('posts:post_create'))
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_context_post_edit(self):
        """Проверка контекста для post_edit."""
        response = self.author_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id},
            ))
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_group_contains_list_of_posts(self):
        """Проверка что group_list содержит посты,
        отфильтрованные по группе."""
        response = self.author_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug},
            ))
        for post_example in response.context.get('page_obj').object_list:
            with self.subTest():
                self.assertIsInstance(post_example, Post)
                self.assertEqual(post_example.group, self.group)

    def test_profile_contains_list_of_posts(self):
        """Проверка что profile содержит посты,
        отфильтрованные по пользователю."""
        response = self.author_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            ))
        for post_example in response.context.get('page_obj').object_list:
            with self.subTest():
                self.assertIsInstance(post_example, Post)
                self.assertEqual(post_example.author, self.user)

    def test_post_image_profile(self):
        """Проверка картинки profile."""
        response = self.author_client.get(
            reverse(
                'posts:profile', kwargs={'username': self.user.username}
            ))
        first_object = response.context.get('page_obj')[0]
        self.assertEqual(first_object.image, self.post.image, 'Ошибка image')

    def test_post_image_group_list(self):
        """Проверка картинки group_list"""
        response = self.author_client.get(
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ))
        first_object = response.context.get('page_obj')[0]
        self.assertEqual(first_object.image, self.post.image, 'Ошибка image')

    def test_post_image_post_detail(self):
        """Проверка картинки post_detail"""
        response = self.author_client.get(
            reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}
            ))
        first_object = response.context.get('post')
        self.assertEqual(first_object.image, self.post.image, 'Ошибка image')

    def test_cache_index(self):
        """Проверка работы кэша на главной."""
        self.post = Post.objects.create(
            author=self.user,
            text='test-post',
            group=self.group,
        )
        response = self.author_client.get(
            reverse('posts:index')
        )
        before_delete = response.content
        delete_post = Post.objects.get(id=self.post.id)
        delete_post.delete()
        after_delet = response.content
        self.assertEqual(after_delet, before_delete)
        cache.delete('index_page')
        self.assertEqual(after_delet, before_delete)

    def test_follow_for_auth(self):
        """Проверяем функцию подписки"""
        follow_count = Follow.objects.count()
        Follow.objects.create(
            user=self.user,
            author=self.user2
        )
        self.author_client.post(reverse(
            'posts:profile_follow', kwargs={'username': self.user2}))
        self.assertTrue(Follow.objects.filter(
            user=self.user, author=self.user2).exists()
        )
        self.assertEqual(Follow.objects.count(), follow_count + 1)

    def test_unfollow_for_auth(self):
        """Проверяем функцию отписки"""
        Follow.objects.create(
            user=self.user,
            author=self.user2
        )
        follow_count = Follow.objects.count()
        self.author_client.post(reverse(
            'posts:profile_unfollow', kwargs={'username': self.user2}))
        self.assertFalse(Follow.objects.filter(
            user=self.user, author=self.user2).exists()
        )
        self.assertEqual(Follow.objects.count(), follow_count - 1)
