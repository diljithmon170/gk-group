from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib import messages
from django.core.mail import send_mail, BadHeaderError
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Count
import json
import logging

from .models import ContactMessage, SiteContent, TeamMember
from .forms import ContactForm, QuickContactForm, NewsletterForm

logger = logging.getLogger(__name__)

def get_client_ip(request):
    """Get the client's IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def get_base_context():
    """Get base context data for all pages"""
    return {
        'company_name': 'GK Group',
        'founder_name': 'Mr. Gireesh Kumar',
        'location': 'Palakkad, Kerala, India',
        'tagline': 'Quality You Trust. Service with Commitment.',
        'contact_email': 'gkgroup@mail.com',
        'contact_phone': '+91 0023 4553 759',
        'whatsapp_number': '+9100234553759',
    }

def index(request):
    """
    Home page view with enhanced content
    """
    context = get_base_context()

    # Get dynamic content or use defaults
    context.update({
        'page_title': 'GK Group | Premium Textiles & Steel in Palakkad, Kerala',
        'meta_description': 'GK Group offers premium textiles and steel products in Palakkad, Kerala. Quality clothing, fabrics, construction materials, and hardware with trusted service.',
        'hero_title': SiteContent.get_content('hero_title', 'Welcome to GK Group'),
        'hero_subtitle': SiteContent.get_content('hero_subtitle', context['tagline']),
        'recent_messages_count': ContactMessage.objects.filter(is_read=False).count(),
    })

    return render(request, 'index.html', context)

def about(request):
    """
    About page with company story and information
    """
    context = get_base_context()
    context.update({
        'page_title': 'About GK Group | Our Story & Mission | Gireesh Kumar',
        'meta_description': 'Learn about GK Group\'s journey under founder Mr. Gireesh Kumar. Our mission to provide quality textiles and steel products in Palakkad, Kerala.',
        'about_text': SiteContent.get_content('about_text',
            'Founded with a vision to provide quality products and exceptional service, '
            'GK Group has grown from humble beginnings to become a trusted name in '
            'Palakkad\'s business community. Under the leadership of Mr. Gireesh Kumar, '
            'we continue to uphold our values of trust, quality, and customer satisfaction.'),
        'team_members': TeamMember.objects.filter(is_active=True),
    })

    return render(request, 'about.html', context)

def gk_textiles(request):
    """
    GK Textiles dedicated page
    """
    context = get_base_context()
    context.update({
        'page_title': 'GK Textiles | Premium Clothing & Fabrics | Palakkad',
        'meta_description': 'Explore GK Textiles - your destination for premium clothing, traditional wear, modern outfits, fabrics, and family collections in Palakkad, Kerala.',
        'division_name': 'GK Textiles',
        'division_tagline': 'Elegant Fabrics, Timeless Style',
        'division_description': 'Discover our extensive collection of premium textiles ranging from '
                              'traditional Indian wear to contemporary fashion. At GK Textiles, '
                              'we offer quality fabrics, sarees, and clothing for the entire family.',
    })

    return render(request, 'gk_textiles.html', context)

def gk_steels(request):
    """
    GK Steels dedicated page
    """
    context = get_base_context()
    context.update({
        'page_title': 'GK Steels | Construction Steel & Hardware | Kerala',
        'meta_description': 'GK Steels provides high-quality construction steel, pipes, rods, and hardware materials. Trusted supplier for construction projects in Palakkad, Kerala.',
        'division_name': 'GK Steels',
        'division_tagline': 'Strength That Builds Your Future',
        'division_description': 'Your trusted partner for all construction and hardware needs. '
                              'We provide premium quality steel products, pipes, rods, and '
                              'essential hardware materials for all types of construction projects.',
    })

    return render(request, 'gk_steels.html', context)

def contact(request):
    """
    Contact page with form and information
    """
    context = get_base_context()

    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            try:
                # Save the contact message
                contact_message = form.save(commit=False)
                contact_message.ip_address = get_client_ip(request)
                contact_message.user_agent = request.META.get('HTTP_USER_AGENT', '')
                contact_message.save()

                # Send email notification
                send_contact_email_notification(contact_message)

                messages.success(request,
                    'Thank you for contacting us! We will get back to you within 24 hours.')
                return redirect('contact')

            except Exception as e:
                logger.error(f"Error processing contact form: {str(e)}")
                messages.error(request,
                    'Sorry, there was an error sending your message. Please try again or call us directly.')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ContactForm()

    context.update({
        'page_title': 'Contact GK Group | Visit Our Store in Palakkad',
        'meta_description': 'Contact GK Group for premium textiles and steel products. Visit our store in Palakkad, Kerala or call us. Quick response guaranteed.',
        'form': form,
        'contact_info': SiteContent.get_content('contact_info',
            'Visit us during business hours or call us for any inquiries.'),
        'map_latitude': '10.7867',  # Palakkad coordinates
        'map_longitude': '76.6548',
    })

    return render(request, 'contact.html', context)

@require_http_methods(["POST"])
def contact_form_ajax(request):
    """
    Handle contact form submission via AJAX
    """
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return HttpResponseBadRequest('Invalid request')

    form = ContactForm(request.POST)
    if form.is_valid():
        try:
            contact_message = form.save(commit=False)
            contact_message.ip_address = get_client_ip(request)
            contact_message.user_agent = request.META.get('HTTP_USER_AGENT', '')
            contact_message.save()

            # Send email notification
            send_contact_email_notification(contact_message)

            return JsonResponse({
                'success': True,
                'message': 'Thank you for contacting us! We will get back to you within 24 hours.'
            })

        except Exception as e:
            logger.error(f"Error in AJAX contact form: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': 'Sorry, there was an error sending your message. Please try again.'
            })
    else:
        return JsonResponse({
            'success': False,
            'errors': form.errors,
            'message': 'Please correct the errors below.'
        })

def send_contact_email_notification(contact_message):
    """
    Send email notification for new contact message
    """
    try:
        subject = f"New Contact Form Submission: {contact_message.subject}"

        # HTML email template
        html_message = render_to_string('emails/contact_notification.html', {
            'contact_message': contact_message,
            'site_name': 'GK Group',
        })

        # Plain text version
        plain_message = strip_tags(html_message)

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@gkgroup.com'),
            recipient_list=[getattr(settings, 'CONTACT_EMAIL', 'gkgroup@mail.com')],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Contact email sent successfully for {contact_message.email}")

    except BadHeaderError:
        logger.error("Invalid header found in contact email")
        raise
    except Exception as e:
        logger.error(f"Error sending contact email: {str(e)}")
        raise

@csrf_exempt
@require_http_methods(["POST"])
def newsletter_subscribe(request):
    """
    Handle newsletter subscription
    """
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return HttpResponseBadRequest('Invalid request')

    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip().lower()

        if not email or '@' not in email:
            return JsonResponse({
                'success': False,
                'message': 'Please enter a valid email address.'
            })

        # Here you would typically save to a newsletter model
        # For now, just log it
        logger.info(f"Newsletter subscription request: {email}")

        return JsonResponse({
            'success': True,
            'message': 'Thank you for subscribing to our newsletter!'
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid request format.'
        })

def custom_404(request, exception):
    """
    Custom 404 error page
    """
    context = get_base_context()
    context.update({
        'page_title': 'Page Not Found | GK Group',
        'error_code': '404',
        'error_message': 'The page you are looking for might have been removed, had its name changed, or is temporarily unavailable.',
    })
    return render(request, 'errors/404.html', context, status=404)

def custom_500(request):
    """
    Custom 500 error page
    """
    context = get_base_context()
    context.update({
        'page_title': 'Server Error | GK Group',
        'error_code': '500',
        'error_message': 'Something went wrong on our end. Our team has been notified and we are working to fix this issue.',
    })
    return render(request, 'errors/500.html', context, status=500)

def robots_txt(request):
    """
    Generate robots.txt
    """
    content = """User-agent: *
Allow: /
Disallow: /admin/
Disallow: /static/
Sitemap: /sitemap.xml

Crawl-delay: 1"""

    response = HttpResponse(content, content_type='text/plain')
    return response

def sitemap_xml(request):
    """
    Generate XML sitemap
    """
    from django.contrib.sitemaps import Sitemap

    class StaticViewSitemap(Sitemap):
        def items(self):
            return ['index', 'about', 'gk_textiles', 'gk_steels', 'contact']

        def location(self, item):
            return f'/{item}/' if item != 'index' else '/'

        def changefreq(self, item):
            frequencies = {
                'index': 'weekly',
                'about': 'monthly',
                'gk_textiles': 'weekly',
                'gk_steels': 'weekly',
                'contact': 'monthly',
            }
            return frequencies.get(item, 'monthly')

        def priority(self, item):
            priorities = {
                'index': 1.0,
                'about': 0.8,
                'gk_textiles': 0.9,
                'gk_steels': 0.9,
                'contact': 0.7,
            }
            return priorities.get(item, 0.5)

    from django.contrib.sitemaps.views import sitemap
    sitemaps = {
        'static': StaticViewSitemap,
    }

    return sitemap(request, sitemaps)