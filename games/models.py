from django.db import models
from django.conf import settings

# Create your models here.
class Game(models.Model):
    steam_appid = models.IntegerField(unique=True, null=True) # 스팀 연동용
    title = models.CharField(max_length=200)
    genre = models.CharField(max_length=100)
    image_url = models.URLField()
    # IGDB 등에서 가져온 메타데이터 저장

class Rating(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    score = models.FloatField() # 1.0 ~ 5.0
    playtime_forever = models.IntegerField(default=0) # 스팀에서 가져온 플레이 타임 (분)

    class Meta:
        unique_together = ('user', 'game') # 한 유저는 한 게임에 하나의 평가만
