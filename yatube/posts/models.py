from django.contrib.auth import get_user_model
from django.db import models

from core.models import CreatedModel

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'


class Post(CreatedModel):
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='posts_group',
        help_text='Группа к которой будет относиться пост',
        verbose_name='Группа',
    )
    text = models.TextField(
        verbose_name='text',
        help_text='Текст нового поста'
    )
    pub_date = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='posts',
        verbose_name='Автор',
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    def __str__(self):
        return self.text

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'


class Comment(models.Model):
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        related_name='comments',
        on_delete=models.CASCADE,
    )
    text = models.TextField(
        verbose_name='Комментарий',
        help_text='Текст комментария'
    )
    created = models.DateTimeField(
        'Отправлено в:',
        auto_now_add=True,
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments'
    )

    def __str__(self):
        return self.text

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        related_name='follower',
        verbose_name='Подписчик',
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        User,
        related_name='following',
        verbose_name='Автор',
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                name="%(app_label)s_%(class)s_name_unique",
                fields=['author'],
            ),
        ]
