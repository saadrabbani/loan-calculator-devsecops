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
            steps { 
                sh 'python3 -m unittest discover -s tests -p "test_*.py"'
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