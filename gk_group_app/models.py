from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
from django.contrib.auth.models import User


class ContactMessage(models.Model):
    """
    Model for storing contact form submissions
    """
    name = models.CharField(
        max_length=100,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z\s\.]+$',
                message='Name should only contain letters, spaces, and periods.'
            )
        ],
        help_text="Full name (letters, spaces, and periods only)"
    )
    email = models.EmailField(
        max_length=254,
        help_text="Valid email address"
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^[\d\+\-\s\(\)]+$',
                message='Phone number should only contain digits, +, -, spaces, and parentheses.'
            )
        ],
        help_text="Optional phone number"
    )
    message = models.TextField(
        min_length=10,
        max_length=2000,
        help_text="Your message (10-2000 characters)"
    )
    subject = models.CharField(
        max_length=200,
        default="General Inquiry",
        help_text="Subject of the message"
    )
    interest_area = models.CharField(
        max_length=50,
        choices=[
            ('general', 'General Inquiry'),
            ('gk_textiles', 'GK Textiles'),
            ('gk_steels', 'GK Steels'),
            ('partnership', 'Partnership'),
            ('feedback', 'Feedback'),
        ],
        default='general',
        help_text="Area of interest"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the submitter"
    )
    user_agent = models.TextField(
        blank=True,
        help_text="Browser user agent"
    )
    is_read = models.BooleanField(
        default=False,
        help_text="Whether the message has been read"
    )
    is_archived = models.BooleanField(
        default=False,
        help_text="Whether the message is archived"
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        help_text="When the message was submitted"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When the message was last updated"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Contact Message"
        verbose_name_plural = "Contact Messages"
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['is_read']),
            models.Index(fields=['interest_area']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return f"{self.name} - {self.email} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    def get_absolute_url(self):
        return f"/admin/gk_group_app/contactmessage/{self.id}/change/"

    @property
    def is_recent(self):
        """Return True if message was created within the last 24 hours"""
        return timezone.now() - self.created_at <= timezone.timedelta(days=1)


class SiteContent(models.Model):
    """
    Model for managing dynamic site content
    """
    CONTENT_TYPES = [
        ('hero_title', 'Hero Section Title'),
        ('hero_subtitle', 'Hero Section Subtitle'),
        ('about_text', 'About Section Text'),
        ('contact_info', 'Contact Information'),
        ('meta_description', 'Meta Description'),
        ('footer_text', 'Footer Text'),
        ('announcement', 'Site Announcement'),
    ]

    content_type = models.CharField(
        max_length=50,
        choices=CONTENT_TYPES,
        unique=True,
        help_text="Type of content"
    )
    content = models.TextField(
        help_text="Content text"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this content is active"
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        help_text="When this content was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this content was last updated"
    )

    class Meta:
        ordering = ['content_type']
        verbose_name = "Site Content"
        verbose_name_plural = "Site Contents"

    def __str__(self):
        return f"{self.get_content_type_display()}"

    @classmethod
    def get_content(cls, content_type, default=None):
        """Get content by type, return default if not found"""
        try:
            content_obj = cls.objects.get(content_type=content_type, is_active=True)
            return content_obj.content
        except cls.DoesNotExist:
            return default


class TeamMember(models.Model):
    """
    Model for team members (if needed in the future)
    """
    name = models.CharField(
        max_length=100,
        help_text="Team member name"
    )
    position = models.CharField(
        max_length=100,
        help_text="Job position"
    )
    bio = models.TextField(
        blank=True,
        help_text="Short biography"
    )
    image = models.ImageField(
        upload_to='team/',
        blank=True,
        null=True,
        help_text="Team member photo"
    )
    email = models.EmailField(
        blank=True,
        null=True,
        help_text="Contact email"
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Contact phone"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this team member is active"
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order"
    )
    created_at = models.DateTimeField(
        default=timezone.now
    )

    class Meta:
        ordering = ['order', 'name']
        verbose_name = "Team Member"
        verbose_name_plural = "Team Members"

    def __str__(self):
        return f"{self.name} - {self.position}"
