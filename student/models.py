from django.db import models

from werkzeug.security import generate_password_hash, check_password_hash


class User(models.Model):
    username = models.CharField(max_length=11, verbose_name='用户名', unique=True)
    _password = models.CharField(max_length=128, verbose_name='密码')
    mg_key = models.CharField(max_length=12, verbose_name='数据键')

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, pwd):
        self._password = generate_password_hash(pwd)

    def check_password(self, pwd):
        return check_password_hash(self._password, pwd)

    def __str__(self):
        return self.username

    class Meta:
        db_table = 'user'
