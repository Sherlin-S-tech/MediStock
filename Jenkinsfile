pipeline {
  agent any
  options { timestamps(); disableConcurrentBuilds() }
  parameters {
    booleanParam(name: 'DEPLOY_ENABLED', defaultValue: false, description: 'Deploy the tested image to the configured Ansible target')
  }
  environment {
    APP_IMAGE = "${env.APP_IMAGE ?: 'medicine-stock'}"
    APP_TAG = "${env.APP_TAG ?: (env.GIT_COMMIT ? env.GIT_COMMIT.take(12) : env.BUILD_NUMBER)}"
    SECRET_KEY = credentials('medicine-stock-secret-key')
    NEAR_EXPIRY_DAYS = '30'
  }
  stages {
    stage('Checkout') { steps { checkout scm; script { env.APP_TAG = env.GIT_COMMIT.take(12) } } }
    stage('Setup Dependencies') { steps { sh 'python3 -m venv .venv && .venv/bin/pip install -r requirements.txt' } }
    stage('Syntax Validation') {
      steps {
        sh '''
          .venv/bin/python -m py_compile app.py database.py services.py scripts/seed_demo_data.py
          .venv/bin/python -c "import yaml; [yaml.safe_load(open(p, encoding='utf-8')) for p in ['ansible/deploy.yml','ansible/manage_container.yml']]"
        '''
      }
    }
    stage('Automated Tests') { steps { sh '.venv/bin/pytest -q --junitxml=test-results.xml' } }
    stage('Publish Test Results') { steps { junit allowEmptyResults: true, testResults: 'test-results.xml' } }
    stage('Build Docker Image') { steps { sh 'docker build --tag "$APP_IMAGE:$APP_TAG" .' } }
    stage('Deploy with Ansible') {
      when { expression { return params.DEPLOY_ENABLED } }
      steps {
        withEnv(["MEDICINE_STOCK_SECRET_KEY=${SECRET_KEY}"]) {
          sh 'ansible-playbook -i ansible/inventory.ini ansible/deploy.yml --extra-vars "app_image=$APP_IMAGE:$APP_TAG app_tag=$APP_TAG"'
        }
      }
    }
    stage('Verify Deployment') {
      when { expression { return params.DEPLOY_ENABLED } }
      steps {
        sh 'ansible -i ansible/inventory.ini medicine_hosts -m ansible.builtin.uri -a "url=http://127.0.0.1:5000/health status_code=200"'
      }
    }
  }
  post {
    always { junit allowEmptyResults: true, testResults: 'test-results.xml' }
    success { echo "Pipeline succeeded for ${APP_IMAGE}:${APP_TAG}" }
    failure { echo 'Pipeline failed. Review the first failed stage and console log; deployment is gated on tests.' }
  }
}
