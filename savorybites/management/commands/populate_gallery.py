import os
from django.core.management.base import BaseCommand
from django.core.files import File
from savorybites.models import Gallery

class Command(BaseCommand):
    help = 'Populate Gallery model with existing images in media/gallery_images/'

    def handle(self, *args, **options):
        gallery_dir = 'media/gallery_images/'
        if not os.path.exists(gallery_dir):
            self.stdout.write(self.style.WARNING(f'Directory {gallery_dir} does not exist'))
            return

        count = 0
        for filename in os.listdir(gallery_dir):
            if filename.endswith(('.png', '.jpg', '.jpeg', '.gif')):
                filepath = os.path.join(gallery_dir, filename)
                if not Gallery.objects.filter(image=f'gallery_images/{filename}').exists():
                    with open(filepath, 'rb') as f:
                        gallery_obj = Gallery(image=File(f, name=filename))
                        gallery_obj.save()
                        count += 1
                        self.stdout.write(f'Created Gallery object for {filename}')

        self.stdout.write(self.style.SUCCESS(f'Successfully created {count} Gallery objects'))