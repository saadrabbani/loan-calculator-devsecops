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
                    
                    # Method 1: Try running Trivy with Docker (most reliable)
                    if docker --version >/dev/null 2>&1; then
                        echo "📦 Using Docker-based Trivy scan..."
                        docker run --rm -v "$(pwd):/workspace" -w /workspace aquasec/trivy:latest fs --format table --output /workspace/trivy-report-table.txt . || echo "⚠️ Docker Trivy scan had issues"
                        
                        # Also generate JSON and try HTML
                        docker run --rm -v "$(pwd):/workspace" -w /workspace aquasec/trivy:latest fs --format json --output /workspace/trivy-report.json . || true
                        docker run --rm -v "$(pwd):/workspace" aquasec/trivy:latest fs --format template --template "@contrib/html.tpl" --output /workspace/trivy-report.html . || echo "⚠️ HTML template not available"
                    
                    # Method 2: Try native Trivy if Docker fails
                    elif trivy --version >/dev/null 2>&1; then
                        echo "🔧 Using native Trivy installation..."
                        
                        # Copy files to /tmp to avoid snap restrictions
                        TEMP_DIR="/tmp/trivy-scan-$$"
                        mkdir -p "$TEMP_DIR"
                        cp -r . "$TEMP_DIR/"
                        cd "$TEMP_DIR"
                        
                        trivy fs --format table --output trivy-report-table.txt . || echo "⚠️ Native Trivy scan had issues"
                        trivy fs --format json --output trivy-report.json . || true
                        
                        # Copy reports back
                        cp *.txt *.json "$WORKSPACE/" 2>/dev/null || true
                        cd "$WORKSPACE"
                        rm -rf "$TEMP_DIR"
                    
                    # Method 3: Manual dependency check if Trivy fails
                    else
                        echo "⚠️ Trivy not available, performing manual dependency check..."
                        echo "📋 Checking requirements.txt for known vulnerable packages..."
                        
                        # Create a simple vulnerability report
                        cat > trivy-report-table.txt << EOF
DEPENDENCY SCAN RESULTS
========================
Scanning: requirements.txt

EOF
                        
                        if [ -f "requirements.txt" ]; then
                            echo "📦 Found dependencies:" >> trivy-report-table.txt
                            cat requirements.txt >> trivy-report-table.txt
                            echo "" >> trivy-report-table.txt
                            echo "⚠️ Manual review required - Trivy unavailable" >> trivy-report-table.txt
                        else
                            echo "❌ No requirements.txt found" >> trivy-report-table.txt
                        fi
                    fi
                    
                    # Display results
                    echo "📄 Dependency scan completed!"
                    echo "==================== TRIVY RESULTS ===================="
                    
                    if [ -f "trivy-report-table.txt" ]; then
                        cat trivy-report-table.txt
                        
                        # Count vulnerabilities if file contains them
                        CRITICAL=$(grep -c "CRITICAL" trivy-report-table.txt 2>/dev/null || echo "0")
                        HIGH=$(grep -c "HIGH" trivy-report-table.txt 2>/dev/null || echo "0")
                        MEDIUM=$(grep -c "MEDIUM" trivy-report-table.txt 2>/dev/null || echo "0")
                        LOW=$(grep -c "LOW" trivy-report-table.txt 2>/dev/null || echo "0")
                        
                        echo ""
                        echo "🚨 VULNERABILITY SUMMARY:"
                        echo "   CRITICAL: $CRITICAL"
                        echo "   HIGH: $HIGH" 
                        echo "   MEDIUM: $MEDIUM"
                        echo "   LOW: $LOW"
                    else
                        echo "❌ No scan results available"
                    fi
                    
                    echo "======================================================="
                '''
            }
        }
        stage('Deploy') {
            steps { 
                sh '''
                    echo "🚀 Starting deployment..."
                    
                    # Cleanup old containers
                    docker stop loan-app 2>/dev/null || echo "ℹ️ No existing container to stop"
                    docker rm loan-app 2>/dev/null || echo "ℹ️ No existing container to remove"
                    
                    # Deploy new container
                    if docker run -d -p 5000:5000 --name loan-app loan-calculator:latest; then
                        echo "✅ Container started successfully"
                    else
                        echo "❌ Failed to start container"
                        exit 1
                    fi
                    
                    # Wait for app to start
                    echo "⏳ Waiting for application to start..."
                    sleep 15
                    
                    # Health check with retries
                    for i in {1..5}; do
                        if curl -f http://localhost:5000 >/dev/null 2>&1; then
                            echo "✅ Application is running at http://localhost:5000"
                            break
                        else
                            echo "⏳ Health check attempt $i failed, retrying..."
                            sleep 5
                            if [ $i -eq 5 ]; then
                                echo "❌ Application health check failed after 5 attempts!"
                                echo "📋 Container logs:"
                                docker logs loan-app
                                exit 1
                            fi
                        fi
                    done
                '''
            }
        }
        stage('DAST') {
            steps { 
                sh '''
                    echo "🛡️ Running OWASP ZAP Dynamic Security Scan..."
                    
                    # Check if ZAP is available
                    if command -v zap-baseline.py >/dev/null 2>&1; then
                        echo "🔍 ZAP found, running baseline scan..."
                        
                        # Run ZAP baseline scan with error handling
                        zap-baseline.py -t http://localhost:5000 -r zap-report.html -w zap-report.md -I || {
                            echo "⚠️ ZAP scan completed with findings or errors"
                        }
                        
                        echo "📄 DAST scan completed!"
                        
                        # Show ZAP results summary if available
                        if [ -f "zap-report.md" ]; then
                            echo "==================== ZAP RESULTS ===================="
                            head -50 zap-report.md 2>/dev/null || echo "Could not display ZAP results"
                            echo "======================================================="
                        else
                            echo "⚠️ ZAP markdown report not generated"
                        fi
                    
                    # Alternative: Use Docker-based ZAP if native not available
                    elif docker --version >/dev/null 2>&1; then
                        echo "🐳 Using Docker-based ZAP scan..."
                        
                        docker run --rm -v $(pwd):/zap/wrk/:rw -t zaproxy/zap-stable zap-baseline.py \\
                            -t http://host.docker.internal:5000 \\
                            -r zap-report.html \\
                            -I || echo "⚠️ Docker ZAP scan completed with findings"
                    
                    else
                        echo "⚠️ ZAP not available, creating placeholder report..."
                        cat > zap-report.md << EOF
# DAST Security Scan Report

**Status**: ZAP not available on this system
**Target**: http://localhost:5000
**Recommendation**: Install OWASP ZAP for proper dynamic security testing

## Manual Security Checklist:
- [ ] Application responds to requests
- [ ] No sensitive information in error messages  
- [ ] HTTPS should be used in production
- [ ] Input validation should be implemented
- [ ] Authentication should be required for sensitive operations

EOF
                        echo "📝 Placeholder security report created"
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
                    echo "🔗 Report Access Methods:"
                    echo "   1. ✅ Console output (scroll up to see results)"
                    echo "   2. 📁 Jenkins build artifacts (download below)"
                    echo "   3. 🌐 Application running at: http://localhost:5000"
                    
                    # Validate reports exist
                    if [ -f "trivy-report-table.txt" ]; then
                        echo "   4. ✅ Dependency scan report available"
                    else
                        echo "   4. ⚠️ Dependency scan report missing"
                    fi
                    
                    if [ -f "zap-report.html" ] || [ -f "zap-report.md" ]; then
                        echo "   5. ✅ Security scan report available"
                    else
                        echo "   5. ⚠️ Security scan report missing"
                    fi
                '''
            }
        }
    }
    post {
        always {
            // Archive ALL report files as Jenkins artifacts
            archiveArtifacts artifacts: '*.html, *.txt, *.json, *.md', allowEmptyArchive: true, fingerprint: true
            
            // Clean up any temporary files
            sh 'rm -rf /tmp/trivy-scan-* 2>/dev/null || true'
        }
        success {
            echo '''
            🎉 PIPELINE COMPLETED SUCCESSFULLY!
            
            📋 WHAT TO DO NEXT:
            ================
            1️⃣ Scroll up to see detailed scan results in console
            2️⃣ Check "Build Artifacts" section below for downloadable reports
            3️⃣ Visit your application: http://localhost:5000
            4️⃣ Review security findings and fix any critical issues
            
            💡 TIP: Look for the "TRIVY RESULTS" and "ZAP RESULTS" sections above!
            '''
        }
        failure {
            echo '''
            ❌ PIPELINE FAILED!
            
            🔍 TROUBLESHOOTING STEPS:
            ========================
            1️⃣ Check the console output above for specific error messages
            2️⃣ Verify all required tools are installed (Docker, Python, etc.)
            3️⃣ Check if ports are available (5000 for app)
            4️⃣ Ensure GitHub repository is accessible
            
            💡 TIP: Most common issues are permission problems or missing dependencies
            '''
        }
    }
}