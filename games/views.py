from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Game, Rating

@login_required
def game_detail(request, game_id):
    # steam_appid를 기준으로 게임을 찾거나, id를 기준으로 찾도록 수정 가능
    # 현재 모델 구조상 steam_appid가 unique하므로 이를 사용할 수도 있지만, 
    # urls.py에서 <int:game_id>로 넘겨준다면 pk(id)를 사용하는 것이 일반적입니다.
    # 여기서는 편의상 steam_appid를 game_id로 가정하고 처리하거나, 
    # 실제 DB의 id를 사용할지 결정해야 합니다. 
    # users/views.py에서 steam_appid를 game_id로 매핑해서 보내고 있으므로,
    # 여기서도 steam_appid로 조회하는 것이 맞습니다.
    
    game = get_object_or_404(Game, steam_appid=game_id)
    
    # 리뷰 작성/수정
    if request.method == 'POST':
        score = request.POST.get('score')
        content = request.POST.get('content')
        
        if score:
            rating, created = Rating.objects.update_or_create(
                user=request.user,
                game=game,
                defaults={
                    'score': float(score),
                    'content': content
                }
            )
            return redirect('games:detail', game_id=game_id)

    # 리뷰 목록 가져오기
    reviews = Rating.objects.filter(game=game).select_related('user').order_by('-updated_at')
    
    # 내 리뷰 확인
    my_review = reviews.filter(user=request.user).first()
    
    context = {
        'game': game,
        'reviews': reviews,
        'my_review': my_review,
    }
    return render(request, 'games/detail.html', context)

@login_required
def toggle_wishlist(request, game_id):
    game = get_object_or_404(Game, steam_appid=game_id)
    user = request.user
    
    if user.wishlist.filter(pk=game.pk).exists():
        user.wishlist.remove(game)
        is_wishlisted = False
    else:
        user.wishlist.add(game)
        is_wishlisted = True
        
    return JsonResponse({'is_wishlisted': is_wishlisted})
