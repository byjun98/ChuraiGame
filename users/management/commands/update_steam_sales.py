"""
Django Management Command: Update Steam Sales Data
Fetches latest Steam sale data and updates the JSON file.

Usage:
    python manage.py update_steam_sales

For automated daily updates, set up a cron job:
    # Linux/Mac - Add to crontab (run: crontab -e)
    0 6 * * * cd /path/to/project && /path/to/venv/bin/python manage.py update_steam_sales

    # Windows - Use Task Scheduler
    # Create a task that runs: python manage.py update_steam_sales
"""
import requests
import json
import time
import os
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


class Command(BaseCommand):
    help = 'Fetch and update Steam sale data from steamsale.windbell.co.kr API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=2000,
            help='Number of sale items to fetch (default: 2000)'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Items per API request (default: 100, max: 100)'
        )

    def handle(self, *args, **options):
        target_count = options['count']
        batch_size = min(options['batch_size'], 100)  # Max 100
        
        API_URL = "https://steamsale.windbell.co.kr/api/v1/sales"
        
        collected_data = []
        page = 1
        
        self.stdout.write(
            self.style.NOTICE(f"🚀 Starting Steam sale data update: Target {target_count} items")
        )
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://steamsale.windbell.co.kr/'
        }

        while len(collected_data) < target_count:
            try:
                params = {
                    'keyword': '',
                    'page': page,
                    'size': batch_size
                }
                
                response = requests.get(API_URL, params=params, headers=headers, timeout=30)
                
                if response.status_code != 200:
                    self.stdout.write(
                        self.style.ERROR(f"❌ Page {page} request failed: {response.status_code}")
                    )
                    break
                
                data = response.json()
                items = data.get('list', [])
                
                if not items:
                    self.stdout.write(self.style.WARNING("🏁 No more data available."))
                    break
                    
                # Process and store data
                for item in items:
                    game_info = {
                        'game_id': item.get('game_id'),
                        'title': item.get('title_nm'),
                        'current_price': item.get('sale_price_va'),
                        'original_price': item.get('full_price_va'),
                        'discount_rate': item.get('discount_rt'),
                        'thumbnail': item.get('img_lk'),
                        'store_link': item.get('store_lk')
                    }
                    collected_data.append(game_info)
                
                if page % 5 == 0:
                    self.stdout.write(f"   ✅ Page {page} done (Total: {len(collected_data)} items)")
                
                page += 1
                time.sleep(0.2)  # Rate limiting
                
            except requests.RequestException as e:
                self.stdout.write(self.style.ERROR(f"⚠️ Request error: {e}"))
                break
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"⚠️ Error: {e}"))
                break

        # Trim to target count
        final_result = collected_data[:target_count]

        # Save to file
        file_path = os.path.join(settings.BASE_DIR, 'users', 'steam_sale_dataset_fast.json')
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(final_result, f, ensure_ascii=False, indent=2)
            
            self.stdout.write(
                self.style.SUCCESS(f"\n🎉 Complete! Saved {len(final_result)} items to {file_path}")
            )
        except IOError as e:
            raise CommandError(f"Failed to save file: {e}")
