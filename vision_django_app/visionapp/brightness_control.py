"""Small wrapper to set screen brightness when `screen_brightness_control` is available.

If the package is not installed, the module silently becomes a no-op while
logging an informative message so the rest of the app doesn't crash.
"""
try:
    import screen_brightness_control as sbc
except Exception:
    sbc = None


def set_auto_brightness(left_d, right_d, user_specific=False):
    """Change system brightness based on estimated diopter, personalized per user.

    Args:
        left_d (float): left eye diopter
        right_d (float): right eye diopter
        user_specific (bool): If True, uses more personalized calculation based on user's specific eye power
    """
    if sbc is None:
        # Do not crash if sbc is unavailable; print an informational message only.
        print("[AUTO-BRIGHTNESS SKIPPED] `screen_brightness_control` not installed.")
        return

    try:
        # Only set brightness if we have actual user profile data (not default/zero values)
        # This ensures brightness is ONLY set based on user's actual eye power, not defaults
        if left_d == 0 and right_d == 0:
            print("[AUTO-BRIGHTNESS SKIPPED] No user profile data available (default values detected).")
            return
        
        # Use the worse eye (more negative diopter = worse vision = needs more brightness)
        # This ensures the brightness is set for the user's specific needs
        worse_eye_d = min(left_d, right_d)
        
        if user_specific:
            # Personalized brightness calculation based on user's specific eye power
            # More negative diopter = worse vision = higher brightness needed
            # Formula: brightness = 70 + (abs(diopter) * 8) with limits
            # This gives a smooth, personalized curve instead of fixed ranges
            base_brightness = 20
            brightness_adjustment = abs(worse_eye_d) * 5
            brightness = min(100, max(20, base_brightness + brightness_adjustment))
            
            # Round to nearest 5 for cleaner values
            brightness = round(brightness / 5) * 5
        else:
            # Fallback to range-based calculation for backward compatibility
            if worse_eye_d <= -3:
                brightness = 90
            elif worse_eye_d <= -2:
                brightness = 80
            elif worse_eye_d <= -1.5:
                brightness = 75
            elif worse_eye_d <= -1:
                brightness = 60
            elif worse_eye_d <= -0.5:
                brightness = 50
            else:
                # Don't set default brightness - only set if user has actual profile data
                print("[AUTO-BRIGHTNESS SKIPPED] Eye power values too close to normal (no adjustment needed).")
                return

        sbc.set_brightness(int(brightness))
        print(f"[AUTO-BRIGHTNESS] Brightness set to {int(brightness)}% (based on user eye power: L={left_d}, R={right_d})")
    except Exception as e:
        print(f"[AUTO-BRIGHTNESS ERROR] {e}")
