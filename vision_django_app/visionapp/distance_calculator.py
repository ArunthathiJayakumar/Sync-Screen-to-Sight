import cv2
import numpy as np
import subprocess
import sys
import os

try:
    import pandas as pd
    _pandas_installed = True
except Exception:
    pd = None
    _pandas_installed = False

# Auto-install and import mediapipe
_mediapipe_installed = False
mp = None
_use_old_api = False

def install_mediapipe():
    """Report that mediapipe is not available"""
    global _mediapipe_installed, mp
    print('[DISTANCE] Mediapipe is not available. Please install using: pip install mediapipe==0.10.32')
    return False

try:
    import mediapipe as mp
    _mediapipe_installed = True
    print('[DISTANCE] Mediapipe imported successfully')
    # Check which API version is available
    try:
        from mediapipe.solutions import face_detection
        _use_old_api = True
        print('[DISTANCE] Using old mediapipe API (solutions)')
    except ImportError:
        try:
            from mediapipe.tasks.vision import FaceDetector
            _use_old_api = False
            print('[DISTANCE] Using new mediapipe API (tasks)')
        except ImportError:
            print('[DISTANCE] Could not find either old or new mediapipe API')
            _mediapipe_installed = False
except Exception as e:
    print(f'[DISTANCE] Mediapipe import failed: {e}')
    install_mediapipe()
    print('[DISTANCE] Warning: Could not install mediapipe')
    mp = None
    _mediapipe_installed = False


class DistanceCalculator:
    """calculate the distance (cm) between user's eyes and laptop screen using webcam 
    """

    # colors to use (in BGR)
    colors = [(76, 168, 240), (255, 0, 255), (255, 255, 0)]
    # instantiation face detection solution (lazy instance attribute in __init__)

    @staticmethod
    def draw_bbox(img, bbox, color, l=30, t=5, rt=1):
        """draw bounding box around user(s) face

        Args:
            img (numpy ndarray): video frame
            bbox (tuple): bounding box data (x,y,width, height)
            color (tuple): color in BGR
            l (int, optional): corners lines length. Defaults to 30.
            t (int, optional): corners lines thickness. Defaults to 5.
            rt (int, optional): bounding box thickness. Defaults to 1.
        """
        # draw bbox
        x, y, w, h = bbox
        x1, y1 = x + w, y + h

        cv2.rectangle(img, bbox, color, rt)
        # top left
        cv2.line(img, (x, y), (x + l, y), color, t)
        cv2.line(img, (x, y), (x, y + l), color, t)
        # top right
        cv2.line(img, (x1, y), (x1 - l, y), color, t)
        cv2.line(img, (x1, y), (x1, y + l), color, t)
        # bottom left
        cv2.line(img, (x, y1), (x + l, y1), color, t)
        cv2.line(img, (x, y1), (x, y1 - l), color, t)
        # bottom right
        cv2.line(img, (x1, y1), (x1 - l, y1), color, t)
        cv2.line(img, (x1, y1), (x1, y1 - l), color, t)

    @staticmethod
    def draw_dist_between_eyes(img, center_left, center_right, color, distance_value):
        """draw a line between user's eyes and annotate the distance (pixel) between them

        Args:
            img (numpy ndarray): video frame
            center_left (tuple): left eye landmark (x,y)
            center_right (tuple): right eye landmark (x,y)
            color (tuple): color in BGR
            distance_value ([type]): distance between eyes (pixel)
        """
        # mark eyes
        cv2.circle(img, center_left, 1, color, thickness=8)
        cv2.circle(img, center_right, 1, color, thickness=8)

        # line between eyes
        cv2.line(img, center_left, center_right, color, 3)

        # add distance value
        cv2.putText(img, f'{int(distance_value)}',
                    (center_left[0], center_left[1] -
                     10), cv2.FONT_HERSHEY_PLAIN,
                    2, color, 2)

    def __init__(self):
        # Check for mediapipe availability dynamically (not just at import time)
        mediapipe_available = False
        self.use_old_api = False
        self.use_haar_cascade = False
        self.face_detector = None  # For new API
        self.face_detection = None  # For old API
        self.haar_face_cascade = None  # For Haar Cascade fallback
        
        try:
            # Try new API (mediapipe 0.10.30+)
            from mediapipe.tasks.python.vision import FaceDetector
            from mediapipe.tasks.python.vision.face_detector import FaceDetectorOptions
            from mediapipe.tasks.python.core.base_options import BaseOptions
            
            # Look for the model file in common locations
            import os
            model_path = None
            possible_paths = [
                'face_detection_short_range.tflite',
                os.path.join(os.getcwd(), 'face_detection_short_range.tflite'),
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    model_path = path
                    break
            
            # If model not found, try to download it
            if not model_path or not os.path.exists(model_path):
                print('[DISTANCE] Face detection model not found locally, attempting to download...')
                try:
                    import urllib.request
                    download_url = 'https://storage.googleapis.com/mediapipe-assets/face_detection_short_range.tflite'
                    model_path = 'face_detection_short_range.tflite'
                    urllib.request.urlretrieve(download_url, model_path)
                    print(f'[DISTANCE] Model downloaded to {model_path}')
                except Exception as download_err:
                    print(f'[DISTANCE] Failed to download model: {download_err}')
                    model_path = None
            
            if model_path and os.path.exists(model_path):
                try:
                    # Create BaseOptions with the model path
                    base_options = BaseOptions(model_asset_path=model_path)
                    # Create FaceDetectorOptions
                    options = FaceDetectorOptions(
                        base_options=base_options,
                        min_detection_confidence=0.5
                    )
                    # Create the detector
                    self.face_detector = FaceDetector.create_from_options(options)
                    self.use_old_api = False
                    mediapipe_available = True
                    print('[DISTANCE] FaceDetector (new API) created successfully')
                except Exception as e:
                    print(f'[DISTANCE] Failed to create new API FaceDetector with options: {e}')
                    # Fallback to Haar Cascade
                    print('[DISTANCE] Falling back to Haar Cascade for face detection')
                    self._init_haar_cascade()
                    if self.haar_face_cascade is not None:
                        self.use_haar_cascade = True
                        mediapipe_available = True
            else:
                print('[DISTANCE] Could not locate or download face detection model')
                # Fallback to Haar Cascade
                print('[DISTANCE] Falling back to Haar Cascade for face detection')
                self._init_haar_cascade()
                if self.haar_face_cascade is not None:
                    self.use_haar_cascade = True
                    mediapipe_available = True
                    
        except ImportError as e:
            print(f'[DISTANCE] New API not available: {e}. Trying old API...')
            # Try old API
            try:
                import mediapipe as mp_check
                _ = mp_check.solutions.face_detection
                self.face_detection = mp_check.solutions.face_detection.FaceDetection(
                    model_selection=0, min_detection_confidence=0.75
                )
                self.use_old_api = True
                mediapipe_available = True
                print('[DISTANCE] FaceDetection (old API) created successfully')
            except Exception as e:
                print(f'[DISTANCE] Failed to create old API FaceDetection: {e}')
                # Fallback to Haar Cascade
                print('[DISTANCE] Falling back to Haar Cascade for face detection')
                self._init_haar_cascade()
                if self.haar_face_cascade is not None:
                    self.use_haar_cascade = True
                    mediapipe_available = True
        except Exception as e:
            print(f'[DISTANCE] Unexpected error during initialization: {e}')
            # Fallback to Haar Cascade
            print('[DISTANCE] Falling back to Haar Cascade for face detection')
            self._init_haar_cascade()
            if self.haar_face_cascade is not None:
                self.use_haar_cascade = True
                mediapipe_available = True
        
        if not mediapipe_available:
            print('[DISTANCE] Mediapipe not available and Haar Cascade initialization failed, face detection set to None')
            self.face_detection = None
            self.face_detector = None
            self.haar_face_cascade = None
    
    def _init_haar_cascade(self):
        """Initialize OpenCV's Haar Cascade classifier as fallback"""
        try:
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.haar_face_cascade = cv2.CascadeClassifier(cascade_path)
            if self.haar_face_cascade.empty():
                print('[DISTANCE] Failed to load Haar Cascade')
                self.haar_face_cascade = None
            else:
                print('[DISTANCE] Haar Cascade loaded successfully')
        except Exception as e:
            print(f'[DISTANCE] Error loading Haar Cascade: {e}')
            self.haar_face_cascade = None

    def run_config(self):
        """it is used to for the initial configuration of the system where the user needs to measure few distances in cm corresponding to different distances in pixel  
        """

        # webcam input:
        cap = cv2.VideoCapture(0)
        while cap.isOpened():
            success, image = cap.read()
            if not success:
                print("Ignoring empty camera frame.")
                continue

            if self.face_detection is None:
                print('[DISTANCE] Mediapipe not installed; `run_config` is disabled.')
                break
            image.flags.writeable = False
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = self.face_detection.process(image)
            bbox_list, eyes_list = [], []
            if results.detections:
                for detection in results.detections:
                    # get bbox data
                    bboxc = detection.location_data.relative_bounding_box
                    ih, iw, ic = image.shape
                    bbox = int(bboxc.xmin*iw), int(bboxc.ymin *
                                                   ih), int(bboxc.width*iw), int(bboxc.height*ih)
                    bbox_list.append(bbox)

                    # get the eyes landmark
                    left_eye = detection.location_data.relative_keypoints[0]
                    right_eye = detection.location_data.relative_keypoints[1]
                    eyes_list.append([(int(left_eye.x*iw), int(left_eye.y*ih)),
                                      (int(right_eye.x*iw), int(right_eye.y*ih))])

            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            for bbox, eye in zip(bbox_list, eyes_list):

                dist_between_eyes = np.sqrt(
                    (eye[0][1]-eye[1][1])**2 + (eye[0][0]-eye[1][0])**2)

                # draw bbox
                DistanceCalculator.draw_bbox(image, bbox, self.colors[0])

                # draw distace between eyes
                DistanceCalculator.draw_dist_between_eyes(
                    image, eye[0], eye[1], self.colors[0], dist_between_eyes)

            cv2.imshow('webcam', image)
            if cv2.waitKey(5) & 0xFF == ord('k'):
                break
        cap.release()

    def calculate_distance(self, distance_pixel, distance_cm):
        """calculate distance in cm between user's eyes and laptop screen

        Args:
            distance_pixel (list): distance between eyes in pixel
            distance_cm (list): distance to screen in cm
        """

        coff = np.polyfit(distance_pixel, distance_cm, 2)

        cap = cv2.VideoCapture(0)
        while cap.isOpened():
            success, image = cap.read()
            if not success:
                print("Ignoring empty camera frame.")
                continue

            if self.face_detection is None:
                print('[DISTANCE] Mediapipe not installed; `calculate_distance` is disabled.')
                break
            image.flags.writeable = False
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = self.face_detection.process(image)
            bbox_list, eyes_list = [], []
            if results.detections:
                for detection in results.detections:
                    bboxc = detection.location_data.relative_bounding_box
                    ih, iw, ic = image.shape
                    bbox = int(bboxc.xmin*iw), int(bboxc.ymin *
                                                   ih), int(bboxc.width*iw), int(bboxc.height*ih)
                    bbox_list.append(bbox)

                    left_eye = detection.location_data.relative_keypoints[0]
                    right_eye = detection.location_data.relative_keypoints[1]
                    eyes_list.append([(int(left_eye.x*iw), int(left_eye.y*ih)),
                                      (int(right_eye.x*iw), int(right_eye.y*ih))])

            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            for bbox, eye in zip(bbox_list, eyes_list):

                dist_between_eyes = np.sqrt(
                    (eye[0][1]-eye[1][1])**2 + (eye[0][0]-eye[1][0])**2)

                # calculate distance in cm
                a, b, c = coff
                distance_cm = a*dist_between_eyes**2+b*dist_between_eyes+c

                if distance_cm > 51: 
                    # draw bbox
                    DistanceCalculator.draw_bbox(image, bbox, self.colors[2])
                    # add distance in cm
                    cv2.putText(image, f'{int(distance_cm)} cm - safe',
                                (bbox[0], bbox[1] - 10), cv2.FONT_HERSHEY_PLAIN,
                                2, self.colors[2], 2)

                else:
                    # draw bbox
                    DistanceCalculator.draw_bbox(image, bbox, self.colors[1])
                    cv2.putText(image, f'{int(distance_cm)} cm - too close',
                                (bbox[0], bbox[1] - 10), cv2.FONT_HERSHEY_PLAIN,
                                2, self.colors[1], 2)

            cv2.imshow('webcam', image)
            if cv2.waitKey(5) & 0xFF == ord('k'):
                break
        cap.release()


if __name__ == '__main__':
    try:
        if pd is not None:
            df = pd.read_csv('distance_xy.csv')
            dp = df['distance_pixel']
            dc = df['distance_cm']
        else:
            arr = np.loadtxt('distance_xy.csv', delimiter=',', skiprows=1)
            dp = arr[:, 0]
            dc = arr[:, 1]
    except Exception:
        dp = np.array([178, 150, 137, 111, 94, 81, 65, 54])
        dc = np.array([19, 22, 27, 34, 42, 49, 61, 72])

    eye_screen_distance = DistanceCalculator()
    eye_screen_distance.calculate_distance(dp, dc)
