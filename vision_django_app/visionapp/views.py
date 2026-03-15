import json
import random
import csv
import io
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from charts import GolovinSivtsev, LandoltC, EChart
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from visionapp.models import UserVisionData, GeneratedNotes, MindMapNode
CHART_V_VALUES = [
    0.1, 0.2, 0.3,  
    0.4, 0.5, 0.6, 0.7, 0.8, 0.9,   
    1.0, 1.5, 2.0   
]

# ✅ Helper functions                                                                                                                                                                                                                                                                                                                                                                                                                                                                 
def estimate_diopter_from_v(v):                                        
    """
    Simple approximation: higher v -> better vision (lower diopter)
    Diopter roughly ~ -1.5*(1 - v)
    """
    return round(-1.5 * (1.0 - v), 2)

def index(request):
    return render(request, 'index.html')


def signup_view(request):
    if request.method == 'POST':
        email = request.POST.get('DUsername')
        password = request.POST.get('DPassword')
        conf_password = request.POST.get('confPw')
        if password != conf_password:
            messages.error(request, "Passwords do not match")
            return redirect('signup')
        if User.objects.filter(username=email).exists():
            messages.error(request, "User already exists")
            return redirect('signup')
        User.objects.create_user(username=email, email=email, password=password)
        messages.success(request, "Account created successfully! Please login.")
        return redirect('signin')
    return render(request, 'signup.html')


@csrf_exempt  # Prevent CSRF 403 for login form submissions
def signin_view(request):
    if request.method == 'POST':
        email = request.POST.get('Username')
        password = request.POST.get('Password')
        user = authenticate(request, username=email, password=password)
        if user:
            login(request, user)
            messages.success(request, f"Welcome back, {email}!")
            
            # Check if user has previous vision test data and set brightness
            try:
                vision_data = UserVisionData.objects.get(user=user)
                # Set brightness based on user's stored eye power data (personalized)
                try:
                    from visionapp.brightness_control import set_auto_brightness
                    set_auto_brightness(vision_data.left_d, vision_data.right_d, user_specific=True)
                except Exception as e:
                    print(f"Unable to change system brightness: {e}")
            except UserVisionData.DoesNotExist:
                pass  # New user, no previous data
            
            # Always redirect to home - user can choose to retake test or use previous data
            return redirect('home')
        else:
            messages.error(request, "Invalid credentials")
            return redirect('signin')
    return render(request, 'signin.html')


def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully!")
    return redirect('signin')


from django.contrib.auth.decorators import login_required


@login_required
def profile_view(request):
    """Profile page where user can manually update visual acuity and diopter values."""
    try:
        vision_data = UserVisionData.objects.get(user=request.user)
    except UserVisionData.DoesNotExist:
        vision_data = UserVisionData.objects.create(
            user=request.user,
            left_v=1.0, right_v=1.0,
            left_d=0.0, right_d=0.0
        )

    if request.method == 'POST':
        try:
            vision_data.left_v = float(request.POST.get('left_v', vision_data.left_v))
            vision_data.right_v = float(request.POST.get('right_v', vision_data.right_v))
            vision_data.left_d = float(request.POST.get('left_d', vision_data.left_d))
            vision_data.right_d = float(request.POST.get('right_d', vision_data.right_d))
            vision_data.save()
            messages.success(request, "Vision data updated successfully!")
            try:
                from visionapp.brightness_control import set_auto_brightness
                set_auto_brightness(vision_data.left_d, vision_data.right_d, user_specific=True)
            except Exception:
                pass
            return redirect('profile')
        except (ValueError, TypeError):
            messages.error(request, "Invalid values. Please enter valid numbers.")

    return render(request, 'visionapp/profile.html', {'vision_data': vision_data})


def home(request):
    """Landing page for the vision test."""
    # Check if user has previous vision test data
    has_previous_data = False
    previous_data = None
    if request.user.is_authenticated:
        try:
            previous_data = UserVisionData.objects.get(user=request.user)
            has_previous_data = True
        except UserVisionData.DoesNotExist:
            pass
    
    context = {
        'has_previous_data': has_previous_data,
        'previous_data': previous_data
    }
    return render(request, 'visionapp/home.html', context)


def export_results(request):
    """Export vision test results as PDF or Excel/CSV. Works with URL params or stored user data."""
    format_type = request.GET.get('format', 'pdf').lower()
    
    # Get data from URL params (for non-logged-in users) or from stored data
    if request.GET.get('left_v'):
        # Use URL parameters
        left_v = float(request.GET.get('left_v', 1.0))
        right_v = float(request.GET.get('right_v', 1.0))
        left_d = float(request.GET.get('left_d', 0.0))
        right_d = float(request.GET.get('right_d', 0.0))
        username = request.user.username if request.user.is_authenticated else 'Guest User'
    elif request.user.is_authenticated:
        # Use stored data
        try:
            vision_data = UserVisionData.objects.get(user=request.user)
            left_v = vision_data.left_v
            right_v = vision_data.right_v
            left_d = vision_data.left_d
            right_d = vision_data.right_d
            username = request.user.username
        except UserVisionData.DoesNotExist:
            return HttpResponse("No vision data found to export.", status=404)
    else:
        return HttpResponse("No vision data provided.", status=400)
    
    if format_type == 'pdf':
        return export_results_pdf(left_v, right_v, left_d, right_d, username)
    elif format_type in ['excel', 'csv', 'xlsx']:
        return export_results_excel(left_v, right_v, left_d, right_d, username)
    else:
        return HttpResponse("Invalid format. Use 'pdf' or 'excel'.", status=400)


def export_results_pdf(left_v, right_v, left_d, right_d, username):
    """Generate PDF export for vision test results."""
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from datetime import datetime

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    y = height - 60
    p.setFont("Helvetica-Bold", 20)
    p.drawString(50, y, "Vision Test Results Summary")
    y -= 40

    p.setFont("Helvetica", 12)
    p.drawString(50, y, f"User: {username}")
    y -= 25
    p.drawString(50, y, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    y -= 40

    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "Test Results:")
    y -= 30

    p.setFont("Helvetica", 12)
    p.drawString(70, y, f"Left Eye:")
    p.drawString(200, y, f"Visual Acuity (V) = {left_v}")
    p.drawString(350, y, f"Diopter = {left_d}")
    y -= 25

    p.drawString(70, y, f"Right Eye:")
    p.drawString(200, y, f"Visual Acuity (V) = {right_v}")
    p.drawString(350, y, f"Diopter = {right_d}")
    y -= 40

    # Add recommendations
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Recommendations:")
    y -= 25
    p.setFont("Helvetica", 10)
    
    if abs(left_d) <= 0.5 and abs(right_d) <= 0.5:
        rec = "Your eyesight is good! Keep maintaining healthy eye habits."
    elif abs(left_d) <= 1.5 and abs(right_d) <= 1.5:
        rec = "Mild correction may be needed. Consider checking with an optometrist."
    else:
        rec = "Your eyesight shows significant difference. Professional evaluation is recommended."
    
    # Wrap text if needed
    words = rec.split()
    lines = []
    current_line = []
    for word in words:
        test_line = ' '.join(current_line + [word])
        if p.stringWidth(test_line, "Helvetica", 10) < width - 100:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    if current_line:
        lines.append(' '.join(current_line))
    
    for line in lines:
        p.drawString(70, y, line)
        y -= 18

    y -= 20
    p.setFont("Helvetica-Oblique", 9)
    p.drawString(50, y, "Note: This is a screening tool and not a medical diagnosis.")
    y -= 20
    p.drawString(50, y, "Please consult with a qualified optometrist for professional evaluation.")

    p.showPage()
    p.save()
    buffer.seek(0)

    response = HttpResponse(buffer, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="vision_results_{username}_{datetime.now().strftime("%Y%m%d")}.pdf"'
    return response


def export_results_excel(left_v, right_v, left_d, right_d, username):
    """Generate Excel/CSV export for vision test results."""
    from datetime import datetime
    
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="vision_results_{username}_{datetime.now().strftime("%Y%m%d")}.csv"'

    writer = csv.writer(response)
    writer.writerow(["Vision Test Results"])
    writer.writerow([])
    writer.writerow(["User", username])
    writer.writerow(["Date", datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    writer.writerow([])
    writer.writerow(["Eye", "Visual Acuity (V)", "Diopter"])
    writer.writerow(["Left Eye", left_v, left_d])
    writer.writerow(["Right Eye", right_v, right_d])
    writer.writerow([])
    
    # Add recommendations
    if abs(left_d) <= 0.5 and abs(right_d) <= 0.5:
        rec = "Your eyesight is good! Keep maintaining healthy eye habits."
    elif abs(left_d) <= 1.5 and abs(right_d) <= 1.5:
        rec = "Mild correction may be needed. Consider checking with an optometrist."
    else:
        rec = "Your eyesight shows significant difference. Professional evaluation is recommended."
    
    writer.writerow(["Recommendation", rec])
    writer.writerow([])
    writer.writerow(["Note", "This is a screening tool and not a medical diagnosis."])
    writer.writerow(["", "Please consult with a qualified optometrist for professional evaluation."])

    return response

def start_test_page(request):
    """Direct view for starting the vision test - no redirects, no authentication required."""
    # IMPORTANT: This view allows both authenticated and unauthenticated users
    # No login required - test can be taken by anyone
    # This view should NEVER redirect - always render test page directly
    # Users can retake the test without logging in again
    return render(request, 'visionapp/test_chart.html')

def recommendation_from_diopter(d):
    if abs(d) <= 0.5:
        return "Your eyesight is good! Keep maintaining healthy eye habits."
    elif abs(d) <= 1.5:
        return "Mild correction may be needed. Consider checking with an optometrist."
    else:
        return "Your eyesight shows significant difference. Professional evaluation is recommended."


GOLOVIN_MAP = ['Ш', 'Б', 'М', 'Н', 'К', 'Ы', 'И']
E_SYMBOL_MAP = ['Е', 'М', 'Э', 'Ш']   
LANDOLT_MAP = ['↑', '→', '↓', '←']


def start_test(request):
    """Send all 3 test layouts + chart image URLs (shuffled for variety)."""
    # Charts stay paired with their layouts so the buttons/voice options
    # always match what the user sees on screen. Only letters/numbers
    # are used now (no direction-only E chart).
    # Map each layout to the actual static image so options match what’s shown
    charts_data = [
        {
            "url": "/static/charts/output2.png",  # E chart image
            "layout": [
                ['E'],
                ['F', 'P'],
                ['T', 'O', 'Z'],
                ['L', 'P', 'E', 'D'],
                ['P', 'E', 'C', 'F', 'D'],
                ['E', 'D', 'F', 'C', 'Z', 'P'],
                ['F', 'E', 'L', 'O', 'P', 'Z', 'D'],
                ['D', 'E', 'F', 'P', 'O', 'T', 'E', 'C'],
                ['L', 'E', 'F', 'O', 'D', 'P', 'C', 'T'],
                ['F', 'D', 'P', 'L', 'T', 'C', 'E', 'O'],
                ['P', 'E', 'Z', 'O', 'L', 'C', 'F', 'T', 'D']
            ]
        },
        {
            "url": "/static/charts/output1.png",  # A chart image
            "layout": [
                ['A'],
                ['D', 'F'],
                ['H', 'Z', 'P'],
                ['T', 'X', 'U', 'D'],
                ['Z', 'A', 'D', 'N', 'H'],
                ['P', 'N', 'T', 'U', 'H', 'X'],
                ['U', 'A', 'Z', 'N', 'F', 'D', 'T'],
                ['N', 'P', 'H', 'T', 'A', 'F', 'X', 'U'],
                ['X', 'D', 'F', 'H', 'P', 'T', 'Z', 'A', 'N'],
                ['F', 'A', 'X', 'T', 'D', 'N', 'H', 'U', 'P', 'Z']
            ]
        },
        {
            "url": "/static/charts/output3.png",  # Numbers chart (85 on top)
            "layout": [
                ['8', '5'],
                ['2', '9', '3'],
                ['8', '7', '5', '4'],
                ['6', '3', '9', '5', '2'],
                ['4', '2', '8', '3', '5', '6'],
                ['3', '7', '4', '6', '2', '6', '2'],
                ['4', '2', '7', '5', '9', '8', '5'],
                ['7', '2', '6', '4', '7', '3', '9'],
                ['3', '8', '7', '5', '2', '5', '4'],
                ['4', '2', '1', '9', '1', '2', '4']
            ]
        }
    ]
    
    # Shuffle so start chart varies but layout always matches its image
    charts = random.sample(charts_data, len(charts_data))

    return JsonResponse({
        'charts': charts,
        'v_values': CHART_V_VALUES
    })

@csrf_exempt
def check_answer(request):
    """Check user’s chosen letter and compute V + diopter on failure."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=400)

    eye = request.POST.get('eye', 'left')
    row = int(request.POST.get('row', 0))
    col = int(request.POST.get('col', 0))
    user_choice = request.POST.get('choice', '').strip()
    layout_json = request.POST.get('layout', '')

    if not layout_json:
        return JsonResponse({'error': 'no layout provided'}, status=400)

    layout = json.loads(layout_json)

    try:
        correct = layout[row][col].strip()
    except Exception:
        return JsonResponse({'error': 'invalid row/col'}, status=400)

    if user_choice == correct:
        return JsonResponse({'status': 'correct'})
    else:
      
        v_idx = min(row, len(CHART_V_VALUES) - 1)
        v = CHART_V_VALUES[v_idx]
        d = estimate_diopter_from_v(v)
        rec = recommendation_from_diopter(d)
        return JsonResponse({
            'status': 'wrong',
            'v': v,
            'diopter': d,
            'recommendation': rec,
            'message': f"{eye.capitalize()} eye result: V={v}, Diopter={d}"
        })
from visionapp.brightness_control import set_auto_brightness

@csrf_exempt
def set_brightness_from_voice(request):
    """Set screen brightness based on voice-provided eye power value.
    
    The power_value can be:
    - A visual acuity value (v) like 0.1, 0.2, etc. (will be converted to diopter)
    - A diopter value directly (negative values like -0.5, -1.0, etc.)
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=400)
    
    try:
        power_value = float(request.POST.get('power_value', 0))
        
        # Determine if it's a v value (0.1-2.0) or diopter value (negative)
        # If power_value is between 0 and 2, treat as v value and convert to diopter
        # If power_value is negative, treat as diopter directly
        if 0 <= power_value <= 2.0:
            # It's a visual acuity (v) value, convert to diopter
            diopter = estimate_diopter_from_v(power_value)
        else:
            # Assume it's already a diopter value
            diopter = power_value
        
        # Set brightness using the same logic as auto_brightness
        # Use the diopter value for both eyes (or user can specify separately)
        left_d = diopter
        right_d = diopter
        
        # Set brightness
        try:
            from visionapp.brightness_control import set_auto_brightness
            set_auto_brightness(left_d, right_d, user_specific=True)
            
            # Get the brightness that was set (approximate)
            worse_eye_d = min(left_d, right_d)
            base_brightness = 70
            brightness_adjustment = abs(worse_eye_d) * 8
            brightness = min(100, max(70, base_brightness + brightness_adjustment))
            brightness = round(brightness / 5) * 5
            
            return JsonResponse({
                'success': True,
                'power_value': power_value,
                'diopter': diopter,
                'brightness': int(brightness),
                'message': f'Brightness adjusted to {int(brightness)}% based on power value {power_value} (diopter: {diopter:.2f})'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Could not adjust brightness: {str(e)}'
            }, status=500)
            
    except ValueError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid power value. Please provide a number.'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)


def final_result(request):
    left_v = float(request.GET.get('left_v', 1.0))
    right_v = float(request.GET.get('right_v', 1.0))
    from_login = request.GET.get('from_login', 'false') == 'true'

    # Get diopter values from URL or calculate
    left_d = float(request.GET.get('left_d', estimate_diopter_from_v(left_v)))
    right_d = float(request.GET.get('right_d', estimate_diopter_from_v(right_v)))

    # Save or update vision test data for logged-in users
    if request.user.is_authenticated:
        vision_data, created = UserVisionData.objects.update_or_create(
            user=request.user,
            defaults={
                'left_v': left_v,
                'right_v': right_v,
                'left_d': left_d,
                'right_d': right_d
            }
        )

    # Set brightness based on user's eye power (personalized per user)
    # Only set if not from login, as login already sets it based on stored data
    # Only set if we have actual user profile data (not default/zero values)
    if not from_login and request.user.is_authenticated:
        try:
            # Only set brightness if user has stored profile data with non-zero values
            try:
                vision_data = UserVisionData.objects.get(user=request.user)
                # Only set if we have actual test data (not default values)
                if vision_data.left_d != 0 or vision_data.right_d != 0:
                    set_auto_brightness(vision_data.left_d, vision_data.right_d, user_specific=True)
            except UserVisionData.DoesNotExist:
                # Only set if the current test results are not default values
                if left_d != 0 or right_d != 0:
                    set_auto_brightness(left_d, right_d, user_specific=True)
        except Exception as e:
            print(f"Unable to change system brightness: {e}")

    # Decide visual health
    if abs(left_d) <= 0.5 and abs(right_d) <= 0.5:
        message = "Hi — your eyesight is good. Eat healthy!"
    else:
        message = "Hi — your eyesight needs attention. Please consult an optometrist."

    context = {
        'left_v': left_v, 'right_v': right_v,
        'left_d': left_d, 'right_d': right_d,
        'message': message,
        'from_login': from_login
    }
    return render(request, 'visionapp/final_result.html', context)



from django.conf import settings
from django.shortcuts import render
import os
from PIL import Image, ImageEnhance
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from docx import Document
from docx.shared import Pt
from docx.shared import Pt, RGBColor


def process_document(request):
    if request.method == 'POST':
        # Get diopter values from form or user's stored profile
        left_d = float(request.POST.get('left_d', 0))
        right_d = float(request.POST.get('right_d', 0))
        
        # If values are 0 or not provided, try to get from user's stored profile
        if (left_d == 0 and right_d == 0) and request.user.is_authenticated:
            try:
                vision_data = UserVisionData.objects.get(user=request.user)
                left_d = vision_data.left_d
                right_d = vision_data.right_d
            except UserVisionData.DoesNotExist:
                pass
        
        # Set screen brightness based on user's profile (personalized)
        # ONLY set if user has stored profile data with non-zero values
        if request.user.is_authenticated:
            try:
                from visionapp.brightness_control import set_auto_brightness
                # Get from user profile if form values are default/zero
                if (left_d == 0 and right_d == 0):
                    try:
                        vision_data = UserVisionData.objects.get(user=request.user)
                        left_d = vision_data.left_d
                        right_d = vision_data.right_d
                    except UserVisionData.DoesNotExist:
                        pass
                
                # Only set brightness if we have actual user profile data (not default/zero)
                if (left_d != 0 or right_d != 0):
                    set_auto_brightness(left_d, right_d, user_specific=True)
            except Exception as e:
                print(f"Unable to change system brightness during document processing: {e}")
        
        uploaded = request.FILES.get('document')
        uploads_dir = settings.MEDIA_ROOT
        os.makedirs(uploads_dir, exist_ok=True)

        # Save uploaded file
        in_path = os.path.join(uploads_dir, uploaded.name)
        with open(in_path, 'wb') as f:
            for chunk in uploaded.chunks():
                f.write(chunk)

        # Eye-based enhancement
        avg_d = min(left_d, right_d)
        brightness = 1.0 + min(1.0, (-avg_d) * 0.25)
        font_scale = 1.0 + (-avg_d) * 0.5
        spacing = 1.0 + (-avg_d) * 0.5

        out_name = 'adjusted_' + uploaded.name
        out_path = os.path.join(uploads_dir, out_name)
        ext = os.path.splitext(uploaded.name)[1].lower()

        # ---------------------- IMAGE FILES ----------------------
        if ext in ['.png', '.jpg', '.jpeg']:
            img = Image.open(in_path).convert('RGB')
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(brightness)

            new_size = (int(img.width * font_scale), int(img.height * font_scale))
            img = img.resize(new_size)
            img.save(out_path)

        # ---------------------- TEXT FILES -> PDF ----------------------
        elif ext in ['.txt', '.md']:
            pdf_out = out_path.replace(ext, '.pdf')
            c = canvas.Canvas(pdf_out, pagesize=A4)
            width, height = A4

            base_font = 12 * font_scale
            x, y = 50, height - 50
            c.setFont("Helvetica", base_font)
            # Set text color to black
            from reportlab.lib.colors import black
            c.setFillColor(black)

            with open(in_path, encoding='utf8', errors='ignore') as f:
                for line in f:
                    c.drawString(x, y, line.strip())
                    y -= base_font * 1.5 * spacing

                    if y < 50:  # new page
                        c.showPage()
                        c.setFont("Helvetica", base_font)
                        c.setFillColor(black)
                        y = height - 50

            c.save()
            out_path = pdf_out

        # ---------------------- DOCX FILES ----------------------
        elif ext == '.docx':
            from docx.shared import Inches, Pt, RGBColor
            from docx.enum.text import WD_COLOR_INDEX
            
            doc = Document(in_path)

            for para in doc.paragraphs:
                # PRESERVE original paragraph formatting (indents, alignment, etc.)
                para_format = para.paragraph_format
                
                # Store original indent values BEFORE any modifications
                original_left_indent = para_format.left_indent
                original_right_indent = para_format.right_indent
                original_first_line_indent = para_format.first_line_indent
                original_alignment = para_format.alignment
                original_space_before = para_format.space_before
                original_space_after = para_format.space_after
                
                # Adjust font size and color for each run
                for run in para.runs:
                    # Increase font size
                    if run.font.size:
                        run.font.size = Pt(run.font.size.pt * font_scale)
                    else:
                        run.font.size = Pt(12 * font_scale)

                    # Enhance contrast - set font color to black for maximum readability
                    # This ensures high contrast between text and background
                    run.font.color.rgb = RGBColor(0, 0, 0)
                    
                    # Note: Brightness enhancement for DOCX is handled at the document level
                    # through font size and spacing adjustments. For images/PDFs, brightness
                    # is adjusted directly using image enhancement techniques.

                # ADJUST line spacing while preserving other formatting
                if para_format.line_spacing:
                    # Limit the line spacing to prevent integer overflow
                    new_spacing = float(para_format.line_spacing) * spacing
                    # Cap the value to prevent overflow (max reasonable value)
                    para_format.line_spacing = min(new_spacing, 10.0)
                else:
                    # Cap default line spacing as well
                    para_format.line_spacing = min(1.5 * spacing, 10.0)
                
                # RESTORE original indent values (preserve left and right indents)
                if original_left_indent is not None:
                    para_format.left_indent = original_left_indent
                if original_right_indent is not None:
                    para_format.right_indent = original_right_indent
                if original_first_line_indent is not None:
                    para_format.first_line_indent = original_first_line_indent
                if original_alignment is not None:
                    para_format.alignment = original_alignment
                if original_space_before is not None:
                    para_format.space_before = original_space_before
                if original_space_after is not None:
                    para_format.space_after = original_space_after

            doc.save(out_path)

        # ---------------------- PDF FILES (PRESERVE LAYOUT) ----------------------
        elif ext == '.pdf':
            try:
                from pypdf import PdfReader, PdfWriter
                from reportlab.pdfgen import canvas
                from reportlab.lib.pagesizes import A4
                from reportlab.lib.colors import black
                from reportlab.pdfbase import pdfmetrics
                from reportlab.pdfbase.ttfonts import TTFont
                import io
                
                # Read original PDF
                reader = PdfReader(in_path)
                writer = PdfWriter()
                
                # Process each page to preserve layout
                for page_num, page in enumerate(reader.pages):
                    # Scale the page based on font_scale
                    # This preserves the original layout while scaling
                    page.scale(float(font_scale))
                    writer.add_page(page)
                
                # Save the scaled PDF
                with open(out_path, 'wb') as output_file:
                    writer.write(output_file)
                    
            except Exception as e:
                # Fallback to text extraction if pypdf fails
                print(f"PDF scaling failed, using text extraction: {e}")
                try:
                    import pdfplumber
                    from reportlab.pdfgen import canvas
                    from reportlab.lib.pagesizes import A4
                    from reportlab.lib.colors import black

                    pdf_out = out_path
                    c = canvas.Canvas(pdf_out, pagesize=A4)
                    width, height = A4

                    base_font = 12 * font_scale
                    x, y = 50, height - 50
                    c.setFillColor(black)

                    with pdfplumber.open(in_path) as pdf:
                        for page in pdf.pages:
                            text = page.extract_text() or ""
                            if text:
                                for line in text.split("\n"):
                                    if line.strip():  # Only process non-empty lines
                                        c.setFont("Helvetica", base_font)
                                        c.setFillColor(black)
                                        # Handle long lines by wrapping
                                        if c.stringWidth(line, "Helvetica", base_font) > (width - 100):
                                            words = line.split()
                                            current_line = ""
                                            for word in words:
                                                test_line = current_line + " " + word if current_line else word
                                                if c.stringWidth(test_line, "Helvetica", base_font) <= (width - 100):
                                                    current_line = test_line
                                                else:
                                                    if current_line:
                                                        c.drawString(x, y, current_line)
                                                        y -= base_font * 1.4 * spacing
                                                    current_line = word
                                            if current_line:
                                                c.drawString(x, y, current_line)
                                                y -= base_font * 1.4 * spacing
                                        else:
                                            c.drawString(x, y, line)
                                            y -= base_font * 1.4 * spacing
                                        
                                        if y < 50:
                                            c.showPage()
                                            c.setFillColor(black)
                                            y = height - 50

                    c.save()
                    out_path = pdf_out
                except Exception as pdf_plumber_error:
                    print(f"PDF plumber also failed: {pdf_plumber_error}")
                    # Return error message to user
                    return render(request, 'visionapp/final_result.html', {
                        'message': f"Error processing PDF file: {str(pdf_plumber_error)}",
                        'left_d': left_d,
                        'right_d': right_d
                    })

        # ---------------------- UNSUPPORTED FILES ----------------------
        else:
            return render(request, 'visionapp/final_result.html', {
                'message': f"Unsupported file type: {ext}",
                'left_d': left_d,
                'right_d': right_d
            })

        # ---------------------- OUTPUT FINAL ----------------------
        adjusted_url = settings.MEDIA_URL + os.path.basename(out_path)

        return render(request, 'visionapp/final_result.html', {
            'adjusted_url': adjusted_url,
            'message': "✅ Document adjusted successfully for your eye comfort!",
            'left_d': left_d, 'right_d': right_d,
            'left_v': request.POST.get('left_v', 1.0),
            'right_v': request.POST.get('right_v', 1.0)
        })


import cv2
from django.http import StreamingHttpResponse
from visionapp.distance_calculator import DistanceCalculator
import numpy as np

try:
    import pandas as pd
    _pandas_installed = True
except Exception:
    pd = None
    _pandas_installed = False
def gen_frames():
    """Use the same logic as distance_calculation.calculate_distance() but stream it to HTML."""
    # load calibration file (use pandas if available; otherwise fall back to numpy)
    try:
        if pd is not None:
            distance_df = pd.read_csv('distance_xy.csv')
            distance_pixel_data = distance_df['distance_pixel'].values
            distance_cm_data = distance_df['distance_cm'].values
        else:
            arr = np.loadtxt('distance_xy.csv', delimiter=',', skiprows=1)
            distance_pixel_data = arr[:, 0]
            distance_cm_data = arr[:, 1]
    except Exception:
        # fallback: default calibration data
        distance_pixel_data = np.array([178, 150, 137, 111, 94, 81, 65, 54])
        distance_cm_data = np.array([19, 22, 27, 34, 42, 49, 61, 72])
    eye_screen_distance = DistanceCalculator()
    coff = np.polyfit(distance_pixel_data, distance_cm_data, 2)

    cap = cv2.VideoCapture(0)
    # If mediapipe is not installed or face detection is disabled then provide a
    # static message frame instead of real webcam streaming.
    face_detection_available = (eye_screen_distance.face_detection is not None or 
                                eye_screen_distance.face_detector is not None or
                                eye_screen_distance.haar_face_cascade is not None)
    
    if not face_detection_available:
        # Create a single static frame that indicates face detection is not available.
        h, w = 480, 640
        static_img = np.zeros((h, w, 3), dtype=np.uint8)
        cv2.putText(static_img, 'Face detection not available', (10, 220), cv2.FONT_HERSHEY_SIMPLEX,
                    1.0, (255, 255, 255), 2)
        _, buffer = cv2.imencode('.jpg', static_img)
        frame = buffer.tobytes()
        # Yield the same frame repetitively until the client disconnects.
        while True:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
    while True:
        success, image = cap.read()
        if not success:
            break

        image.flags.writeable = False
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        bbox_list, eyes_list = [], []
        
        # Use appropriate face detection method
        if eye_screen_distance.face_detection is not None:
            # Old mediapipe API
            results = eye_screen_distance.face_detection.process(image_rgb)
            if results.detections:
                for detection in results.detections:
                    bboxc = detection.location_data.relative_bounding_box
                    ih, iw, ic = image.shape
                    bbox = int(bboxc.xmin * iw), int(bboxc.ymin * ih), int(bboxc.width * iw), int(bboxc.height * ih)
                    bbox_list.append(bbox)

                    left_eye = detection.location_data.relative_keypoints[0]
                    right_eye = detection.location_data.relative_keypoints[1]
                    eyes_list.append([(int(left_eye.x * iw), int(left_eye.y * ih)),
                                      (int(right_eye.x * iw), int(right_eye.y * ih))])
        elif eye_screen_distance.face_detector is not None:
            # New mediapipe API - requires different handling (will implement if needed)
            print('New mediapipe API not fully implemented for streaming')
        elif eye_screen_distance.haar_face_cascade is not None:
            # Haar Cascade fallback
            image_gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
            faces = eye_screen_distance.haar_face_cascade.detectMultiScale(image_gray, 1.3, 5)
            ih, iw, ic = image_rgb.shape
            
            for (x, y, w, h) in faces:
                bbox = (x, y, w, h)
                bbox_list.append(bbox)
                
                # Estimate eye positions from face bounding box (approximately 1/3 and 2/3 across, 1/3 down)
                left_eye_x = int(x + w * 0.33)
                left_eye_y = int(y + h * 0.33)
                right_eye_x = int(x + w * 0.67)
                right_eye_y = int(y + h * 0.33)
                
                eyes_list.append([(left_eye_x, left_eye_y), (right_eye_x, right_eye_y)])

        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        for bbox, eye in zip(bbox_list, eyes_list):
            dist_between_eyes = np.sqrt((eye[0][1]-eye[1][1])**2 + (eye[0][0]-eye[1][0])**2)
            a, b, c = coff
            distance_cm = a * dist_between_eyes**2 + b * dist_between_eyes + c

            if distance_cm > 51:
                DistanceCalculator.draw_bbox(image, bbox, eye_screen_distance.colors[2])
                cv2.putText(image, f'{int(distance_cm)} cm - safe',
                            (bbox[0], bbox[1] - 10), cv2.FONT_HERSHEY_PLAIN,
                            2, eye_screen_distance.colors[2], 2)
            else:
                DistanceCalculator.draw_bbox(image, bbox, eye_screen_distance.colors[1])
                cv2.putText(image, f'{int(distance_cm)} cm - too close',
                            (bbox[0], bbox[1] - 10), cv2.FONT_HERSHEY_PLAIN,
                            2, eye_screen_distance.colors[1], 2)

        _, buffer = cv2.imencode('.jpg', image)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

    cap.release()


def video_feed(request):
    """Stream webcam video with safe/too close color logic."""
    return StreamingHttpResponse(gen_frames(), content_type='multipart/x-mixed-replace; boundary=frame')


def view_file(request):
    """Serve file for viewing in browser (inline) or downloading."""
    from django.http import FileResponse, Http404
    from django.conf import settings
    import os
    from urllib.parse import unquote, urlparse, quote
    
    file_path = request.GET.get('file', '')
    download = request.GET.get('download', '')  # Check if download is requested
    
    if not file_path:
        raise Http404("File not specified")
    
    # Handle both full URLs and relative paths
    parsed = urlparse(file_path)
    if parsed.path:
        file_path = parsed.path
    
    # Remove MEDIA_URL prefix if present
    if file_path.startswith(settings.MEDIA_URL):
        file_path = file_path[len(settings.MEDIA_URL):]
    # Remove leading slash if present
    if file_path.startswith('/'):
        file_path = file_path[1:]
    
    # Decode URL encoding
    file_path = unquote(file_path)
    
    # Construct full path
    full_path = os.path.join(settings.MEDIA_ROOT, file_path)
    
    # Security check - ensure file is within MEDIA_ROOT
    full_path = os.path.normpath(full_path)
    media_root = os.path.normpath(settings.MEDIA_ROOT)
    if not full_path.startswith(media_root):
        raise Http404("Invalid file path")
    
    if not os.path.exists(full_path):
        raise Http404("File not found")
    
    # Determine content type and URL for embedding
    ext = os.path.splitext(full_path)[1].lower()
    filename = os.path.basename(full_path)
    content_types = {
        '.pdf': 'application/pdf',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.txt': 'text/plain',
    }
    content_type = content_types.get(ext, 'application/octet-stream')
    
    # Handle download request
    if download == '1':
        response = FileResponse(open(full_path, 'rb'), content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['X-Content-Type-Options'] = 'nosniff'
        return response
    
    # Raw stream request (for iframe/src). Always serve inline to prevent downloads.
    if request.GET.get('raw') == '1':
        response = FileResponse(open(full_path, 'rb'), content_type=content_type)
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        response['X-Content-Type-Options'] = 'nosniff'
        return response
    
    # URL that the browser can request directly (points back to this view with raw=1)
    quoted_path = quote(file_path.replace("\\", "/"))
    file_url = request.build_absolute_uri(f"{request.path}?file={quoted_path}&raw=1")
    download_url = request.build_absolute_uri(f"{request.path}?file={quoted_path}&download=1")
    
    # For text-like files, render them into HTML so clicking "View" never downloads
    if ext in ['.txt', '.docx']:
        text_content = None
        if ext == '.txt':
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                text_content = f.read()
        else:
            try:
                doc = Document(full_path)
                paragraphs = [p.text for p in doc.paragraphs]
                text_content = "\n".join([p for p in paragraphs if p])
            except Exception:
                text_content = None
    
        if text_content is not None:
            return render(request, 'visionapp/view_file.html', {
                'file_name': filename,
                'text_content': text_content,
                'file_url': file_url,
                'download_url': download_url,
                'file_type': ext.lstrip('.'),
                'is_embeddable': False,
            })
    
    # For PDF and images, embed in a viewer page instead of triggering a download
    if ext in ['.pdf', '.png', '.jpg', '.jpeg']:
        return render(request, 'visionapp/view_file.html', {
            'file_name': filename,
            'file_url': file_url,
            'download_url': download_url,
            'file_type': ext.lstrip('.'),
            'is_embeddable': True,
        })
    
    # Fallback: stream inline (browser decides how to handle)
    response = FileResponse(open(full_path, 'rb'), content_type=content_type)
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    response['X-Content-Type-Options'] = 'nosniff'
    return response


# --- PWA camera view and simple frame analysis API ---
from django.views.decorators.csrf import csrf_exempt
import base64, io
from PIL import Image


def pwa_camera_view(request):
    """Render a simple PWA-friendly camera UI that sends frames to the server."""
    return render(request, 'pwa_camera.html')


@csrf_exempt
def analyze_frame(request):
    """Accepts JSON {image: 'data:image/jpeg;base64,...'} and returns distance JSON.

    This endpoint uses the existing `DistanceCalculator` fallback (Haar Cascade)
    to estimate eye distance from a single uploaded frame. It is intentionally
    simple to keep latency low for prototyping.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        payload = json.loads(request.body.decode('utf-8'))
        img_b64 = payload.get('image', '')
        if ',' in img_b64:
            img_b64 = img_b64.split(',', 1)[1]
        img_bytes = base64.b64decode(img_b64)
        img = Image.open(io.BytesIO(img_bytes)).convert('RGB')
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

        # Instantiate DistanceCalculator (uses Haar fallback if mediapipe not available)
        dc = DistanceCalculator()

        # Use Haar Cascade if available (fast, server-side)
        if getattr(dc, 'haar_face_cascade', None) is not None:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = dc.haar_face_cascade.detectMultiScale(gray, 1.3, 5)
            if len(faces) == 0:
                return JsonResponse({'error': 'no_face'})
            x, y, w, h = faces[0]
            left = (int(x + w * 0.33), int(y + h * 0.33))
            right = (int(x + w * 0.67), int(y + h * 0.33))
            dist_px = np.sqrt((left[0] - right[0]) ** 2 + (left[1] - right[1]) ** 2)
            # Use calibration CSV if available; otherwise use defaults
            try:
                df = None
                if pd is not None:
                    df = pd.read_csv('distance_xy.csv')
                if df is not None:
                    px = df['distance_pixel'].values
                    cm = df['distance_cm'].values
                else:
                    px = np.array([178, 150, 137, 111, 94, 81, 65, 54])
                    cm = np.array([19, 22, 27, 34, 42, 49, 61, 72])
                a, b, c = np.polyfit(px, cm, 2)
                dist_cm = int(a * dist_px ** 2 + b * dist_px + c)
            except Exception:
                dist_cm = None

            return JsonResponse({'distance': dist_cm, 'note': 'haar'})

        # If no detector available
        return JsonResponse({'error': 'no_detector'})
    except Exception as e:
        return JsonResponse({'error': str(e)})


# ==================== AI EXAM PREPARATION VIEWS ====================

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import models
from datetime import datetime, timedelta
import json

from .models import (
    StudyMaterial, Flashcard, Quiz, QuizQuestion, 
    QuizAttempt, StudySession, LearningResource
)
from .ai_examprep import (
    extract_text_from_document, summarize_content, extract_key_concepts,
    generate_flashcards, generate_quiz_questions, recommend_resources
)


@login_required(login_url='/signin/')
def examprep_dashboard(request):
    """Main dashboard for exam preparation."""
    user = request.user
    
    # Get statistics
    total_materials = StudyMaterial.objects.filter(user=user).count()
    total_flashcards = Flashcard.objects.filter(user=user).count()
    total_quizzes = Quiz.objects.filter(user=user).count()
    total_attempts = QuizAttempt.objects.filter(user=user).count()
    
    # Get recent activity
    recent_materials = StudyMaterial.objects.filter(user=user)[:5]
    recent_attempts = QuizAttempt.objects.filter(user=user).select_related('quiz')[:5]
    
    # Calculate average score
    avg_score = 0
    if total_attempts > 0:
        avg_score = QuizAttempt.objects.filter(user=user).aggregate(
            avg=models.Avg('percentage')
        )['avg'] or 0
    
    # Get flashcards due for review
    due_flashcards = Flashcard.objects.filter(
        user=user,
        next_review__lte=timezone.now()
    ).count()
    
    # Get study streak
    study_dates = StudySession.objects.filter(
        user=user
    ).values_list('date', flat=True).distinct().order_by('-date')
    
    streak = 0
    today = timezone.now().date()
    for i, date in enumerate(study_dates):
        if date == today - timedelta(days=i):
            streak += 1
        else:
            break
    
    context = {
        'total_materials': total_materials,
        'total_flashcards': total_flashcards,
        'total_quizzes': total_quizzes,
        'total_attempts': total_attempts,
        'avg_score': round(avg_score, 1),
        'due_flashcards': due_flashcards,
        'streak': streak,
        'recent_materials': recent_materials,
        'recent_attempts': recent_attempts,
    }
    return render(request, 'visionapp/examprep/dashboard.html', context)


@login_required(login_url='/signin/')
def upload_study_material(request):
    """Upload and process study materials."""
    if request.method == 'POST':
        title = request.POST.get('title')
        uploaded_file = request.FILES.get('document')
        
        if not uploaded_file:
            messages.error(request, 'Please select a file to upload.')
            return redirect('upload_study_material')
        
        # Save the file
        material = StudyMaterial.objects.create(
            user=request.user,
            title=title or uploaded_file.name,
            file=uploaded_file
        )
        
        # Process the document
        try:
            file_path = material.file.path
            extracted_text = extract_text_from_document(file_path)
            
            if extracted_text:
                material.extracted_text = extracted_text
                material.summary = summarize_content(extracted_text, num_sentences=3)
                material.key_concepts = extract_key_concepts(extracted_text, num_concepts=10)
                material.save()
                
                # Generate flashcards automatically
                flashcards_data = generate_flashcards(extracted_text, num_cards=10)
                for card_data in flashcards_data:
                    Flashcard.objects.create(
                        user=request.user,
                        material=material,
                        question=card_data['question'],
                        answer=card_data['answer'],
                        context=card_data.get('context', '')
                    )
                
                # Generate quiz automatically
                quiz_questions_data = generate_quiz_questions(extracted_text, num_questions=5)
                if quiz_questions_data:
                    quiz = Quiz.objects.create(
                        user=request.user,
                        material=material,
                        title=f"Quiz: {material.title}",
                        description=f"Auto-generated quiz based on {material.title}",
                        is_auto_generated=True
                    )
                    
                    for i, q_data in enumerate(quiz_questions_data):
                        QuizQuestion.objects.create(
                            quiz=quiz,
                            question_type=q_data['type'],
                            question_text=q_data['question'],
                            options=q_data.get('options', []),
                            correct_answer=str(q_data['correct_answer']),
                            explanation=q_data.get('explanation', ''),
                            order=i
                        )
                
                messages.success(
                    request, 
                    f'Material uploaded and processed successfully! '
                    f'Generated {len(flashcards_data)} flashcards and {len(quiz_questions_data)} quiz questions.'
                )
            else:
                messages.warning(request, 'File uploaded but could not extract text.')
            
            return redirect('examprep_dashboard')
            
        except Exception as e:
            messages.error(request, f'Error processing document: {str(e)}')
            return redirect('upload_study_material')
    
    return render(request, 'visionapp/examprep/upload.html')


@login_required(login_url='/signin/')
def view_flashcards(request, material_id=None):
    """View and review flashcards."""
    user = request.user
    
    if material_id:
        material = get_object_or_404(StudyMaterial, id=material_id, user=user)
        flashcards = Flashcard.objects.filter(user=user, material=material)
    else:
        material = None
        flashcards = Flashcard.objects.filter(user=user)
    
    # Filter by mastery level if requested
    mastery_filter = request.GET.get('mastery')
    if mastery_filter:
        flashcards = flashcards.filter(mastery_level=int(mastery_filter))
    
    # Get due flashcards
    show_due_only = request.GET.get('due') == '1'
    if show_due_only:
        flashcards = flashcards.filter(
            models.Q(next_review__lte=timezone.now()) | models.Q(next_review__isnull=True)
        )
    
    flashcards = flashcards.order_by('mastery_level', '-created_at')
    
    context = {
        'flashcards': flashcards,
        'material': material,
        'total_count': flashcards.count(),
        'due_count': Flashcard.objects.filter(
            user=user,
            next_review__lte=timezone.now()
        ).count(),
    }
    return render(request, 'visionapp/examprep/flashcards.html', context)


@login_required(login_url='/signin/')
def create_flashcard(request):
    """Create a new flashcard manually."""
    if request.method == 'POST':
        question = request.POST.get('question')
        answer = request.POST.get('answer')
        material_id = request.POST.get('material_id')
        
        material = None
        if material_id:
            material = get_object_or_404(StudyMaterial, id=material_id, user=request.user)
        
        Flashcard.objects.create(
            user=request.user,
            material=material,
            question=question,
            answer=answer
        )
        
        messages.success(request, 'Flashcard created successfully!')
        
        if material:
            return redirect('view_flashcards', material_id=material.id)
        return redirect('view_flashcards')
    
    materials = StudyMaterial.objects.filter(user=request.user)
    return render(request, 'visionapp/examprep/create_flashcard.html', {'materials': materials})


@login_required(login_url='/signin/')
@csrf_exempt
def update_flashcard_mastery(request):
    """AJAX endpoint to update flashcard mastery level."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    try:
        data = json.loads(request.body)
        flashcard_id = data.get('flashcard_id')
        mastery_level = data.get('mastery_level')
        
        flashcard = get_object_or_404(Flashcard, id=flashcard_id, user=request.user)
        flashcard.mastery_level = mastery_level
        flashcard.review_count += 1
        flashcard.last_reviewed = timezone.now()
        
        # Calculate next review date based on mastery (spaced repetition)
        days_until_next = [1, 3, 7, 14, 30][min(mastery_level, 4)]
        flashcard.next_review = timezone.now() + timedelta(days=days_until_next)
        
        flashcard.save()
        
        # Log study session
        StudySession.objects.create(
            user=request.user,
            session_type='flashcard_review',
            duration=1,
            items_reviewed=1
        )
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required(login_url='/signin/')
def take_quiz(request, quiz_id=None):
    """Take a quiz."""
    user = request.user
    
    if quiz_id:
        quiz = get_object_or_404(Quiz, id=quiz_id, user=user)
    else:
        # Get a random quiz
        quiz = Quiz.objects.filter(user=user).order_by('?').first()
        if not quiz:
            messages.info(request, 'No quizzes available. Upload study materials to generate quizzes.')
            return redirect('examprep_dashboard')
    
    questions = quiz.questions.all()
    
    context = {
        'quiz': quiz,
        'questions': questions,
        'total_questions': questions.count(),
    }
    return render(request, 'visionapp/examprep/quiz.html', context)


@login_required(login_url='/signin/')
def submit_quiz(request):
    """Submit quiz answers and show results."""
    if request.method != 'POST':
        return redirect('examprep_dashboard')
    
    quiz_id = request.POST.get('quiz_id')
    quiz = get_object_or_404(Quiz, id=quiz_id, user=request.user)
    questions = quiz.questions.all()
    
    score = 0
    total_questions = questions.count()
    answers = {}
    results = []
    
    start_time = request.POST.get('start_time')
    time_taken = 0
    if start_time:
        try:
            start_dt = datetime.fromisoformat(start_time)
            time_taken = int((timezone.now() - start_dt).total_seconds())
        except:
            pass
    
    for question in questions:
        answer_key = f'question_{question.id}'
        user_answer = request.POST.get(answer_key, '')
        answers[str(question.id)] = user_answer
        
        is_correct = user_answer.lower().strip() == question.correct_answer.lower().strip()
        if is_correct:
            score += 1
        
        results.append({
            'question': question,
            'user_answer': user_answer,
            'is_correct': is_correct,
        })
    
    percentage = (score / total_questions * 100) if total_questions > 0 else 0
    
    # Save attempt
    attempt = QuizAttempt.objects.create(
        user=request.user,
        quiz=quiz,
        score=score,
        total_questions=total_questions,
        percentage=percentage,
        time_taken=time_taken,
        answers=answers
    )
    
    # Log study session
    StudySession.objects.create(
        user=request.user,
        session_type='quiz',
        duration=max(1, time_taken // 60),
        items_reviewed=total_questions
    )
    
    context = {
        'quiz': quiz,
        'attempt': attempt,
        'score': score,
        'total_questions': total_questions,
        'percentage': round(percentage, 1),
        'time_taken': time_taken,
        'results': results,
    }
    return render(request, 'visionapp/examprep/quiz_results.html', context)


@login_required(login_url='/signin/')
def quiz_history(request):
    """View quiz attempt history."""
    attempts = QuizAttempt.objects.filter(
        user=request.user
    ).select_related('quiz').order_by('-completed_at')
    
    context = {
        'attempts': attempts,
    }
    return render(request, 'visionapp/examprep/history.html', context)


@login_required(login_url='/signin/')
def learning_resources(request):
    """Get AI-recommended learning resources."""
    user = request.user
    
    # Get user's materials and extract topics
    materials = StudyMaterial.objects.filter(user=user)
    all_topics = []
    for material in materials:
        all_topics.extend(material.key_concepts)
    
    # Get weak areas from quiz attempts
    recent_attempts = QuizAttempt.objects.filter(
        user=user,
        percentage__lt=70
    ).select_related('quiz')[:10]
    
    weak_topics = []
    for attempt in recent_attempts:
        if attempt.quiz.material:
            weak_topics.extend(attempt.quiz.material.key_concepts)
    
    # Combine topics
    topics = list(set(all_topics + weak_topics))
    
    # Get recommendations
    if topics:
        recommendations = recommend_resources(topics)
    else:
        recommendations = []
    
    # Get saved resources
    saved_resources = LearningResource.objects.all()[:20]
    
    context = {
        'recommendations': recommendations,
        'saved_resources': saved_resources,
        'topics': topics,
        'weak_topics': list(set(weak_topics)),
    }
    return render(request, 'visionapp/examprep/resources.html', context)


@login_required(login_url='/signin/')
def study_progress(request):
    """View study progress analytics."""
    user = request.user
    
    # Get study sessions for the last 30 days
    thirty_days_ago = timezone.now() - timedelta(days=30)
    sessions = StudySession.objects.filter(
        user=user,
        date__gte=thirty_days_ago
    )
    
    # Calculate daily study time
    daily_stats = {}
    for i in range(30):
        date = (timezone.now() - timedelta(days=i)).date()
        daily_stats[date.isoformat()] = 0
    
    for session in sessions:
        date_key = session.date.isoformat()
        if date_key in daily_stats:
            daily_stats[date_key] += session.duration
    
    # Get quiz performance over time
    quiz_attempts = QuizAttempt.objects.filter(
        user=user
    ).order_by('completed_at')[:20]
    
    quiz_scores = [
        {'date': attempt.completed_at.isoformat(), 'percentage': attempt.percentage}
        for attempt in quiz_attempts
    ]
    
    # Get flashcard mastery distribution
    mastery_dist = Flashcard.objects.filter(user=user).values('mastery_level').annotate(
        count=models.Count('id')
    )
    
    mastery_data = {i: 0 for i in range(6)}
    for item in mastery_dist:
        mastery_data[item['mastery_level']] = item['count']
    
    # Calculate total study time
    total_study_time = sessions.aggregate(total=models.Sum('duration'))['total'] or 0
    
    context = {
        'daily_stats': daily_stats,
        'quiz_scores': quiz_scores,
        'mastery_data': mastery_data,
        'total_study_time': total_study_time,
        'total_sessions': sessions.count(),
    }
    return render(request, 'visionapp/examprep/progress.html', context)


@login_required(login_url='/signin/')
def study_materials_list(request):
    """List all study materials."""
    materials = StudyMaterial.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'materials': materials,
    }
    return render(request, 'visionapp/examprep/materials_list.html', context)


@login_required(login_url='/signin/')
def delete_study_material(request, material_id):
    """Delete a study material and associated data."""
    material = get_object_or_404(StudyMaterial, id=material_id, user=request.user)
    
    if request.method == 'POST':
        material.delete()
        messages.success(request, 'Study material deleted successfully.')
        return redirect('study_materials_list')
    
    return render(request, 'visionapp/examprep/confirm_delete.html', {'material': material})


# ==================== AI STUDY PLANNER VIEWS ====================

from .models import StudyPlan, StudySchedule
from .ai_examprep import StudyPlanner


@login_required(login_url='/signin/')
def study_planner(request):
    """AI Study Planner - Create and manage study plans."""
    user = request.user
    
    # Get user's active study plans
    study_plans = StudyPlan.objects.filter(user=user, is_active=True).order_by('-created_at')
    
    # Get weak topics from quiz attempts for AI recommendations
    weak_topics = []
    recent_attempts = QuizAttempt.objects.filter(user=user, percentage__lt=70).select_related('quiz')[:10]
    for attempt in recent_attempts:
        if attempt.quiz.material:
            weak_topics.extend(attempt.quiz.material.key_concepts)
    weak_topics = list(set(weak_topics))[:10]  # Top 10 weak topics
    
    context = {
        'study_plans': study_plans,
        'weak_topics': weak_topics,
    }
    return render(request, 'visionapp/examprep/study_planner.html', context)


@login_required(login_url='/signin/')
def create_study_plan(request):
    """Create a new AI-generated study plan."""
    if request.method == 'POST':
        title = request.POST.get('title')
        exam_date = request.POST.get('exam_date')
        syllabus = request.POST.get('syllabus')
        daily_hours = float(request.POST.get('daily_hours', 2.0))
        
        # Create study plan
        study_plan = StudyPlan.objects.create(
            user=request.user,
            title=title,
            exam_date=exam_date,
            syllabus=syllabus,
            daily_study_hours=daily_hours
        )
        
        # Get weak topics for prioritization
        weak_topics = []
        recent_attempts = QuizAttempt.objects.filter(
            user=request.user, percentage__lt=70
        ).select_related('quiz')[:10]
        for attempt in recent_attempts:
            if attempt.quiz.material:
                weak_topics.extend(attempt.quiz.material.key_concepts)
        weak_topics = list(set(weak_topics))
        
        # Generate AI schedule
        schedule_data = StudyPlanner.generate_study_schedule(
            syllabus=syllabus,
            exam_date=exam_date,
            daily_hours=daily_hours,
            weak_topics=weak_topics
        )
        
        # Save schedule to database
        for day_data in schedule_data:
            for item in day_data['items']:
                StudySchedule.objects.create(
                    study_plan=study_plan,
                    date=day_data['date'],
                    topic=item['topic'],
                    description=item['description'],
                    estimated_minutes=item['estimated_minutes']
                )
        
        messages.success(request, f'Study plan "{title}" created successfully with {len(schedule_data)} days of schedule!')
        return redirect('view_study_plan', plan_id=study_plan.id)
    
    return render(request, 'visionapp/examprep/create_study_plan.html')


@login_required(login_url='/signin/')
def view_study_plan(request, plan_id):
    """View a specific study plan with daily schedule."""
    study_plan = get_object_or_404(StudyPlan, id=plan_id, user=request.user)
    schedule_items = study_plan.schedule_items.all()
    
    # Group by date
    from collections import defaultdict
    schedule_by_date = defaultdict(list)
    for item in schedule_items:
        schedule_by_date[item.date].append(item)
    
    # Calculate progress
    total_items = schedule_items.count()
    completed_items = schedule_items.filter(is_completed=True).count()
    progress_percentage = (completed_items / total_items * 100) if total_items > 0 else 0
    
    # Get upcoming items
    from datetime import date
    upcoming_items = schedule_items.filter(date__gte=date.today(), is_completed=False).order_by('date')[:7]
    
    context = {
        'study_plan': study_plan,
        'schedule_by_date': dict(schedule_by_date),
        'total_items': total_items,
        'completed_items': completed_items,
        'progress_percentage': round(progress_percentage, 1),
        'upcoming_items': upcoming_items,
    }
    return render(request, 'visionapp/examprep/view_study_plan.html', context)


@login_required(login_url='/signin/')
def update_schedule_item(request, item_id):
    """Mark schedule item as complete or skipped."""
    item = get_object_or_404(StudySchedule, id=item_id, study_plan__user=request.user)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('notes', '')
        
        if action == 'complete':
            item.is_completed = True
            item.is_skipped = False
            item.completion_notes = notes
            messages.success(request, f'Completed: {item.topic}')
        elif action == 'skip':
            item.is_skipped = True
            item.is_completed = False
            item.completion_notes = notes
            messages.warning(request, f'Skipped: {item.topic} - AI will reschedule this topic')
            
            # Get weak topics for rescheduling priority
            weak_topics = []
            recent_attempts = QuizAttempt.objects.filter(
                user=request.user, percentage__lt=70
            ).select_related('quiz')[:10]
            for attempt in recent_attempts:
                if attempt.quiz.material:
                    weak_topics.extend(attempt.quiz.material.key_concepts)
            
            # Reschedule skipped topic - create proper schedule structure
            schedule_qs = StudySchedule.objects.filter(study_plan=item.study_plan)
            
            # Build schedule grouped by date
            from collections import defaultdict
            schedule_by_date = defaultdict(list)
            for s in schedule_qs:
                schedule_by_date[s.date].append({
                    'topic': s.topic,
                    'description': s.description,
                    'estimated_minutes': s.estimated_minutes
                })
            
            # Convert to list format expected by StudyPlanner
            schedule_list = []
            for date_key, items in schedule_by_date.items():
                total_minutes = sum(i['estimated_minutes'] for i in items)
                schedule_list.append({
                    'date': date_key.isoformat() if hasattr(date_key, 'isoformat') else str(date_key),
                    'items': items,
                    'total_minutes': total_minutes
                })
            
            adjusted_schedule = StudyPlanner.adjust_schedule_for_skipped_topics(
                schedule_list,
                [item.topic],
                weak_topics
            )
            
            # Add rescheduled items
            if adjusted_schedule:
                for day_data in adjusted_schedule[-2:]:  # Add last 2 days (rescheduled)
                    for schedule_item in day_data['items']:
                        if any(st.lower() in schedule_item['topic'].lower() for st in [item.topic]):
                            from datetime import date as dt_date
                            date_val = day_data['date']
                            if isinstance(date_val, str):
                                date_val = dt_date.fromisoformat(date_val)
                            StudySchedule.objects.create(
                                study_plan=item.study_plan,
                                date=date_val,
                                topic=schedule_item['topic'],
                                description=schedule_item['description'] + " (Rescheduled)",
                                estimated_minutes=schedule_item['estimated_minutes']
                            )
        
        item.save()
        return redirect('view_study_plan', plan_id=item.study_plan.id)
    
    return render(request, 'visionapp/examprep/update_schedule_item.html', {'item': item})


@login_required(login_url='/signin/')
def delete_study_plan(request, plan_id):
    """Delete a study plan."""
    study_plan = get_object_or_404(StudyPlan, id=plan_id, user=request.user)
    
    if request.method == 'POST':
        study_plan.delete()
        messages.success(request, 'Study plan deleted successfully.')
        return redirect('study_planner')
    
    return render(request, 'visionapp/examprep/confirm_delete_plan.html', {'study_plan': study_plan})


# ==================== PREVIOUS EXAM PATTERN & SMART REVISION VIEWS ====================

from .models import PreviousExamQuestion, SmartRevision, RevisionSession
from .ai_examprep import ExamPatternAnalyzer, SpacedRepetitionEngine


@login_required(login_url='/signin/')
def previous_exam_questions(request):
    """View and manage previous exam questions with pattern analysis."""
    user = request.user
    
    # Get filter parameters
    subject = request.GET.get('subject', '')
    year = request.GET.get('year', '')
    
    questions = PreviousExamQuestion.objects.filter(user=user)
    if subject:
        questions = questions.filter(subject__icontains=subject)
    if year:
        questions = questions.filter(year=year)
    
    questions = questions.order_by('-year', 'subject')
    
    # Get unique subjects and years for filters
    subjects = PreviousExamQuestion.objects.filter(user=user).values_list('subject', flat=True).distinct()
    years = PreviousExamQuestion.objects.filter(user=user).values_list('year', flat=True).distinct().order_by('-year')
    
    # Generate pattern analysis
    questions_data = list(questions.values())
    pattern_report = ExamPatternAnalyzer.generate_pattern_report(questions_data)
    
    context = {
        'questions': questions,
        'subjects': subjects,
        'years': years,
        'selected_subject': subject,
        'selected_year': year,
        'pattern_report': pattern_report,
    }
    return render(request, 'visionapp/examprep/previous_exam_questions.html', context)


@login_required(login_url='/signin/')
def add_previous_exam_question(request):
    """Add a new previous exam question."""
    if request.method == 'POST':
        PreviousExamQuestion.objects.create(
            user=request.user,
            subject=request.POST.get('subject'),
            year=request.POST.get('year'),
            question_type=request.POST.get('question_type'),
            question_text=request.POST.get('question_text'),
            topic=request.POST.get('topic'),
            marks=request.POST.get('marks', 5),
            difficulty_level=request.POST.get('difficulty_level', 3),
            frequency_count=request.POST.get('frequency_count', 1)
        )
        messages.success(request, 'Previous exam question added successfully!')
        return redirect('previous_exam_questions')
    
    return render(request, 'visionapp/examprep/add_previous_question.html')


@login_required(login_url='/signin/')
def smart_revision_dashboard(request):
    """Smart revision dashboard with spaced repetition."""
    user = request.user
    from datetime import date
    
    # Get due revisions for today
    revisions = SmartRevision.objects.filter(user=user, is_mastered=False)
    revisions_data = list(revisions.values())
    
    due_today = SpacedRepetitionEngine.get_due_revisions(revisions_data, date.today())
    due_count = len(due_today)
    
    # Get upcoming revisions
    upcoming_schedule = SpacedRepetitionEngine.get_revision_schedule(revisions_data, 14)
    
    # Get mastered topics
    mastered_count = SmartRevision.objects.filter(user=user, is_mastered=True).count()
    total_count = revisions.count() + mastered_count
    
    # Get revision streak
    recent_sessions = RevisionSession.objects.filter(
        revision__user=user,
        reviewed_at__gte=date.today() - timedelta(days=7)
    ).count()
    
    context = {
        'due_revisions': revisions.filter(next_review__lte=date.today()).order_by('next_review')[:10],
        'due_count': due_count,
        'upcoming_schedule': upcoming_schedule,
        'mastered_count': mastered_count,
        'total_count': total_count,
        'mastery_percentage': round(mastered_count / total_count * 100, 1) if total_count > 0 else 0,
        'recent_sessions': recent_sessions,
    }
    return render(request, 'visionapp/examprep/smart_revision.html', context)


@login_required(login_url='/signin/')
def add_revision_topic(request):
    """Add a new topic for smart revision."""
    if request.method == 'POST':
        from datetime import date, timedelta
        
        SmartRevision.objects.create(
            user=request.user,
            topic=request.POST.get('topic'),
            subject=request.POST.get('subject', ''),
            next_review=date.today(),
            interval_days=1,
            ease_factor=2.5
        )
        messages.success(request, 'Topic added to smart revision system!')
        return redirect('smart_revision_dashboard')
    
    return render(request, 'visionapp/examprep/add_revision_topic.html')


@login_required(login_url='/signin/')
def review_topic(request, revision_id):
    """Review a topic and update spaced repetition schedule."""
    revision = get_object_or_404(SmartRevision, id=revision_id, user=request.user)
    
    if request.method == 'POST':
        quality = int(request.POST.get('quality', 3))
        time_spent = int(request.POST.get('time_spent', 0))
        notes = request.POST.get('notes', '')
        
        # Record the session
        RevisionSession.objects.create(
            revision=revision,
            quality=quality,
            time_spent_minutes=time_spent,
            notes=notes
        )
        
        # Update revision using SM-2 algorithm
        new_interval, new_ease = SpacedRepetitionEngine.calculate_next_review(
            quality=quality,
            current_interval=revision.interval_days,
            ease_factor=revision.ease_factor
        )
        
        from datetime import date, timedelta
        revision.interval_days = new_interval
        revision.ease_factor = new_ease
        revision.review_count += 1
        revision.last_reviewed = date.today()
        revision.next_review = date.today() + timedelta(days=new_interval)
        
        # Mark as mastered if quality is consistently high
        recent_sessions = revision.sessions.order_by('-reviewed_at')[:3]
        if len(recent_sessions) >= 3 and all(s.quality >= 4 for s in recent_sessions):
            revision.is_mastered = True
            messages.success(request, f'Excellent! {revision.topic} is now marked as mastered!')
        else:
            messages.success(request, f'Review recorded! Next review in {new_interval} days.')
        
        revision.save()
        return redirect('smart_revision_dashboard')
    
    # Get mastery info
    sessions = list(revision.sessions.values())
    mastery_info = SpacedRepetitionEngine.estimate_mastery_level(sessions)
    
    context = {
        'revision': revision,
        'mastery_info': mastery_info,
    }
    return render(request, 'visionapp/examprep/review_topic.html', context)


@login_required(login_url='/signin/')
def exam_pattern_analysis(request):
    """Detailed exam pattern analysis and predictions."""
    user = request.user
    
    questions = PreviousExamQuestion.objects.filter(user=user)
    questions_data = list(questions.values())
    
    # Get pattern report
    pattern_report = ExamPatternAnalyzer.generate_pattern_report(questions_data)
    
    # Get top predictions
    predictions = ExamPatternAnalyzer.predict_important_topics(questions_data, 15)
    
    context = {
        'pattern_report': pattern_report,
        'predictions': predictions,
        'total_questions': questions.count(),
    }
    return render(request, 'visionapp/examprep/exam_pattern_analysis.html', context)


# ==================== AI DOUBT SOLVER VIEWS ====================

from .models import DoubtSession, DoubtMessage
from .ai_examprep import DoubtSolverAI


@login_required(login_url='/signin/')
def doubt_solver(request):
    """AI Doubt Solver - Chat interface for students."""
    user = request.user
    
    # Get active sessions
    sessions = DoubtSession.objects.filter(user=user, is_active=True).order_by('-updated_at')
    
    context = {
        'sessions': sessions,
    }
    return render(request, 'visionapp/examprep/doubt_solver.html', context)


@login_required(login_url='/signin/')
def doubt_chat(request, session_id=None):
    """Chat interface for doubt solving."""
    user = request.user
    
    if session_id:
        session = get_object_or_404(DoubtSession, id=session_id, user=user)
    else:
        # Create new session
        session = DoubtSession.objects.create(user=user, title='New Doubt Session')
        return redirect('doubt_chat', session_id=session.id)
    
    if request.method == 'POST':
        message_text = request.POST.get('message', '')
        image = request.FILES.get('image')
        
        # Save user message
        user_message = DoubtMessage.objects.create(
            session=session,
            message_type='user',
            text=message_text,
            image=image
        )
        
        # Process image if uploaded
        image_analysis = None
        if image:
            image_path = user_message.image.path
            image_analysis = DoubtSolverAI.analyze_question_image(image_path)
        
        # Generate AI response
        question = image_analysis['extracted_text'] if image_analysis else message_text
        subject = image_analysis['subject'] if image_analysis else DoubtSolverAI._detect_subject(message_text)
        question_type = image_analysis['question_type'] if image_analysis else DoubtSolverAI._detect_question_type(message_text)
        
        # Generate explanation
        explanation = DoubtSolverAI.generate_explanation(question, question_type, subject)
        
        # Add study tips
        study_tips = DoubtSolverAI.get_study_tips(subject)
        tips_text = "\n\n### 💡 Study Tips\n" + "\n".join([f"• {tip}" for tip in study_tips[:3]])
        
        # Full AI response
        ai_response = explanation + tips_text
        
        # Save AI message
        DoubtMessage.objects.create(
            session=session,
            message_type='ai',
            text=ai_response
        )
        
        # Update session
        if not session.title or session.title == 'New Doubt Session':
            session.title = question[:50] + '...' if len(question) > 50 else question
        if not session.subject:
            session.subject = subject
        session.save()
        
        # If AJAX request, return JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'ai_response': ai_response,
                'subject': subject,
                'question_type': question_type
            })
        
        return redirect('doubt_chat', session_id=session.id)
    
    messages = session.messages.all()
    
    context = {
        'session': session,
        'messages': messages,
    }
    return render(request, 'visionapp/examprep/doubt_chat.html', context)


@login_required(login_url='/signin/')
def delete_doubt_session(request, session_id):
    """Delete a doubt session."""
    session = get_object_or_404(DoubtSession, id=session_id, user=request.user)
    
    if request.method == 'POST':
        session.delete()
        messages.success(request, 'Chat session deleted.')
        return redirect('doubt_solver')
    
    return render(request, 'visionapp/examprep/confirm_delete_doubt.html', {'session': session})


# ==================== AUTO NOTES GENERATOR VIEWS ====================

@login_required(login_url='/signin/')
def auto_notes_generator(request):
    """Main page for Auto Notes Generator."""
    notes = GeneratedNotes.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'visionapp/examprep/auto_notes.html', {'notes': notes})


@login_required(login_url='/signin/')
def upload_notes_file(request):
    """Handle file upload and process it."""
    if request.method != 'POST':
        return redirect('auto_notes_generator')
    
    if 'file' not in request.FILES:
        messages.error(request, 'Please select a file to upload.')
        return redirect('auto_notes_generator')
    
    uploaded_file = request.FILES['file']
    
    # Determine file type
    file_name = uploaded_file.name.lower()
    if file_name.endswith('.pdf'):
        file_type = 'pdf'
    elif file_name.endswith('.docx'):
        file_type = 'docx'
    elif file_name.endswith('.txt'):
        file_type = 'txt'
    elif file_name.endswith(('.png', '.jpg', '.jpeg')):
        file_type = 'image'
    else:
        messages.error(request, 'Unsupported file format. Please upload PDF, DOCX, TXT, or image files.')
        return redirect('auto_notes_generator')
    
    # Create notes entry
    notes = GeneratedNotes.objects.create(
        user=request.user,
        title=request.POST.get('title', file_name),
        original_file=uploaded_file,
        file_type=file_type,
        processing_status='processing'
    )
    
    # Process the file
    try:
        from visionapp.ai_examprep import AutoNotesGenerator
        import traceback
        
        # Extract text
        file_path = notes.original_file.path
        print(f"Processing file: {file_path}, type: {file_type}")
        
        extracted_text = AutoNotesGenerator.extract_text_from_file(file_path, file_type)
        print(f"Extracted text length: {len(extracted_text) if extracted_text else 0}")
        
        if not extracted_text:
            notes.processing_status = 'failed'
            notes.save()
            messages.error(request, 'Could not extract text from the file. The file might be empty, corrupted, or in an unsupported format.')
            return redirect('auto_notes_generator')
        
        # Clean and store extracted text
        cleaned_text = AutoNotesGenerator.clean_text(extracted_text)
        notes.extracted_text = cleaned_text[:10000]  # Limit stored text
        
        # Generate short notes
        notes_data = AutoNotesGenerator.generate_short_notes(cleaned_text)
        notes.short_notes = notes_data.get('summary', '')
        notes.key_points = notes_data.get('key_points', [])
        notes.important_definitions = notes_data.get('definitions', [])
        notes.formulas = notes_data.get('formulas', [])
        
        # Generate mind map
        mind_map_data = AutoNotesGenerator.generate_mind_map(extracted_text, notes_data)
        notes.mind_map_data = mind_map_data
        
        # Generate SVG
        mind_map_svg = AutoNotesGenerator.generate_mind_map_svg(mind_map_data)
        notes.mind_map_svg = mind_map_svg
        
        notes.processing_status = 'completed'
        notes.save()
        
        messages.success(request, 'Notes generated successfully!')
        return redirect('view_generated_notes', notes_id=notes.id)
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error processing file: {str(e)}")
        print(f"Traceback: {error_details}")
        notes.processing_status = 'failed'
        notes.save()
        messages.error(request, f'Error processing file: {str(e)}')
        return redirect('auto_notes_generator')


@login_required(login_url='/signin/')
def view_generated_notes(request, notes_id):
    """View generated notes and mind map."""
    notes = get_object_or_404(GeneratedNotes, id=notes_id, user=request.user)
    return render(request, 'visionapp/examprep/view_notes.html', {'notes': notes})


@login_required(login_url='/signin/')
def delete_generated_notes(request, notes_id):
    """Delete generated notes."""
    notes = get_object_or_404(GeneratedNotes, id=notes_id, user=request.user)
    
    if request.method == 'POST':
        notes.delete()
        messages.success(request, 'Notes deleted.')
        return redirect('auto_notes_generator')
    
    return render(request, 'visionapp/examprep/confirm_delete_notes.html', {'notes': notes})

