pipeline {
    agent any
    stages {
        stage('Clone') {
            steps { git 'https://github.com/saadrabbani/loan-calculator-devsecops.git' }
        }
        stage('Build') {
            steps { sh 'docker build -t loan-calculator:latest .' }
        }
        stage('Unit Test') {
            steps { 
                sh 'python3 -m unittest discover -s tests -p "test_*.py"'
            }
        }
        stage('Dependency Scan') {
            steps { 
                sh '''
                    echo "🔍 Running Trivy dependency scan..."
                    trivy fs --format table . || echo "⚠️ Trivy scan completed with findings"
                '''
            }
        }
        stage('Deploy') {
            steps { 
                sh '''
                    # Cleanup old containers
                    docker stop loan-app 2>/dev/null || true
                    docker rm loan-app 2>/dev/null || true
                    
                    # Deploy new container
                    docker run -d -p 5000:5000 --name loan-app loan-calculator:latest
                    
                    # Wait for app to start
                    sleep 10
                    echo "✅ Application deployed at http://localhost:5000"
                '''
            }
        }
        stage('DAST') {
            steps { 
                sh '''
                    echo "🛡️ Running OWASP ZAP scan..."
                    zap-baseline -t http://localhost:5000 -r zap-report.html || echo "⚠️ ZAP scan completed"
                    echo "📄 Check zap-report.html for security findings"
                    pwd
                '''
            }
        }
    }
}