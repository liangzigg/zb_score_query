
from pymongo import MongoClient
#
# key = 'u1509044144'
# client = MongoClient()
#
# jg = list(client.jg[key].find({"类型": {"$regex": '学期.*'}}))
# print(list(jg))
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "score_analysis.settings")
django.setup()

from pymongo import MongoClient
#
# from student.models import User
#
# user = User.objects.create(username='1509044144', password='wxl910', mg_key='u1509044144')
#
# print(user.password)
# print(user.mg_key)

conn = MongoClient()
result = conn.jg.u1509044144.aggregate([{'$group': {'_id': '$学期'}}])
print(list(result))
