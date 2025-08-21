# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Module
from .services import create_mux_asset

@receiver(post_save, sender=Module)
def create_mux_asset_on_save(sender, instance, created, **kwargs):
    if created and instance.module_type == "video" and instance.google_drive_file_id:
        video_url = f"https://drive.google.com/uc?id={instance.google_drive_file_id}&export=download"
        asset = create_mux_asset(video_url)
        if asset:
            instance.mux_asset_id = asset.data.id
            if asset.data.playback_ids:
                instance.mux_playback_id = asset.data.playback_ids[0].id
                instance.mux_status = asset.data.status
            instance.save()
