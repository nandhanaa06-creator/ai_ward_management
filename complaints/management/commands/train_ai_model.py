"""
Django management command to train the AI complaint categorization model.
Usage: python manage.py train_ai_model
"""

from django.core.management.base import BaseCommand
from ai_model.train_model import train_model, test_model_predictions


class Command(BaseCommand):
    help = 'Train the AI model for complaint categorization'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n🤖 Starting AI Model Training...\n'))
        
        try:
            # Train the model
            model, accuracy = train_model()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ Model trained successfully with {accuracy*100:.2f}% accuracy!\n'
                )
            )
            
            # Test predictions
            self.stdout.write(self.style.WARNING('\n🧪 Testing model predictions...\n'))
            test_model_predictions()
            
            self.stdout.write(
                self.style.SUCCESS(
                    '\n✅ AI Model is ready to use!\n'
                    'The model will now automatically categorize complaints.\n'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\n❌ Error training model: {str(e)}\n')
            )
            raise
