from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count
import json

from .models import ContactMessage, SiteContent, TeamMember


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    """
    Admin interface for ContactMessage model
    """
    list_display = [
        'name', 'email', 'phone', 'interest_area_display', 'subject_preview',
        'is_read', 'is_recent', 'created_at', 'mark_as_read_action'
    ]
    list_filter = [
        'is_read', 'is_archived', 'interest_area', 'created_at'
    ]
    search_fields = [
        'name', 'email', 'phone', 'subject', 'message'
    ]
    list_editable = ['is_read', 'is_archived']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    readonly_fields = [
        'ip_address', 'user_agent', 'created_at', 'updated_at'
    ]

    fieldsets = (
        ('Contact Information', {
            'fields': ('name', 'email', 'phone', 'interest_area')
        }),
        ('Message Details', {
            'fields': ('subject', 'message')
        }),
        ('System Information', {
            'fields': ('ip_address', 'user_agent', 'created_at', 'updated_at', 'is_read', 'is_archived'),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_as_read', 'mark_as_unread', 'archive_messages', 'unarchive_messages']

    def interest_area_display(self, obj):
        """Display interest area with color coding"""
        colors = {
            'general': 'secondary',
            'gk_textiles': 'warning',
            'gk_steels': 'info',
            'partnership': 'success',
            'feedback': 'danger'
        }
        color = colors.get(obj.interest_area, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color,
            obj.get_interest_area_display()
        )
    interest_area_display.short_description = 'Interest Area'
    interest_area_display.admin_order_field = 'interest_area'

    def subject_preview(self, obj):
        """Show truncated subject"""
        if len(obj.subject) > 50:
            return obj.subject[:50] + '...'
        return obj.subject
    subject_preview.short_description = 'Subject'

    def is_recent(self, obj):
        """Show if message is recent (within 24 hours)"""
        if obj.is_recent:
            return format_html(
                '<span class="badge bg-success">Recent</span>'
            )
        return ''
    is_recent.short_description = 'Recent'
    is_recent.boolean = False

    def mark_as_read_action(self, obj):
        """Custom action to mark as read"""
        if not obj.is_read:
            obj.is_read = True
            obj.save()
            return format_html(
                '<a href="{}" class="button">Mark as Read</a>',
                reverse('admin:gk_group_app_contactmessage_change', args=[obj.pk])
            )
        return format_html(
            '<span class="badge bg-success">Read</span>'
        )
    mark_as_read_action.short_description = 'Status'

    def mark_as_read(self, request, queryset):
        """Bulk mark as read action"""
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} messages marked as read.')
    mark_as_read.short_description = 'Mark selected as read'

    def mark_as_unread(self, request, queryset):
        """Bulk mark as unread action"""
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} messages marked as unread.')
    mark_as_unread.short_description = 'Mark selected as unread'

    def archive_messages(self, request, queryset):
        """Bulk archive action"""
        updated = queryset.update(is_archived=True)
        self.message_user(request, f'{updated} messages archived.')
    archive_messages.short_description = 'Archive selected messages'

    def unarchive_messages(self, request, queryset):
        """Bulk unarchive action"""
        updated = queryset.update(is_archived=False)
        self.message_user(request, f'{updated} messages unarchived.')
    unarchive_messages.short_description = 'Unarchive selected messages'

    def get_queryset(self, request):
        """Optimize queries with related data"""
        return super().get_queryset(request).select_related()

    def changelist_view(self, request, extra_context=None):
        """Add summary statistics to changelist"""
        response = super().changelist_view(request, extra_context)

        try:
            qs = self.get_queryset(request)
            total_messages = qs.count()
            unread_messages = qs.filter(is_read=False).count()
            archived_messages = qs.filter(is_archived=True).count()
            recent_messages = qs.filter(
                created_at__gte=timezone.now() - timezone.timedelta(days=1)
            ).count()

            response.context_data.update({
                'summary_cards': {
                    'total': total_messages,
                    'unread': unread_messages,
                    'archived': archived_messages,
                    'recent': recent_messages,
                }
            })
        except Exception:
            pass

        return response


@admin.register(SiteContent)
class SiteContentAdmin(admin.ModelAdmin):
    """
    Admin interface for SiteContent model
    """
    list_display = ['content_type_display', 'content_preview', 'is_active', 'updated_at']
    list_filter = ['is_active', 'content_type', 'updated_at']
    search_fields = ['content', 'content_type']
    list_editable = ['is_active']
    ordering = ['content_type']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Content Details', {
            'fields': ('content_type', 'content', 'is_active')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def content_type_display(self, obj):
        """Display content type with icon"""
        icons = {
            'hero_title': 'fas fa-heading',
            'hero_subtitle': 'fas fa-quote-left',
            'about_text': 'fas fa-info-circle',
            'contact_info': 'fas fa-address-card',
            'meta_description': 'fas fa-search',
            'footer_text': 'fas fa-footer',
            'announcement': 'fas fa-bullhorn',
        }
        icon = icons.get(obj.content_type, 'fas fa-file-alt')
        return format_html(
            '<i class="{} me-2"></i>{}',
            icon,
            obj.get_content_type_display()
        )
    content_type_display.short_description = 'Content Type'

    def content_preview(self, obj):
        """Show truncated content"""
        if len(obj.content) > 100:
            return obj.content[:100] + '...'
        return obj.content
    content_preview.short_description = 'Content Preview'

    def has_add_permission(self, request):
        """Only allow adding if content type doesn't exist"""
        return True

    def get_queryset(self, request):
        """Optimize queries"""
        return super().get_queryset(request)


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    """
    Admin interface for TeamMember model
    """
    list_display = [
        'photo_thumbnail', 'name', 'position', 'email', 'phone',
        'is_active', 'order', 'created_at'
    ]
    list_filter = ['is_active', 'position', 'created_at']
    search_fields = ['name', 'position', 'email', 'bio']
    list_editable = ['is_active', 'order']
    ordering = ['order', 'name']
    readonly_fields = ['created_at']

    fieldsets = (
        ('Member Information', {
            'fields': ('name', 'position', 'bio', 'is_active', 'order')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone')
        }),
        ('Photo', {
            'fields': ('image',)
        }),
        ('System Information', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def photo_thumbnail(self, obj):
        """Show thumbnail of member photo"""
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="50" class="rounded-circle" style="object-fit: cover;">',
                obj.image.url
            )
        return format_html(
            '<div class="bg-secondary text-white rounded-circle d-flex align-items-center justify-content-center" style="width: 50px; height: 50px;"><i class="fas fa-user"></i></div>'
        )
    photo_thumbnail.short_description = 'Photo'

    def get_queryset(self, request):
        """Optimize queries"""
        return super().get_queryset(request)


# Customize admin site
admin.site.site_header = 'GK Group Administration'
admin.site.site_title = 'GK Group Admin'
admin.site.index_title = 'Welcome to GK Group Administration Panel'

# Add custom CSS for admin interface
class GKGroupAdminSite(admin.AdminSite):
    site_header = 'GK Group Administration'
    site_title = 'GK Group Admin'
    index_title = 'Welcome to GK Group Administration Panel'

    def each_context(self, request):
        context = super().each_context(request)
        context['custom_css'] = """
        <style>
        .summary-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
        }
        .badge {
            font-size: 0.8em;
        }
        </style>
        """
        return context


# Create custom admin templates directory
class GKGroupModelAdmin(admin.ModelAdmin):
    """Base admin class with custom templates"""

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('mark-read/<int:object_id>/', self.admin_site.admin_view(self.mark_read_view), name='mark_read'),
        ]
        return custom_urls + urls

    def mark_read_view(self, request, object_id):
        """Custom view to mark message as read"""
        try:
            obj = self.get_object(request, object_id)
            if obj:
                obj.is_read = True
                obj.save()
                self.message_user(request, 'Message marked as read.')
        except Exception as e:
            self.message_user(request, f'Error: {str(e)}')

        from django.http import HttpResponseRedirect
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('admin:gk_group_app_contactmessage_changelist')))


# Apply custom admin base class
for model in [ContactMessage, SiteContent, TeamMember]:
    admin.site.unregister(model)
    admin.site.register(model, type(
        f'{model.__name__}Admin',
        (GKGroupModelAdmin, admin.ModelAdmin),
        {}
    ))
