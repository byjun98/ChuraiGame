from django.core.management.base import BaseCommand
from users.management.commands.add_korean_games import KOREAN_POPULAR_GAMES
from games.models import Game

class Command(BaseCommand):
    help = 'Sync Korean games: Delete games from DB that are NOT in KOREAN_POPULAR_GAMES list'

    def handle(self, *args, **options):
        # 1. Source of Truth
        source_titles = {g['title'].strip() for g in KOREAN_POPULAR_GAMES}
        self.stdout.write(f"Source list has {len(source_titles)} games.")

        # 2. Find Candidates in DB
        # We target games that have 'korean' or 'nintendo' tags, or contain Korean characters in the title.
        # These are the primary markers for games managed by add_korean_games.py.
        candidates = Game.objects.filter(
            title__regex=r'[가-힣]'
        ) | Game.objects.filter(
            tags__slug__in=['korean', 'nintendo']
        )
        
        candidates = candidates.distinct()
        
        self.stdout.write(f"Scanning {candidates.count()} candidate games in DB...")
        
        # 3. Check and Delete
        deleted_count = 0
        for game in candidates:
            db_title = game.title.strip()
            
            # Exact match check
            # If the game in DB is NOT in our source list, assume it is a "ghost" (removed from list).
            if db_title not in source_titles:
                 # Debug info
                 tags = list(game.tags.values_list('slug', flat=True))
                 self.stdout.write(self.style.WARNING(f"Ghost found: '{db_title}' (Tags: {tags})"))
                 
                 # Delete
                 game.delete()
                 deleted_count += 1
                 self.stdout.write(self.style.ERROR(f" -> DELETED"))

        self.stdout.write(self.style.SUCCESS(f"Sync complete. Deleted {deleted_count} ghost games."))
