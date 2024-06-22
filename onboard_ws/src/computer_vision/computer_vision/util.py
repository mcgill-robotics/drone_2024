import string
import easyocr
import cv2
import numpy as np

# Initialize the OCR reader
reader = easyocr.Reader(['en'], gpu=True)  #change to true when on jetson


def read_letter_and_color_on_shape(letter_crop):
    """
    Read the letter text from the given cropped image.

    Args:
        letter_crop (PIL.Image.Image): Cropped image containing the letter.

    Returns:
        tuple: Tuple containing the formatted text and its confidence score.
    """
    # process object
    grayImage_letter = cv2.cvtColor(letter_crop, cv2.COLOR_BGR2GRAY)
    thresh_im_letter = cv2.adaptiveThreshold(grayImage_letter, 255,
                                             cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                             cv2.THRESH_BINARY, 11, 2)
    hsv_img = cv2.cvtColor(letter_crop, cv2.COLOR_BGR2HSV)

    colors = {}

    detections = reader.readtext(thresh_im_letter)
    if (len(detections) == 0):
        return None, None, None, None
    bbox, text, score = detections[0]

    # red boundaries
    red_lower1 = np.array([0, 100, 20])
    red_upper1 = np.array([10, 255, 255])
    red_lower2 = np.array([160, 100, 20])
    red_upper2 = np.array([179, 255, 255])
    red_lower_mask = cv2.inRange(hsv_img, red_lower1, red_upper1)
    red_upper_mask = cv2.inRange(hsv_img, red_lower2, red_upper2)
    red_mask = red_lower_mask + red_upper_mask

    # green boundaries
    green_lower = np.array([36, 50, 70], np.uint8)
    green_upper = np.array([89, 255, 255], np.uint8)
    green_mask = cv2.inRange(hsv_img, green_lower, green_upper)

    # blue boundaries
    blue_lower = np.array([90, 50, 70], np.uint8)
    blue_upper = np.array([128, 255, 255], np.uint8)
    blue_mask = cv2.inRange(hsv_img, blue_lower, blue_upper)

    # white boundaries
    white_lower = np.array([0, 0, 231], np.uint8)
    white_upper = np.array([180, 18, 255], np.uint8)
    white_mask = cv2.inRange(hsv_img, white_lower, white_upper)

    # black boundaries
    black_lower = np.array([0, 0, 0], np.uint8)
    black_upper = np.array([180, 255, 30], np.uint8)
    black_mask = cv2.inRange(hsv_img, black_lower, black_upper)

    # purple boundaries
    purple_lower = np.array([129, 50, 70], np.uint8)
    purple_upper = np.array([158, 255, 255], np.uint8)
    purple_mask = cv2.inRange(hsv_img, purple_lower, purple_upper)

    # brown boundaries
    brown_lower = np.array([10, 100, 20], np.uint8)
    brown_upper = np.array([20, 255, 200], np.uint8)
    brown_mask = cv2.inRange(hsv_img, brown_lower, brown_upper)

    # orange boundaries
    orange_lower = np.array([10, 50, 70], np.uint8)
    orange_upper = np.array([24, 255, 255], np.uint8)
    orange_mask = cv2.inRange(hsv_img, orange_lower, orange_upper)

    # For red color
    res_red = cv2.bitwise_and(hsv_img, hsv_img, mask=red_mask)
    # For green color
    res_green = cv2.bitwise_and(hsv_img, hsv_img, mask=green_mask)
    # For blue color
    res_blue = cv2.bitwise_and(hsv_img, hsv_img, mask=blue_mask)
    # For white color
    res_white = cv2.bitwise_and(hsv_img, hsv_img, mask=white_mask)
    # For black color
    res_black = cv2.bitwise_and(hsv_img, hsv_img, mask=black_mask)
    # For purple color
    res_purple = cv2.bitwise_and(hsv_img, hsv_img, mask=purple_mask)
    # For brown color
    res_brown = cv2.bitwise_and(hsv_img, hsv_img, mask=brown_mask)
    # For orange color
    res_orange = cv2.bitwise_and(hsv_img, hsv_img, mask=orange_mask)

    # creating contour to track red color
    contours, hierarchy = cv2.findContours(red_mask, cv2.RETR_TREE,
                                           cv2.CHAIN_APPROX_SIMPLE)
    for pic, contour in enumerate(contours):
        area = cv2.contourArea(contour)
        colors[area] = ['red']

    # Creating contour to track green color
    contours, hierarchy = cv2.findContours(green_mask, cv2.RETR_TREE,
                                           cv2.CHAIN_APPROX_SIMPLE)
    for pic, contour in enumerate(contours):
        area = cv2.contourArea(contour)
        colors[area] = ['green']

    # Creating contour to track blue color
    contours, hierarchy = cv2.findContours(blue_mask, cv2.RETR_TREE,
                                           cv2.CHAIN_APPROX_SIMPLE)
    for pic, contour in enumerate(contours):
        area = cv2.contourArea(contour)
        colors[area] = ['blue']

    # creating contour to track white color
    contours, hierarchy = cv2.findContours(white_mask, cv2.RETR_TREE,
                                           cv2.CHAIN_APPROX_SIMPLE)
    for pic, contour in enumerate(contours):
        area = cv2.contourArea(contour)
        colors[area] = ['white']

    # Creating contour to track black color
    contours, hierarchy = cv2.findContours(black_mask, cv2.RETR_TREE,
                                           cv2.CHAIN_APPROX_SIMPLE)
    for pic, contour in enumerate(contours):
        area = cv2.contourArea(contour)
        colors[area] = ['black']

    # Creating contour to track purple color
    contours, hierarchy = cv2.findContours(purple_mask, cv2.RETR_TREE,
                                           cv2.CHAIN_APPROX_SIMPLE)
    for pic, contour in enumerate(contours):
        area = cv2.contourArea(contour)
        colors[area] = ['purple']

    # creating contour to track brown color
    contours, hierarchy = cv2.findContours(brown_mask, cv2.RETR_TREE,
                                           cv2.CHAIN_APPROX_SIMPLE)
    for pic, contour in enumerate(contours):
        area = cv2.contourArea(contour)
        colors[area] = ['brown']

    # Creating contour to track orange color
    contours, hierarchy = cv2.findContours(orange_mask, cv2.RETR_TREE,
                                           cv2.CHAIN_APPROX_SIMPLE)
    for pic, contour in enumerate(contours):
        area = cv2.contourArea(contour)
        if (area > 10):  #this is just me trying to see if it exists
            colors[area] = ['orange']

    shape_color = None
    letter_color = None
    current_upper_area = 0
    current_lower_area = 0
    for area, color in colors:
        if shape_color == None and letter_color == None:
            shape_color = color
            letter_color = color
            current_upper_area = area
            current_lower_area = area
        elif area > current_upper_area:
            shape_color = color
            current_upper_area = area
        elif area < current_lower_area:
            letter_color = color
            current_lower_area = area

    return text, score, shape_color, letter_color
