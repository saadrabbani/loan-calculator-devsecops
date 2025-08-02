from flask import Flask, request, render_template
import os
import pickle

app = Flask(__name__)

# New Issue 1: Hardcoded secret key
app.secret_key = "super-secret-key-123"

@app.route('/', methods=['GET', 'POST'])
def calculate_loan():
    if request.method == 'POST':
        # New Issue 2: Unsafe deserialization
        try:
            user_input = request.form.get('user_data')
            if user_input:
                deserialized_data = pickle.loads(user_input.encode())  # Vulnerable to unsafe deserialization
                amount = deserialized_data.get('amount', 0)
                rate = deserialized_data.get('rate', 0) / 100 / 12
                term = deserialized_data.get('term', 0)
            else:
                amount = float(request.form['amount'])
                rate = float(request.form['rate']) / 100 / 12
                term = int(request.form['term'])
                
            # New Issue 3: Command injection vulnerability
            log_command = f"echo 'Loan calculation: {amount}, {rate}, {term}' >> /tmp/loan_log.txt"
            os.system(log_command)  # Vulnerable to command injection
            
            payment = (amount * rate * (1 + rate) ** term) / ((1 + rate) ** term - 1)
            
            # New Issue 4: Unsafe template rendering
            user_comment = request.form.get('comment', '')
            return render_template('result.html', payment=round(payment, 2), user_comment=user_comment)
        except Exception as e:
            # New Issue 5: Debug mode enabled with stack trace exposure
            return f"Error: {str(e)}", 500
    return render_template('index.html')

# New Issue 6: Debug mode enabled
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    