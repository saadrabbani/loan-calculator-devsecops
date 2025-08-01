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
                    
                    # Generate detailed Trivy report in multiple formats
                    trivy fs --format table --output trivy-report-table.txt .
                    trivy fs --format json --output trivy-report.json .
                    trivy fs --format template --template "@contrib/html.tpl" --output trivy-report.html . || true
                    
                    echo "📄 Trivy scan completed!"
                    echo "==================== TRIVY RESULTS ===================="
                    cat trivy-report-table.txt
                    echo "======================================================="
                    
                    # Count vulnerabilities
                    CRITICAL=$(grep -c "CRITICAL" trivy-report-table.txt || echo "0")
                    HIGH=$(grep -c "HIGH" trivy-report-table.txt || echo "0")
                    MEDIUM=$(grep -c "MEDIUM" trivy-report-table.txt || echo "0")
                    LOW=$(grep -c "LOW" trivy-report-table.txt || echo "0")
                    
                    echo "🚨 VULNERABILITY SUMMARY:"
                    echo "   CRITICAL: $CRITICAL"
                    echo "   HIGH: $HIGH" 
                    echo "   MEDIUM: $MEDIUM"
                    echo "   LOW: $LOW"
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
                    echo "⏳ Waiting for application to start..."
                    sleep 15
                    
                    # Health check
                    if curl -f http://localhost:5000 >/dev/null 2>&1; then
                        echo "✅ Application is running at http://localhost:5000"
                    else
                        echo "❌ Application health check failed!"
                        docker logs loan-app
                        exit 1
                    fi
                '''
            }
        }
        stage('DAST') {
            steps { 
                sh '''
                    echo "🛡️ Running OWASP ZAP Dynamic Security Scan..."
                    
                    # Run ZAP baseline scan
                    zap-baseline.py -t http://localhost:5000 -r zap-report.html -w zap-report.md || true
                    
                    echo "📄 DAST scan completed!"
                    
                    # Show ZAP results summary if available
                    if [ -f "zap-report.md" ]; then
                        echo "==================== ZAP RESULTS ===================="
                        head -50 zap-report.md
                        echo "======================================================="
                    fi
                '''
            }
        }
        stage('Report Summary') {
            steps {
                sh '''
                    echo "📊 SECURITY SCAN SUMMARY"
                    echo "========================="
                    
                    echo "📁 Generated Reports:"
                    ls -la *.html *.txt *.json *.md 2>/dev/null || echo "No reports found"
                    
                    echo ""
                    echo "🔗 To view reports:"
                    echo "   1. Check Jenkins build artifacts (below)"
                    echo "   2. Or access via Jenkins workspace"
                    echo "   3. Or check the console output above"
                '''
            }
        }
    }
    post {
        always {
            // Archive ALL report files as Jenkins artifacts
            archiveArtifacts artifacts: '*.html, *.txt, *.json, *.md', allowEmptyArchive: true, fingerprint: true
            
            // Publish HTML reports (if you have HTML Publisher plugin)
            publishHTML([
                allowMissing: false,
                alwaysLinkToLastBuild: true,
                keepAll: true,
                reportDir: '.',
                reportFiles: 'trivy-report.html, zap-report.html',
                reportName: 'Security Reports',
                reportTitles: 'Trivy and ZAP Security Reports'
            ])
        }
        success {
            echo '''
            🎉 Pipeline completed successfully!
            
            📋 NEXT STEPS:
            1. Scroll up to see Trivy vulnerability summary
            2. Scroll up to see ZAP security findings  
            3. Click "Security Reports" link (left sidebar)
            4. Download artifacts below to view full HTML reports
            5. Your app is running at: http://localhost:5000
            '''
        }
        failure {
            echo "❌ Pipeline failed! Check the logs above for details."
        }
    }
}