from flask import *
import sqlite3
import secrets
import time
import os
from PIL import Image
import cv2
import cv2
from pyzbar.pyzbar import decode

connection = sqlite3.connect('user_data.db')
cursor = connection.cursor()

command = """CREATE TABLE IF NOT EXISTS user(name TEXT, password TEXT, mobile TEXT, email TEXT)"""
cursor.execute(command)

command = """CREATE TABLE IF NOT EXISTS wallet(phone TEXT, amount TEXT)"""
cursor.execute(command)

command = """CREATE TABLE IF NOT EXISTS book(name TEXT, email TEXT, fromloc TEXT, toloc TEXT, Date TEXT, passengers TEXT, names TEXT, routenum TEXT, amount TEXT, status TEXT)"""
cursor.execute(command)

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/home')
def home():
    return render_template('userlog.html')

@app.route('/Scanner')
def Scanner():
    vs = cv2.VideoCapture(0)
    while True:
        ret, img = vs.read()
        detectedBarcodes = decode(img)
        d=''
        t=''
        for barcode in detectedBarcodes:
            (x, y, w, h) = barcode.rect
            cv2.rectangle(img, (x-10, y-10),
                        (x + w+10, y + h+10),
                        (255, 0, 0), 2)
            d = barcode.data
            t = barcode.type
        if d != "":
            d = d.decode('utf-8', 'ignore')
            cv2.putText(img, str(d), (50, 50) , cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0) , 2)
        cv2.imshow("Image", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        if d != "":
            break
    vs.release()
    cv2.destroyAllWindows()
    print(d)
    connection = sqlite3.connect('user_data.db')
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM book WHERE name = '"+d+"' and status = 'pending'")
    result = cursor.fetchall()
    print(result)
    if result:
        result = list(result[-1])
        row = result[:6]
        row.append(result[6].split("\r\n"))
        row.extend(result[7:])
        print(row)
        cursor.execute("update book set status = 'completed' where name = '"+d+"'")
        connection.commit()
        return render_template('adminlog.html', row = row)
    else:
        return render_template('adminlog.html', row = False, msg="Invalide QR code")

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':

        connection = sqlite3.connect('user_data.db')
        cursor = connection.cursor()

        email = request.form['email']
        password = request.form['password']

        query = "SELECT * FROM user WHERE email = '"+email+"' AND password= '"+password+"'"
        cursor.execute(query)
        result = cursor.fetchone()

        if result:
            session['phone'] = result[2]
            return render_template('userlog.html')
        else:
            return render_template('signin.html', msg='Sorry, Incorrect Credentials Provided,  Try Again')

    return render_template('signin.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':

        connection = sqlite3.connect('user_data.db')
        cursor = connection.cursor()

        name = request.form['name']
        password = request.form['password']
        mobile = request.form['phone']
        email = request.form['email']
        
        print(name, mobile, email, password)

        cursor.execute("INSERT INTO user VALUES ('"+name+"', '"+password+"', '"+mobile+"', '"+email+"')")
        connection.commit()

        return render_template('signin.html', msg='Successfully Registered')
    
    return render_template('signup.html')

@app.route('/booking', methods=['GET', 'POST'])
def booking():
    if request.method == 'POST':

        connection = sqlite3.connect('user_data.db')
        cursor = connection.cursor()

        name = request.form['name']
        email = request.form['email']
        From = request.form['from']
        To = request.form['to']
        Date = request.form['Date']
        nop = request.form['nop']

        i = 1
        passengers = ''
        while True:
            try:
                names = request.form[f'passenger_name_{i}']
                passengers += names+'\n'
                i += 1
            except:
                break
        passengers = passengers[:-1]
        values = [name, email, From, To, Date, nop, passengers]

        
        if values[2] == 'RWF' and values[3] == 'Avalahalli':
            amt = 15 * int(values[5])
            routenum = '285, 285M, 285MC, 285MK'

        if values[2] == 'NES' and values[3] == 'Avalahlli':
            amt = 20 * int(values[5])
            routenum = '285, 285M, 285MC, 285MK'

        if values[2] == 'NES' and values[3] == 'Rajanukunte':
            amt = 20 * int(values[5])
            routenum = '285, 285M, 285MC, 285MK'

        if values[2] == 'RWF' and values[3] == 'Rajanukunte':
            amt = 15 * int(values[5])
            routenum = '285, 285M, 285MC, 285MK'
        
        connection = sqlite3.connect('user_data.db')
        cursor = connection.cursor()

        cursor.execute("select * from wallet where phone = '"+session['phone']+"'")
        result = cursor.fetchone()

        if result:
            Balance = int(result[1])
            if Balance < amt:
                print('insufficient balance')
                return render_template('userlog.html', msg='insufficient balance')
            else:
                av_balance = Balance - amt
                cursor.execute("update wallet set amount = '"+str(av_balance)+"' where phone = '"+session['phone']+"'")
                connection.commit()

                values.append(routenum)
                values.append(amt)
                values.append('pending')
                
                cursor.execute("INSERT INTO book VALUES (?,?,?,?,?,?,?,?,?,?)", values)
                connection.commit()

                import qrcode
                qr = qrcode.QRCode(
                    version =1,
                    box_size =10,
                    border=6)

                qr.add_data(values[0])
                qr.make(fit=True)
                image = qr.make_image(fill_color="black", back_color= "white")
                image.save('static/'+values[0]+'.png')
                print("QR code has been generated successfully!")

                cursor.execute("SELECT * FROM book WHERE name = '"+values[0]+"' and status = 'pending'")
                result = cursor.fetchall()
                result = list(result[-1])
                row = result[:6]
                row.append(result[6].split("\n"))
                row.extend(result[7:])
                print(row)
                return render_template('userlog.html', row = row, QR='http://127.0.0.1:5000/static/'+values[0]+'.png')
        else:
            print('insufficient balance')
            return render_template('userlog.html', msg='insufficient balance')
    return render_template('userlog.html')

@app.route('/recharge', methods=['GET', 'POST'])
def recharge():
    connection = sqlite3.connect('user_data.db')
    cursor = connection.cursor()
    phone = session['phone']

    print(phone)

    if request.method == 'POST':
        amount = int(request.form['amount'])

        cursor.execute("select * from wallet where phone = '"+phone+"'")
        result = cursor.fetchone()
        if result:
            print(result[1])
            amount += int(result[1])
            cursor.execute("update wallet set amount = '"+str(amount)+"'")
            connection.commit()
        else:
            cursor.execute("INSERT INTO wallet VALUES ('"+phone+"', '"+str(amount)+"')")
            connection.commit()

        cursor.execute("select * from wallet where phone = '"+phone+"'")
        result=cursor.fetchone()

        if result:
            balance = result[1]
        else:
            balance = 0

        return render_template('wallet.html',balance=balance)
    
    cursor.execute("select * from wallet where phone = '"+phone+"'")
    result=cursor.fetchone()
    print(result)
    if result:
        balance = result[1]
    else:
        balance = 0 
    return render_template('wallet.html',balance=balance)


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        print(email, password)

        if email == 'admin@gmail.com' and password == 'admin@123':
            return render_template('adminlog.html')
        else:
            return render_template('admin.html', msg='Sorry, Incorrect Credentials Provided,  Try Again')

    return render_template('admin.html')

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
