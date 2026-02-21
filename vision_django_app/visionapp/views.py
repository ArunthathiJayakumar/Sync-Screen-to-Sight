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
from visionapp.models import UserVisionData
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
    if eye_screen_distance.face_detection is None:
        # Create a single static frame that indicates mediapipe is not installed.
        h, w = 480, 640
        static_img = np.zeros((h, w, 3), dtype=np.uint8)
        cv2.putText(static_img, 'Mediapipe not installed', (10, 220), cv2.FONT_HERSHEY_SIMPLEX,
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
        results = eye_screen_distance.face_detection.process(image_rgb)

        bbox_list, eyes_list = [], []
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

