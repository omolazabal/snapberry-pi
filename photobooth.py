#!/usr/bin/env python2.7

import os
import io
import picamera
import cv2
import numpy as np
import smtplib
import pyimgur
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from time import sleep


IMG0_PATH = 'captures/image0.jpg'
IMG1_PATH = 'captures/image1.jpg'
IMG2_PATH = 'captures/image2.jpg'
GMAIL_USR_PATH = 'info/user'
GMAIL_PWD_PATH = 'info/passwd'
IMGUR_CID_PATH = 'info/cid'

term_win_title = 'pi@rp9: ~/Desktop/photobooth'

mst = cv2.imread('filters/mst.png')
dog = cv2.imread('filters/dog.png')
hat = cv2.imread('filters/hat.png')

mst = cv2.GaussianBlur(mst,(5,5),0)
dog = cv2.GaussianBlur(dog,(5,5),0)
hat = cv2.GaussianBlur(hat,(5,5),0)



def clear():
    os.system('clear')


def apply_moustache(mst,fc,x,y,w,h):
    face_width = w
    face_height = h
    mst_width = int(face_width*0.8166666)-20
    mst_height = int(face_height*0.842857)-20
    mst = cv2.resize(mst,(mst_width,mst_height))
    for i in range(int(0.62857142857*face_height),int(0.62857142857*face_height)+mst_height):
        for j in range(int(0.29166666666*face_width),int(0.29166666666*face_width)+mst_width):
            for k in range(3):
                if mst[i-int(0.62857142857*face_height)][j-int(0.29166666666*face_width)][k] <235:
                    fc[y+i][x+j][k] = mst[i-int(0.62857142857*face_height)][j-int(0.29166666666*face_width)][k]
    return fc


def apply_hat(hat,fc,x,y,w,h):
    face_width = w
    face_height = h
    hat_width = face_width+100
    hat_height = int(0.35*face_height)+100
    hat = cv2.resize(hat,(hat_width,hat_height))
    for i in range(hat_height):
        for j in range(hat_width):
            for k in range(3):
                if hat[i][j][k]<235:
                    fc[y+i-int(0.25*face_height)][x+j][k] = hat[i][j][k]
    return fc


def apply_dog(dog,fc,x,y,w,h):
    face_width = w
    face_height = h
    dog_width = int(face_width*1.5)+30
    dog_height = int(face_height*1.75)+100
    dog = cv2.resize(dog,(dog_width, dog_height))
    for i in range(int(face_height*1.75)):
        for j in range(int(face_width*1.5)):
            for k in range(3):
                if dog[i][j][k]<235:
                    fc[y+i-int(0.375*h)-1][x+j-int(0.25*w)][k] = dog[i][j][k]
    return fc


def display_images():
    images = [
        IMG0_PATH,
        IMG1_PATH,
        IMG2_PATH
    ]
   
    for image in images:
        img = cv2.imread(image)
        cv2.namedWindow('Photo', cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty('Photo', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        cv2.imshow('Photo', img)
        cv2.waitKey(0)

    cv2.destroyWindow('Photo')
    os.system('wmctrl -a "{}"'.format(term_win_title))


def send_mail(recipients):
    gmail_user = ''
    gmail_passwd = ''

    with open(GMAIL_USR_PATH, 'r') as user_file:
        gmail_user = user_file.read().replace('\n', '')
    with open(GMAIL_PWD_PATH, 'r') as passwd_file:
        gmail_passwd = passwd_file.read().replace('\n', '')

    img0_data = open(IMG0_PATH, 'rb').read()
    img1_data = open(IMG1_PATH, 'rb').read()
    img2_data = open(IMG2_PATH, 'rb').read()

    img0 = MIMEImage(img0_data, name=os.path.basename(IMG0_PATH))
    img1 = MIMEImage(img1_data, name=os.path.basename(IMG1_PATH))
    img2 = MIMEImage(img2_data, name=os.path.basename(IMG2_PATH))
    text = MIMEText('Here are your photos. Thank you for '
                    'stopping by the Snapberry Pi booth!')

    for recipient in recipients:
        msg = MIMEMultipart()
        msg['Subject'] = 'Snapberry Pi Photos'
        msg['From'] = gmail_user
        msg['To'] = recipient
        msg.attach(text)
        msg.attach(img0)
        msg.attach(img1)
        msg.attach(img2)

        print 'Sending email to {}...'.format(recipient)

        try:
            s = smtplib.SMTP('smtp.gmail.com', 587)
            s.ehlo()
            s.starttls()
            s.login(gmail_user, gmail_passwd)
            s.sendmail(gmail_user, recipient, msg.as_string())
            s.quit()
        except:
            print 'Failed to send email to {}.'.format(recipient)


def send_sms(recipients):
    gmail_user = ''
    gmail_passwd = ''
    sms_gateways = [
        'mms.att.net',      # AT&T
        'vtext.com',        # Verizon
    ]

    with open(GMAIL_USR_PATH, 'r') as f:
        gmail_user = f.read().replace('\n', '')
    with open(GMAIL_PWD_PATH, 'r') as f:
        gmail_passwd = f.read().replace('\n', '')

    link0, link1, link2 = get_imgur_links()

    text = MIMEText('Thank you for stopping by the Snapberry Pi booth!'
                    '\n{}\n{}\n{}'.format(link0, link1, link2), 'plain')

    for recipient in recipients:
        print 'Sending message to {}...'.format(recipient)
        for gateway in sms_gateways:
            destination = recipient + '@' + gateway
            msg = MIMEMultipart()
            msg.attach(text)

            try:
                s = smtplib.SMTP('smtp.gmail.com', 587)
                s.ehlo()
                s.starttls()
                s.login(gmail_user, gmail_passwd)
                s.sendmail(gmail_user, destination, msg.as_string())
                s.quit()
            except:
                print 'Failed to send message to {}'.format(destination)
        print ''


def get_imgur_links():
    with open('info/cid', 'r') as f:
        CLIENT_ID = f.read().replace('\n', '')
    im = pyimgur.Imgur(CLIENT_ID)
    
    img0 = im.upload_image(IMG0_PATH, title='Mustache')
    img1 = im.upload_image(IMG1_PATH, title='Cowboy Hat')
    img2 = im.upload_image(IMG2_PATH, title='Dog Filter')

    return img0.link, img1.link, img2.link


def main():
    face_cascade = cv2.CascadeClassifier('haarcascade_frontalface.xml')  # Cascade file.
    stream = io.BytesIO()  # Memory stream for photos.

    emails = []
    phones = []
    arrays = []

    while True:
        clear()
        selection = raw_input('Press [ENTER] to start.')
        with picamera.PiCamera() as camera:
            camera.vflip = True
            camera.start_preview()
            camera.annotate_text = '5'
            sleep(1)
            camera.annotate_text = '4'
            sleep(1)

            for i in range(3):
                camera.annotate_text = '3'
                sleep(1)
                camera.annotate_text = '2'
                sleep(1)
                camera.annotate_text = '1'
                sleep(1)
                camera.annotate_text = ''
                camera.capture(stream, format='jpeg')
                arrays.append(np.fromstring(stream.getvalue(), dtype=np.uint8)) # Convert the picture into a np array
                stream.seek(0)
                stream.truncate()

            for i in range(3):
                camera.annotate_text = 'Preprocessing...'
                image = cv2.imdecode(arrays[i], 1)                       # Create an OpenCV image
                gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)            # Convert to grayscale
                camera.annotate_text = 'Detecting faces..'
                faces = face_cascade.detectMultiScale(gray, 1.1, 5)      # Look for faces using cascade file

                #Apply filter
                for (x,y,w,h) in faces:
                    if i == 0:
                        camera.annotate_text = 'Applying moustache filter...'
                        image = apply_moustache(mst, image, x-40, y-60, w, h)
                    elif i == 1:
                        camera.annotate_text = 'Applying cowboy hat filter...'
                        image = apply_hat(hat, image, x-45, y-70, w, h)
                    elif i == 2:
                        camera.annotate_text = 'Applying dog filter...'
                        image = apply_dog(dog, image, x-40, y-20, w, h)

                # Reset stream and save image.
                camera.annotate_text = 'Finishing...'
                cv2.imwrite('captures/image%s.jpg' % i, image)

            camera.stop_preview()

        display_images()
        del arrays[:]
        clear()

        print 'Share your photos!'
        print 'Press (1) to add a phone number (TMobile and Verizon only).'
        print 'Press (2) to add an email.'
        print 'Press (3) to share.\n'

        selection = ''

        while selection != '3':
            selection = raw_input("Selection: ")

            if selection == '1':
                phone = raw_input('Phone number: ')
                phone = phone.replace(' ', '')
                phones.append(phone)
            elif selection == '2':
                email = raw_input('Email address: ')
                email = email.replace(' ', '')
                emails.append(email)
            elif selection != '3':
                print 'Invalid selection.'

            print ''

        clear()

        if len(emails) != 0:
            print 'Creating email...'
            send_mail(emails)
            del emails[:]
        if len(phones) != 0:
            print 'Creating message...'
            send_sms(phones)
            del phones[:]
        
        print 'Thank you for stopping by!'
        sleep(3)

if __name__ == '__main__':
    main()
