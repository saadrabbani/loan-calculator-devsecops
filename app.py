from flask import Flask, request, render_template

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def calculate_loan():
    if request.method == 'POST':
        amount = float(request.form['amount'])
        rate = float(request.form['rate']) / 100 / 12
        term = int(request.form['term'])
        payment = (amount * rate * (1 + rate) ** term) / ((1 + rate) ** term - 1)
        return render_template('result.html', payment=round(payment, 2))
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)