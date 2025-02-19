from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# In-memory storage
app_state = {
    'users': [
        # Sample user for testing
        {'name': 'Test User', 'email': 'test@test.com', 'password': 'test123'}
    ],
    'jobs': [
        # Sample job for testing
        {'title': 'Software Developer', 'company': 'Tech Corp', 'location': 'New York', 'description': 'Looking for a full-stack developer', 'postedBy': 'test@test.com', 'date': '2/19/2025'}
    ],
    'current_user': None
}

@app.route('/')
def home():
    if app_state['current_user']:
        return redirect(url_for('main_page'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user and user.password == password:
            return redirect(url_for('dashboard'))  # Or wherever you want to redirect after login
        else:
            return "Invalid login credentials", 400

    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        if any(user['email'] == email for user in app_state['users']):
            flash('Email already exists!')
            return redirect(url_for('signup'))
        app_state['users'].append({'name': name, 'email': email, 'password': password})
        flash('Account created successfully!')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/main', methods=['GET', 'POST'])
def main_page():
    if not app_state['current_user']:
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form['title']
        company = request.form['company']
        location = request.form['location']
        description = request.form['description']
        app_state['jobs'].append({
            'title': title, 'company': company, 'location': location, 'description': description,
            'postedBy': app_state['current_user']['email'], 'date': '2/19/2025'
        })
        flash('Job posted successfully!')
    return render_template('main.html', jobs=app_state['jobs'])

@app.route('/logout')
def logout():
    app_state['current_user'] = None
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

@app.route('/post_job')
def post_job_page():
    if 'user' not in session:
        return redirect(url_for('index'))
    return render_template('post_job.html')

@app.route('/post_job', methods=['POST'])
def post_job():
    if 'user' not in session:
        return redirect(url_for('index'))

    title = request.form['title']
    company = request.form['company']
    location = request.form['location']
    description = request.form['description']

    # Add the new job post to the list (or save to a database in a real app)
    jobs.append({
        'title': title,
        'company': company,
        'location': location,
        'description': description,
        'postedBy': session['user'],
        'date': '2/19/2025'  # You can replace this with dynamic date
    })

    return redirect(url_for('main_page'))
