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
    dog_width = int(face_width*1.5)+10
    dog_height = int(face_height*1.75)+10
    dog = cv2.resize(dog,(dog_width, dog_height))
    for i in range(int(face_height*1.75)):
        for j in range(int(face_width*1.5)):
            for k in range(3):
                if dog[i][j][k]<235:
                    fc[y+i-int(0.375*h)-1][x+j-int(0.25*w)][k] = dog[i][j][k]
    return fc


def display_images():
    images = [
        'captures/image0.jpg',
        'captures/image1.jpg',
        'captures/image2.jpg'
    ]
   
    for image in images:
        img = cv2.imread(image)
        cv2.namedWindow('Photo', cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty('Photo', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        cv2.imshow('Photo', img)
        cv2.waitKey(0)

    cv2.destroyWindow('Photo')
    os.system('wmctrl -a "pi@rp9: ~/Desktop/photobooth"')


def send_mail(recipients):
    gmail_user = ''
    gmail_passwd = ''

    with open('info/user', 'r') as user_file:
        gmail_user = user_file.read().replace('\n', '')
    with open('info/passwd', 'r') as passwd_file:
        gmail_passwd = passwd_file.read().replace('\n', '')

    img0_data = open('captures/image0.jpg', 'rb').read()
    img1_data = open('captures/image1.jpg', 'rb').read()
    img2_data = open('captures/image2.jpg', 'rb').read()

    img0 = MIMEImage(img0_data, name=os.path.basename('captures/image0.jpg'))
    img1 = MIMEImage(img1_data, name=os.path.basename('captures/image1.jpg'))
    img2 = MIMEImage(img2_data, name=os.path.basename('captures/image2.jpg'))
    text = MIMEText('Here are your photos! Thank you for '
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

        try:
            s = smtplib.SMTP('smtp.gmail.com', 587)
            s.ehlo()
            s.starttls()
            s.login(gmail_user, gmail_passwd)
            s.sendmail(gmail_user, recipient, msg.as_string())
            s.quit()
            print 'Email sent to {}!'.format(recipient)
        except:
            print 'Failed to send email to {}.'.format(recipient)


def send_sms(recipients):
    gmail_user = ''
    gmail_passwd = ''
    sms_gateways = [
        'tmomail.net',      # Tmobile
        'mms.att.net',      # AT&T
        'vtext.com',        # Verizon
        'page.nextel.com',  # Sprint
    ]

    with open('info/user', 'r') as f:
        gmail_user = f.read().replace('\n', '')
    with open('info/passwd', 'r') as f:
        gmail_passwd = f.read().replace('\n', '')

    link0, link1, link2 = get_imgur_links()

    text = MIMEText('Here are your photos! Thank you for stopping by the SnapBerry'
                    'Pi booth!\n{}\n{}\n{}'.format(link0, link1, link2), 'plain')

    for recipient in recipients:
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
                print 'Message sent to {}!'.format(destination)
            except:
                print 'Failed to send message to {}.'.format(destination)
        print ''


def get_imgur_links():
    with open('info/cid', 'r') as f:
        CLIENT_ID = f.read().replace('\n', '')
    img0_path = "captures/image0.jpg"
    img1_path = "captures/image1.jpg"
    img2_path = "captures/image2.jpg"
    im = pyimgur.Imgur(CLIENT_ID)
    
    img0 = im.upload_image(img0_path, title="Mustache")
    img1 = im.upload_image(img1_path, title="Cowboy Hat")
    img2 = im.upload_image(img2_path, title="Dog Filter")

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
            camera.annotate_text = '3'
            sleep(1)

            for i in range(3):
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
                        image = apply_moustache(mst, image, x-35, y-60, w, h)
                    elif i == 1:
                        camera.annotate_text = 'Applying cowboy hat filter...'
                        image = apply_hat(hat, image, x-45, y-70, w, h)
                    elif i == 2:
                        camera.annotate_text = 'Applying dog filter...'
                        image = apply_dog(dog, image, x-25, y+25, w, h)

                # Reset stream and save image.
                camera.annotate_text = 'Finishing...'
                cv2.imwrite('captures/image%s.jpg' % i, image)

            camera.stop_preview()
            del arrays[:]

        display_images()
        clear()
        selection = ''
        print "Select one of the following:"
        print "Press (1) to recieve photos through text."
        print "Press (2) to recieve photos through email."
        selection =  raw_input("Selection: ")
        clear()

        if selection == '1':
            print 'Enter the phone numbers you want the photos to be sent to.'
            print 'Enter "1" to stop entering phone numbers.'
            phone = ''

            while phone != '1':
                phone = raw_input('Phone number: ')
                phone = phone.replace(' ', '')
                if phone != '1':
                    phones.append(phone)

            send_sms(phones)
            del phones[:]

        elif selection == '2':
            print 'Enter the email addresses you want the photos to be sent to.'
            print 'Enter "1" to stop entering emails.'
            email = ''

            while email != '1':
                email = raw_input('Email address: ')
                email = email.replace(' ', '')
                if email != '1':
                    emails.append(email)

            send_mail(emails)
            del emails[:]

        sleep(3)

if __name__ == '__main__':
    main()
