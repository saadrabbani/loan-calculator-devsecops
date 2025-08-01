pipeline {
    agent any
    stages {
        stage('Clone') {
            steps { git 'https://github.com/saadrabbani/loan-calculator-devsecops.git' }
        }
        stage('Build') {
            steps { sh 'docker build -t loan-calculator:latest .' }
        }
        stage('Test') {
            steps { sh 'python3 -m unittest tests/test_app.py' }
        }
        stage('Deploy') {
            steps { sh 'docker run -d -p 8080:5000 loan-calculator:latest' }
        }
    }
}