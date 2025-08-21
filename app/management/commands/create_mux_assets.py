from django.core.management.base import BaseCommand
from app.models import Module
from app.services import create_mux_asset

class Command(BaseCommand):
    help = "Create Mux assets for all video modules without one"

    def handle(self, *args, **kwargs):
        modules = Module.objects.filter(module_type="video", mux_asset_id__isnull=True)
        for module in modules:
            self.stdout.write(f"Creating asset for {module.name}...")
            video_url = f"https://drive.google.com/uc?id={module.google_drive_file_id}&export=download"
            asset = create_mux_asset(video_url)
            if asset:
                asset_id = asset.data.id
                playback_id = asset.data.playback_ids[0].id
            else:
                self.stdout.write(self.style.ERROR(f"❌ Failed to create Mux asset for {module.name}"))
                continue
            module.mux_asset_id = asset_id
            module.mux_playback_id = playback_id
            module.save()
            self.stdout.write(self.style.SUCCESS(f"✔ Created Mux asset for {module.name}"))
