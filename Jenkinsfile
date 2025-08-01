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
            steps { sh 'python3 -m unittest discover -s tests -p "test_*.py"' }
        }
        stage('Dependency Scan') {
            steps { 
                sh '''
                    if docker --version >/dev/null 2>&1; then
                        docker run --rm -v "$(pwd):/workspace" -w /workspace aquasec/trivy:latest fs --format table --output /workspace/trivy-report-table.txt .
                        docker run --rm -v "$(pwd):/workspace" -w /workspace aquasec/trivy:latest fs --format json --output /workspace/trivy-report.json .
                        docker run --rm -v "$(pwd):/workspace" -w /workspace aquasec/trivy:latest fs --format template --template "@contrib/html.tpl" --output /workspace/trivy-report.html .
                    elif trivy --version >/dev/null 2>&1; then
                        TEMP_DIR="/tmp/trivy-scan-$$"
                        mkdir -p "$TEMP_DIR"
                        cp -r . "$TEMP_DIR/"
                        cd "$TEMP_DIR"
                        trivy fs --format table --output trivy-report-table.txt .
                        trivy fs --format json --output trivy-report.json .
                        cp *.txt *.json "$WORKSPACE/" 2>/dev/null
                        cd "$WORKSPACE"
                        rm -rf "$TEMP_DIR"
                    else
                        if [ -f "requirements.txt" ]; then
                            echo "DEPENDENCY SCAN RESULTS\n========================\nScanning: requirements.txt\n\n📦 Found dependencies:" > trivy-report-table.txt
                            cat requirements.txt >> trivy-report-table.txt
                            echo "\n⚠️ Manual review required - Trivy unavailable" >> trivy-report-table.txt
                        else
                            echo "DEPENDENCY SCAN RESULTS\n========================\n❌ No requirements.txt found" > trivy-report-table.txt
                        fi
                    fi
                    if [ -f "trivy-report-table.txt" ]; then
                        cat trivy-report-table.txt
                        CRITICAL=$(grep -c "CRITICAL" trivy-report-table.txt 2>/dev/null || echo "0")
                        HIGH=$(grep -c "HIGH" trivy-report-table.txt 2>/dev/null || echo "0")
                        MEDIUM=$(grep -c "MEDIUM" trivy-report-table.txt 2>/dev/null || echo "0")
                        LOW=$(grep -c "LOW" trivy-report-table.txt 2>/dev/null || echo "0")
                        echo "\n🚨 VULNERABILITY SUMMARY:\n   CRITICAL: $CRITICAL\n   HIGH: $HIGH\n   MEDIUM: $MEDIUM\n   LOW: $LOW"
                    else
                        echo "❌ No scan results available"
                    fi
                '''
            }
        }
        stage('Deploy') {
            steps { 
                sh '''
                    docker stop loan-app 2>/dev/null || true
                    docker rm loan-app 2>/dev/null || true
                    if docker run -d -p 5000:5000 --name loan-app loan-calculator:latest; then
                        sleep 15
                        for i in {1..5}; do
                            if curl -f http://localhost:5000 >/dev/null 2>&1; then
                                echo "✅ Application is running at http://localhost:5000"
                                break
                            else
                                sleep 5
                                if [ $i -eq 5 ]; then
                                    echo "❌ Application health check failed after 5 attempts!"
                                    docker logs loan-app
                                    exit 1
                                fi
                            fi
                        done
                    else
                        exit 1
                    fi
                '''
            }
        }
        stage('DAST - Security Testing') {
            steps { 
                sh '''
                    curl -I http://localhost:5000 2>/dev/null > headers.txt
                    if curl -s -o /dev/null -w "%{http_code}" http://localhost:5000 | grep -q "200"; then
                        APP_STATUS="RUNNING"
                    else
                        APP_STATUS="ERROR"
                    fi
                    XFRAME=$(grep -q "X-Frame-Options" headers.txt && echo "PRESENT" || echo "MISSING")
                    XXSS=$(grep -q "X-XSS-Protection" headers.txt && echo "PRESENT" || echo "MISSING")
                    CSP=$(grep -q "Content-Security-Policy" headers.txt && echo "PRESENT" || echo "MISSING")
                    XSS_PAYLOAD="<script>alert('XSS')</script>"
                    XSS_RESPONSE=$(curl -s "http://localhost:5000/?test=$XSS_PAYLOAD" 2>/dev/null)
                    XSS_RISK=$(echo "$XSS_RESPONSE" | grep -q "<script>" && echo "HIGH" || echo "LOW")
                    for method in OPTIONS TRACE PUT DELETE; do
                        RESPONSE=$(curl -s -X $method -I http://localhost:5000 2>/dev/null | head -1)
                        if echo "$RESPONSE" | grep -q "200\\|405"; then
                            echo "$method: $(echo $RESPONSE | cut -d' ' -f2-)"
                        fi
                    done
                    ERROR_RESPONSE=$(curl -s "http://localhost:5000/nonexistent-page-test" 2>/dev/null)
                    ERROR_DISCLOSURE=$(echo "$ERROR_RESPONSE" | grep -qi "error\\|exception\\|stack\\|traceback" && echo "HIGH" || echo "LOW")
                    cat > zap-report.html << EOF
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Security Assessment Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #2c3e50; color: white; padding: 20px; }
        .section { margin: 20px 0; padding: 15px; border-left: 4px solid #3498db; }
        .risk-high { border-left-color: #e74c3c; background: #fdf2f2; }
        .risk-medium { border-left-color: #f39c12; background: #fef9e7; }
        .risk-low { border-left-color: #27ae60; background: #eafaf1; }
        .test-result { margin: 10px 0; padding: 10px; background: #f8f9fa; }
        pre { background: #2c3e50; color: white; padding: 10px; overflow-x: auto; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🛡️ Dynamic Application Security Testing (DAST) Report</h1>
        <p><strong>Target:</strong> http://localhost:5000</p>
        <p><strong>Scan Date:</strong> $(date)</p>
        <p><strong>Scan Method:</strong> Manual Security Assessment</p>
    </div>
    <div class="section">
        <h2>📊 Executive Summary</h2>
        <p><strong>Application Status:</strong> $APP_STATUS</p>
        <p><strong>Overall Risk Level:</strong> $([ "$XSS_RISK" = "HIGH" ] || [ "$ERROR_DISCLOSURE" = "HIGH" ] && echo "HIGH" || echo "MEDIUM")</p>
        <p><strong>Tests Performed:</strong> 5 security tests completed</p>
    </div>
    <div class="section $([ "$XSS_RISK" = "HIGH" ] && echo "risk-high" || echo "risk-low")">
        <h2>🔍 Test Results</h2>
        <div class="test-result">
            <h3>1. Application Connectivity Test</h3>
            <p><strong>Result:</strong> $APP_STATUS</p>
        </div>
        <div class="test-result">
            <h3>2. Security Headers Analysis</h3>
            <p><strong>X-Frame-Options:</strong> $XFRAME</p>
            <p><strong>X-XSS-Protection:</strong> $XXSS</p>
            <p><strong>Content-Security-Policy:</strong> $CSP</p>
        </div>
        <div class="test-result">
            <h3>3. Cross-Site Scripting (XSS) Test</h3>
            <p><strong>Risk Level:</strong> $XSS_RISK</p>
        </div>
        <div class="test-result">
            <h3>4. HTTP Methods Security</h3>
        </div>
        <div class="test-result">
            <h3>5. Error Information Disclosure</h3>
            <p><strong>Risk Level:</strong> $ERROR_DISCLOSURE</p>
        </div>
    </div>
    <div class="section">
        <h2>🔧 Recommendations</h2>
        <ul>
            <li>Install OWASP ZAP for comprehensive vulnerability scanning</li>
            <li>Implement missing security headers (CSP, X-Frame-Options, etc.)</li>
            <li>Ensure all user inputs are properly validated and sanitized</li>
            <li>Implement secure error handling that doesn't leak information</li>
            <li>Use HTTPS in production environment</li>
            <li>Implement rate limiting to prevent abuse</li>
        </ul>
    </div>
    <div class="section">
        <h2>📋 Raw HTTP Headers</h2>
        <pre>$(cat headers.txt)</pre>
    </div>
    <div class="section">
        <h2>🏷️ Report Information</h2>
        <p><strong>Generated By:</strong> Jenkins CI/CD Pipeline</p>
        <p><strong>Tool:</strong> Manual Security Assessment</p>
    </div>
</body>
</html>
EOF
                    cat > zap-report.md << EOF
# 🛡️ DAST Security Assessment Report

**Target:** http://localhost:5000  
**Date:** $(date)  
**Method:** Manual Security Testing

## 📊 Summary
- **Application Status:** $APP_STATUS
- **XSS Risk:** $XSS_RISK  
- **Error Disclosure Risk:** $ERROR_DISCLOSURE
- **Security Headers:** Missing $([ "$CSP" = "MISSING" ] && echo "CSP, "; [ "$XFRAME" = "MISSING" ] && echo "X-Frame-Options, "; [ "$XXSS" = "MISSING" ] && echo "X-XSS-Protection" | sed 's/, $//')

## 🔍 Detailed Results

### Security Headers Status:
- X-Frame-Options: $XFRAME
- X-XSS-Protection: $XXSS  
- Content-Security-Policy: $CSP

### Vulnerability Tests:
- XSS Protection: $XSS_RISK risk level
- Error Disclosure: $ERROR_DISCLOSURE risk level

## 🎯 Recommendations:
1. Install OWASP ZAP: \`sudo apt install zaproxy\`
2. Implement Content Security Policy
3. Add missing security headers
4. Validate all user inputs
5. Use HTTPS in production
6. Implement proper error handling
EOF
                    echo "📊 SECURITY ASSESSMENT COMPLETED!\n=================================\n✅ HTML Report: zap-report.html\n✅ Markdown Report: zap-report.md\n\n🔍 Key Findings:\n   - XSS Risk Level: $XSS_RISK\n   - Error Disclosure Risk: $ERROR_DISCLOSURE\n   - Security Headers: $([ "$CSP" = "MISSING" ] && [ "$XFRAME" = "MISSING" ] && echo "Multiple missing" || echo "Some present")\n\n📁 Reports saved and ready for download!"
                '''
            }
        }
        stage('Report Summary') {
            steps {
                sh '''
                    echo "📊 SECURITY SCAN SUMMARY\n=========================\n\n📁 Generated Reports:"
                    ls -la *.html *.txt *.json *.md 2>/dev/null || echo "No reports found"
                    echo "\n🔗 Report Access Methods:\n   1. ✅ Console output\n   2. 📁 Jenkins build artifacts\n   3. 🌐 Application running at: http://localhost:5000"
                    [ -f "trivy-report-table.txt" ] && echo "   4. ✅ Dependency scan report available" || echo "   4. ⚠️ Dependency scan report missing"
                    [ -f "zap-report.html" ] || [ -f "zap-report.md" ] && echo "   5. ✅ Security scan report available" || echo "   5. ⚠️ Security scan report missing"
                '''
            }
        }
    }
    post {
        always {
            archiveArtifacts artifacts: '*.html, *.txt, *.json, *.md', allowEmptyArchive: true, fingerprint: true
            sh 'rm -rf /tmp/trivy-scan-* 2>/dev/null || true'
        }
        success {
            echo '🎉 PIPELINE COMPLETED SUCCESSFULLY!\n\n📋 WHAT TO DO NEXT:\n================\n1️⃣ Review console output\n2️⃣ Check build artifacts\n3️⃣ Visit application: http://localhost:5000\n4️⃣ Review security findings'
        }
        failure {
            echo '❌ PIPELINE FAILED!\n\n🔍 TROUBLESHOOTING STEPS:\n========================\n1️⃣ Check console output\n2️⃣ Verify tool installations\n3️⃣ Check port availability\n4️⃣ Ensure GitHub repository access'
        }
    }
}