"""
Enhanced Restaurant Model Migration

This migration enhances the Restaurant model to support comprehensive wizard data:
- Changes OneToOne to ForeignKey (multiple restaurants per user)  
- Adds comprehensive contact, branding, delivery, and facility fields
- Adds operating hours and delivery hours models
- Adds JSON fields for complex data structures

Note: This is a major schema change. Consider data migration strategies for existing data.
"""

from django.db import migrations, models
import uuid
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('restaurants', '0003_alter_menucategory_order'),  # Correct dependency
    ]

    operations = [
        # First, create new models for operating hours
        migrations.CreateModel(
            name='RestaurantOperatingHours',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('day_of_week', models.CharField(choices=[('monday', 'Monday'), ('tuesday', 'Tuesday'), ('wednesday', 'Wednesday'), ('thursday', 'Thursday'), ('friday', 'Friday'), ('saturday', 'Saturday'), ('sunday', 'Sunday')], max_length=10)),
                ('is_open', models.BooleanField(default=True)),
                ('open_time', models.TimeField(blank=True, null=True)),
                ('close_time', models.TimeField(blank=True, null=True)),
                ('has_break', models.BooleanField(default=False)),
                ('break_start', models.TimeField(blank=True, null=True)),
                ('break_end', models.TimeField(blank=True, null=True)),
                ('restaurant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='operating_hours', to='restaurants.restaurant')),
            ],
            options={
                'ordering': ['day_of_week'],
            },
        ),
        
        migrations.CreateModel(
            name='RestaurantDeliveryHours',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('day_of_week', models.CharField(choices=[('monday', 'Monday'), ('tuesday', 'Tuesday'), ('wednesday', 'Wednesday'), ('thursday', 'Thursday'), ('friday', 'Friday'), ('saturday', 'Saturday'), ('sunday', 'Sunday')], max_length=10)),
                ('is_available', models.BooleanField(default=True)),
                ('start_time', models.TimeField(blank=True, null=True)),
                ('end_time', models.TimeField(blank=True, null=True)),
                ('restaurant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='delivery_hours', to='restaurants.restaurant')),
            ],
            options={
                'ordering': ['day_of_week'],
            },
        ),

        # Add new fields to Restaurant model
        migrations.AddField(
            model_name='restaurant',
            name='cuisine_type',
            field=models.CharField(default='Other', max_length=50),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='price_range',
            field=models.CharField(default='$$', max_length=10),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='city',
            field=models.CharField(default='-', max_length=100),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='state',
            field=models.CharField(default='-', max_length=100),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='zip_code',
            field=models.CharField(default='00000', max_length=20),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='country',
            field=models.CharField(default='United States', max_length=100),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='delivery_radius',
            field=models.FloatField(default=5.0),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='delivery_fee',
            field=models.DecimalField(decimal_places=2, default=2.99, max_digits=6),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='minimum_order',
            field=models.DecimalField(decimal_places=2, default=15.00, max_digits=8),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='service_areas',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='primary_phone',
            field=models.CharField(default='-', max_length=20),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='secondary_phone',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='email',
            field=models.EmailField(default='temp@example.com', max_length=254),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='website',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='social_media',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='contact_person',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='emergency_contact',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='banner_image',
            field=models.ImageField(blank=True, null=True, upload_to='restaurant/banners/'),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='brand_colors',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='tagline',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='story',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='specialties',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='tags',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='special_diets',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='accessibility_features',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='parking_available',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='is_active',
            field=models.BooleanField(default=True),
        ),

        # Add unique constraints for hours
        migrations.AlterUniqueTogether(
            name='restaurantoperatinghours',
            unique_together={('restaurant', 'day_of_week')},
        ),
        migrations.AlterUniqueTogether(
            name='restaurantdeliveryhours',
            unique_together={('restaurant', 'day_of_week')},
        ),

        # Update Restaurant ordering
        migrations.AlterModelOptions(
            name='restaurant',
            options={'ordering': ['-created_at']},
        ),

        # CRITICAL: Change Restaurant.user from OneToOne to ForeignKey
        # This requires careful handling of existing data
        
        migrations.AlterField(
            model_name='restaurant',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='restaurants', to='users.customuser'),
        ),
    ]