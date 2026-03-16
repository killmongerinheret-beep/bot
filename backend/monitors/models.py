from django.db import models
from django.utils import timezone
import hashlib
import secrets

class Agency(models.Model):
    PLAN_CHOICES = [
        ('free', 'Free'),
        ('pro', 'Pro'),
        ('agency', 'Agency'),
    ]
    
    name = models.CharField(max_length=255)
    api_key = models.CharField(max_length=255, unique=True, blank=True, null=True)
    telegram_chat_id = models.CharField(max_length=100, blank=True, null=True)
    owner_id = models.CharField(max_length=100, blank=True, null=True, db_index=True, unique=True, help_text="Clerk User ID")
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='free')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Agencies"


class User(models.Model):
    """Simple user model for authentication"""
    email = models.EmailField(unique=True, db_index=True)
    username = models.CharField(max_length=150, unique=True, db_index=True)
    password_hash = models.CharField(max_length=255)
    full_name = models.CharField(max_length=255, blank=True)
    agency = models.ForeignKey(Agency, on_delete=models.CASCADE, related_name='users')
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_super_admin = models.BooleanField(default=False)  # New field for super admin
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)

    def set_password(self, raw_password):
        """Hash and set password"""
        salt = secrets.token_hex(16)
        password_with_salt = f"{raw_password}{salt}"
        self.password_hash = f"{salt}${hashlib.sha256(password_with_salt.encode()).hexdigest()}"

    def check_password(self, raw_password):
        """Verify password"""
        try:
            salt, hashed = self.password_hash.split('$')
            password_with_salt = f"{raw_password}{salt}"
            return hashlib.sha256(password_with_salt.encode()).hexdigest() == hashed
        except:
            return False

    def __str__(self):
        return f"{self.username} ({self.agency.name})"

    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['email'], name='users_email_idx'),
            models.Index(fields=['username'], name='users_username_idx'),
        ]


class SiteCredential(models.Model):
    agency = models.ForeignKey(Agency, on_delete=models.CASCADE, related_name='credentials')
    site = models.CharField(max_length=50, choices=[('vatican', 'Vatican')])
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.site.upper()} Creds - {self.agency.name}"

class Proxy(models.Model):
    ip_port = models.CharField(max_length=255, help_text="e.g., 142.111.48.253:7030")
    username = models.CharField(max_length=255, blank=True, null=True)
    password = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    fail_count = models.PositiveIntegerField(default=0)
    consecutive_failures = models.PositiveIntegerField(default=0)
    cooldown_until = models.DateTimeField(null=True, blank=True)
    last_used = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.ip_port
    
    class Meta:
        verbose_name_plural = "Proxies"

class MonitorTask(models.Model):
    SITE_CHOICES = [
        ('vatican', 'Vatican Museums'),
    ]
    
    TICKET_TYPE_CHOICES = [
        (0, 'Regular Ticket'),
        (1, 'Guided Tour'),
    ]

    MATCH_STRATEGY_CHOICES = [
        ('any', 'ANY (Notify if any slot matches)'),
        ('all', 'ALL (Notify only if all slots match)'),
    ]

    NOTIFICATION_MODE_CHOICES = [
        ('any_change', 'Notify on any change'),
        ('available_only', 'Notify only when available'),
        ('silent', 'Silent (No notifications)'),
    ]

    TIER_CHOICES = [
        ('monitor', 'Monitor (Notify Only)'),
        ('sniper', 'Sniper (Auto-Book)'),
    ]

    agency = models.ForeignKey(Agency, on_delete=models.CASCADE, related_name='tasks')
    site = models.CharField(max_length=50, choices=SITE_CHOICES)
    area_name = models.CharField(max_length=255, help_text="e.g., Musei Vaticani or Colosseo")
    dates = models.JSONField(help_text="List of dates to check (e.g., ['2026-06-15'])")
    preferred_times = models.JSONField(help_text="List of preferred times (e.g., ['10:00', '14:30'])")
    visitors = models.PositiveIntegerField(default=1)
    ticket_type = models.IntegerField(choices=TICKET_TYPE_CHOICES, default=0)
    ticket_label = models.CharField(max_length=255, blank=True, null=True, help_text="e.g. 'Standard Entry (Full Price)'") 
    
    # ✅ ENHANCED: Vatican-specific ticket selection
    ticket_id = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        help_text="Vatican ticket ID (e.g., '929041748' from resolve_all_dynamic_ids). Leave empty to scan ALL tickets.",
        db_index=True  # For efficient grouping
    )
    ticket_name = models.CharField(
        max_length=300,
        blank=True,
        null=True,
        help_text="Human-readable ticket name (e.g., 'Musei Vaticani - Biglietti d'ingresso')"
    )
    
    # ✅ ENHANCED: Language for guided tours
    language = models.CharField(
        max_length=10, 
        blank=True, 
        null=True,
        help_text="Language code for guided tours: ENG, ITA, FRA, TED, SPA. NULL for standard tickets that don't require language."
    )
    
    check_interval = models.IntegerField(default=60, help_text="Interval in seconds")
    
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='monitor')
    match_strategy = models.CharField(max_length=20, choices=MATCH_STRATEGY_CHOICES, default='any')
    notification_mode = models.CharField(max_length=20, choices=NOTIFICATION_MODE_CHOICES, default='any_change')
    
    is_active = models.BooleanField(default=True)
    last_checked = models.DateTimeField(null=True, blank=True)
    last_status = models.CharField(max_length=50, default='unknown')
    last_result_summary = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.site.upper()} Task - {self.agency.name} ({self.created_at.strftime('%Y-%m-%d')})"

class CheckResult(models.Model):
    task = models.ForeignKey(MonitorTask, on_delete=models.CASCADE, related_name='results')
    check_time = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=50) # available, sold_out, error
    details = models.JSONField(blank=True, null=True) # Detailed slot data
    error_message = models.TextField(blank=True, null=True)
    screenshot_path = models.CharField(max_length=500, blank=True, null=True)

    def __str__(self):
        return f"Result for {self.task.id} at {self.check_time}"


class TelegramGroup(models.Model):
    """
    Represents a Telegram group/chat that has added the bot.
    Requires admin approval before receiving notifications.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    ]
    
    # Telegram Info
    chat_id = models.CharField(max_length=255, unique=True, db_index=True)
    chat_type = models.CharField(max_length=20)  # 'group', 'supergroup', 'channel', 'private'
    chat_title = models.CharField(max_length=255, null=True, blank=True)
    chat_username = models.CharField(max_length=255, null=True, blank=True)
    
    # Linked Agency (optional - for multi-agency support)
    agency = models.ForeignKey(Agency, on_delete=models.SET_NULL, null=True, blank=True, related_name='telegram_groups')
    
    # Approval Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.CharField(max_length=255, null=True, blank=True)  # Admin user ID
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(null=True, blank=True)
    
    # Metadata
    added_by_user_id = models.CharField(max_length=255, null=True, blank=True)
    added_by_username = models.CharField(max_length=255, null=True, blank=True)
    added_by_first_name = models.CharField(max_length=255, null=True, blank=True)
    member_count = models.IntegerField(null=True, blank=True)
    
    # Settings
    notification_enabled = models.BooleanField(default=True)
    notification_language = models.CharField(max_length=10, default='en')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'telegram_groups'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.chat_title or self.chat_id} ({self.status})"
    
    def is_approved(self):
        return self.status == 'approved'
    
    def approve(self, admin_id):
        self.status = 'approved'
        self.approved_by = admin_id
        self.approved_at = timezone.now()
        self.save()
    
    def reject(self, admin_id, reason=None):
        self.status = 'rejected'
        self.approved_by = admin_id
        self.rejection_reason = reason
        self.save()
    
    def suspend(self, reason=None):
        self.status = 'suspended'
        self.rejection_reason = reason
        self.save()
