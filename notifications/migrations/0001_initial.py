# Generated by Django 5.0.1 on 2025-06-06 04:57

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('orders', '0001_initial'),
        ('restaurants', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='NotificationTemplate',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('type', models.CharField(choices=[('ORDER_PLACED', 'Order Placed'), ('ORDER_CONFIRMED', 'Order Confirmed'), ('ORDER_PREPARING', 'Order Being Prepared'), ('ORDER_READY', 'Order Ready for Pickup'), ('ORDER_PICKED_UP', 'Order Picked Up'), ('ORDER_DELIVERED', 'Order Delivered'), ('ORDER_CANCELLED', 'Order Cancelled'), ('DRIVER_ASSIGNED', 'Driver Assigned'), ('DRIVER_NEARBY', 'Driver Nearby'), ('PAYMENT_SUCCESSFUL', 'Payment Successful'), ('PAYMENT_FAILED', 'Payment Failed'), ('REVIEW_REQUEST', 'Review Request'), ('PROMOTION_AVAILABLE', 'Promotion Available'), ('RESTAURANT_OPENED', 'Restaurant Opened'), ('RESTAURANT_CLOSED', 'Restaurant Closed'), ('SYSTEM_MAINTENANCE', 'System Maintenance')], max_length=50, unique=True)),
                ('title_template', models.CharField(max_length=200)),
                ('message_template', models.TextField()),
                ('is_active', models.BooleanField(default=True)),
                ('send_push', models.BooleanField(default=True)),
                ('send_email', models.BooleanField(default=False)),
                ('send_sms', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=200)),
                ('message', models.TextField()),
                ('priority', models.CharField(choices=[('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High'), ('URGENT', 'Urgent')], default='MEDIUM', max_length=10)),
                ('is_read', models.BooleanField(default=False)),
                ('read_at', models.DateTimeField(blank=True, null=True)),
                ('sent_push', models.BooleanField(default=False)),
                ('sent_email', models.BooleanField(default=False)),
                ('sent_sms', models.BooleanField(default=False)),
                ('action_url', models.URLField(blank=True, null=True)),
                ('action_text', models.CharField(blank=True, max_length=50, null=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('recipient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL)),
                ('related_order', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='orders.order')),
                ('related_restaurant', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='restaurants.restaurant')),
                ('template', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='notifications.notificationtemplate')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='NotificationPreference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_updates_push', models.BooleanField(default=True)),
                ('order_updates_email', models.BooleanField(default=True)),
                ('order_updates_sms', models.BooleanField(default=False)),
                ('promotions_push', models.BooleanField(default=True)),
                ('promotions_email', models.BooleanField(default=False)),
                ('promotions_sms', models.BooleanField(default=False)),
                ('system_updates_push', models.BooleanField(default=True)),
                ('system_updates_email', models.BooleanField(default=False)),
                ('restaurant_orders_push', models.BooleanField(default=True)),
                ('restaurant_orders_email', models.BooleanField(default=True)),
                ('restaurant_reviews_push', models.BooleanField(default=True)),
                ('restaurant_reviews_email', models.BooleanField(default=True)),
                ('driver_assignments_push', models.BooleanField(default=True)),
                ('driver_assignments_sms', models.BooleanField(default=True)),
                ('do_not_disturb_start', models.TimeField(blank=True, null=True)),
                ('do_not_disturb_end', models.TimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='notification_preferences', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='PushToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.TextField()),
                ('device_type', models.CharField(choices=[('ios', 'iOS'), ('android', 'Android'), ('web', 'Web')], max_length=10)),
                ('device_id', models.CharField(blank=True, max_length=100, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('last_used', models.DateTimeField(auto_now=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='push_tokens', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='NotificationLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('delivery_method', models.CharField(choices=[('push', 'Push Notification'), ('email', 'Email'), ('sms', 'SMS')], max_length=10)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('sent', 'Sent'), ('delivered', 'Delivered'), ('failed', 'Failed'), ('bounced', 'Bounced')], default='pending', max_length=20)),
                ('provider', models.CharField(blank=True, max_length=50, null=True)),
                ('provider_message_id', models.CharField(blank=True, max_length=200, null=True)),
                ('error_message', models.TextField(blank=True, null=True)),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('delivered_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('notification', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='delivery_logs', to='notifications.notification')),
            ],
            options={
                'ordering': ['-created_at'],
                'indexes': [models.Index(fields=['notification', 'delivery_method'], name='notificatio_notific_257f61_idx'), models.Index(fields=['status', 'created_at'], name='notificatio_status_68c9bc_idx')],
            },
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['recipient', 'is_read', 'created_at'], name='notificatio_recipie_86ea8b_idx'),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['recipient', 'created_at'], name='notificatio_recipie_f39341_idx'),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['template', 'created_at'], name='notificatio_templat_6821fb_idx'),
        ),
        migrations.AddIndex(
            model_name='pushtoken',
            index=models.Index(fields=['user', 'is_active'], name='notificatio_user_id_47d48f_idx'),
        ),
        migrations.AddIndex(
            model_name='pushtoken',
            index=models.Index(fields=['token'], name='notificatio_token_454efe_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='pushtoken',
            unique_together={('user', 'token')},
        ),
    ]
