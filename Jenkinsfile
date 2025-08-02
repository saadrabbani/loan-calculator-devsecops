pipeline {
    agent any
    stages {
        stage('Clone') {
            steps { 
                git 'https://github.com/saadrabbani/loan-calculator-devsecops.git' 
            }
        }
        stage('Build') {
            steps { 
                sh 'docker build -t loan-calculator:latest .' 
            }
        }
        stage('Test') {
            steps { 
                sh 'python3 -m unittest discover -s tests -p "test_*.py"'
            }
        }
        stage('SonarQube Analysis') {
            steps {
                sh '''
                    source ~/.bashrc
                    sonar-scanner \
                        -Dsonar.projectKey=Loan-Calculator-Application \
                        -Dsonar.sources=. \
                        -Dsonar.host.url=http://192.168.80.109:9000 \
                        -Dsonar.login=sqp_9776029d91d2a8bc0d0b617af9acd182f6dbeae3
                '''
            }
        }
        stage('Deploy') {
            steps { 
                sh '''
                    # Stop any running containers using port 5000
                    docker stop $(docker ps -q --filter "publish=5000") 2>/dev/null || true
                    
                    # Remove stopped containers to free up the name and resources
                    docker container prune -f
                    
                    # Start new container
                    docker run -d -p 5000:5000 --name loan-app loan-calculator:latest
                    
                    echo "✅ Application deployed successfully!"
                    echo "🌐 Access your app at: http://localhost:5000"
                '''
            }
        }
    }
}