"""
Django management command to train the AI priority prediction model.
Usage: python manage.py train_priority_model
"""

from django.core.management.base import BaseCommand
from ai_model.priority_model import train_priority_model, test_priority_predictions


class Command(BaseCommand):
    help = 'Train the AI model for complaint priority prediction'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n🎯 Starting Priority Prediction Model Training...\n'))
        
        try:
            # Train the model
            model, accuracy = train_priority_model()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ Priority model trained successfully with {accuracy*100:.2f}% accuracy!\n'
                )
            )
            
            # Test predictions
            self.stdout.write(self.style.WARNING('\n🧪 Testing priority predictions...\n'))
            test_priority_predictions()
            
            self.stdout.write(
                self.style.SUCCESS(
                    '\n✅ Priority Prediction Model is ready to use!\n'
                    'The model will now automatically predict complaint priorities.\n'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\n❌ Error training priority model: {str(e)}\n')
            )
            raise
